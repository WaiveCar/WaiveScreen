import logging
import os
import time
import cv2
import numpy as np

OUT_DIR='/home/adorno/camera_recordings'
try:
  os.mkdir(OUT_DIR)
except:
  pass

log_format = '%(asctime)s %(levelname)s:%(message)s'
logging.basicConfig(filename='{}/camera.log'.format(OUT_DIR), format=log_format, level=logging.DEBUG)
#logging.basicConfig(format=log_format, level=logging.DEBUG)

W = 640
H = 360
RECORDING_SECONDS = 60 * 15

class Camera():
  MAX_VALUE_PERCENTAGE = 0.15
  HIST_BINS = 32
  AE_PREROLL = 8
  ME_PREROLL = 2
  DEFAULT_SATURATION = 60
  DEFAULT_BRIGHTNESS = -12
  CALIBRATION_INTERVAL = 40  # Frames
  BLANK_FRAME = np.zeros([H, W, 3], np.uint8)

  def __init__(self, cam_num):
    device = '/dev/video{}'.format(cam_num)
    self.cap = cv2.VideoCapture(device, apiPreference=cv2.CAP_V4L2)
    self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, W*2)
    self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, H*2)
    self.cam_num = cam_num
    self.saturation = self.DEFAULT_SATURATION
    self.auto_exposure = True
    self.brightness = self.DEFAULT_BRIGHTNESS
    self._gframe = None
    self._cframe = None
    self.hist = None
    self.last_hist = None
    self.calibrating_brightness = False
    self.ae_req_count = 0
    self.frame_num = 0
    self.cframe_current = False
    self.gframe_current = False
    self.disabled = False
    self.camera_info_overlay = True

  def calibrate(self):
    self.ae_req_count = 0
    self.sample_frame(pre_roll_override=30)
    self.save_frame('first')
    for i in range(4):
      self.sample_frame()
      self.save_frame('mid')
      switching = self.check_calibration()
      if switching:
        h_max = self.hist.max()
        self.sample_frame()
        if h_max < self.hist.max():
          self.auto_exposure = not self.auto_exposure
        break
    while self.calibrating_brightness:
      self.sample_frame()
      self.save_frame('b_cal')
      self.calibrate_brightness(force_run=True)
    self.save_frame('end')

  def record(self, for_secs=None):
    t = time.strftime('%Y%m%d-%H%M%S')
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    self.out = cv2.VideoWriter('{}/video{}-{}.mp4'.format(OUT_DIR, self.cam_num, t), fourcc, 10.0, (1280,720))
    self.frame_num = 0
    if for_secs:
      end_frame_num = for_secs * 30
    try:
      while self.cap.isOpened() and self.frame_num <= end_frame_num:
        ret = self.grab()
        if ret:
          self.out.write(self.cframe)
        if self.calibrating_brightness:
          self.calibrate_brightness()
        elif self.frame_num % self.CALIBRATION_INTERVAL == 0:
          self.check_calibration()
    except Exception as ex:
      logging.error('Stopped with: {}'.format(ex))
    except:  # Keyboard
      pass
    self.out.release()
  
  def check_calibration(self):
    switching = False
    self.calc_hist()
    if self.hist.max() / self.gframe.size > self.MAX_VALUE_PERCENTAGE:  # Over Exposed
      if self.hist.argmax() < self.hist.size / 3:
        logging.debug('CAM{}-Frame hist.max() too low: {} @ {}'.format(self.cam_num, self.hist.max() / self.gframe.size, self.hist.argmax()))
        switching = self.request_exposure('auto')
      elif self.hist.argmax() > (self.hist.size / 3) * 2:
        logging.debug('CAM{}-Frame hist.max() too high: {} @ {}'.format(self.cam_num, self.hist.max() / self.gframe.size, self.hist.argmax()))
        switching = self.request_exposure('manual')
      if switching:
        logging.debug('CAM{}-Changing Exposure'.format(self.cam_num))
        self.brightness = self.DEFAULT_BRIGHTNESS
      self.cal_int = 10
    else:
      self.cal_int = 5
    self.bdiff = 0
    self.calibrating_brightness = True
    self.next_cal_frame_num = self.pre_roll + self.frame_num
    return switching

  def calibrate_brightness(self, force_run=False):
    if self.next_cal_frame_num == self.frame_num or force_run:
      self.calc_hist()
      logging.debug('CAM{}-Hist Offset: {}'.format(self.cam_num, self.hist_offset))
      if self.hist_offset < -1:
        if self.bdiff < 0:
          self.cal_int = self.cal_int / 2
          self.calibrating_brightness = False
        self.brightness = self.brightness + self.cal_int
      elif self.hist_offset > 1:
        if self.bdiff > 0:
          self.cal_int = self.cal_int / 2
          self.calibrating_brightness = False
        self.brightness = self.brightness - self.cal_int
      else:
        self.calibrating_brightness = False
        return
      self.next_cal_frame_num = self.pre_roll + self.frame_num

  def request_exposure(self, exp):
    if exp == 'auto':
      if self.auto_exposure:
        self.ae_req_count -= 1
        return False
      elif self.ae_req_count < 2 :
        self.ae_req_count += 1
        return False
      else:
        self.auto_exposure = True
        return True
    if exp == 'manual':
      if not self.auto_exposure:
        self.ae_req_count += 1
        return False
      elif self.ae_req_count > -2 :
        self.ae_req_count -= 1
        return False
      else:
        self.exposure = 0
        return True

  def sample_frame(self, pre_roll_override=None):
    pre_roll = pre_roll_override  if pre_roll_override is not None else self.pre_roll
    self.grab(count=pre_roll + 1)
    self.calc_hist()

  def calc_hist(self):
    self.last_hist = self.hist
    self.hist = cv2.calcHist([self.gframe], [0], None, [self.HIST_BINS], [0,256])
    self.hist_nz = self.hist.nonzero()[0]

  def save_frame(self, tag):
    t = time.strftime('%Y%m%d-%H%M%S')
    cv2.imwrite('{}/t_{}-cam_{}-ea_{}-ex_{}-bri_{}-{}.jpg'.format(OUT_DIR, t, self.cam_num, self.auto_exposure, self.exposure, self.brightness, tag), self.cframe)
    logging.debug('Frame ({})- sum:{} hist_nz.size:{}/{} hist_nz:{}'.format(tag, self.gframe.sum(), self.hist_nz.size, self.hist.size, self.hist_nz))

  def load_frame(self, fname):
    self.cframe = cv2.imread(fname, 0)
    self.calc_hist()

  def disable(self):
    logging.info('Camera {} is not working.  Disabling'.format(self.cam_num))
    self.disabled = True

  def add_overlay(self):
    exposure_string = 'Auto' if self.auto_exposure else self.exposure
    info_string = 'Cam{} - Exposure: {}  Brightness: {}  Frame: {}'.format(self.cam_num, exposure_string, self.brightness, self.frame_num)
    cv2.putText(self.cframe, info_string, (10, 20), cv2.FONT_HERSHEY_PLAIN, 1.0, (255, 255, 255), lineType=cv2.LINE_AA)

  def grab(self, count=1):
    for i in range(count):
      if self.disabled:
        return False
      self.cframe_current = False
      self.gframe_current = False
      ret = self.cap.grab()
      if not ret:
        self.disable()
        return False
      else:
        self.frame_num += 1
    return True

  def cframe(self, v=None):
    if v is None:
      if self.disabled:
        return self.BLANK_FRAME
      elif self.cframe_current:
        return self._cframe
      else:
        ret, self._cframe = self.cap.retrieve()
        if not ret:
          self.disable()
          return self.BLANK_FRAME
        else:
          self.cframe_current = True
          self._cframe = cv2.resize(self._cframe, (W, H))
          return self._cframe
    else:
      self.cframe_current = True
      self._cframe = v

  @property
  def frame(self):
    if self.disabled:
      return self.BLANK_FRAME
    if self.camera_info_overlay:
      self.add_overlay()
    return self.cframe

  @property
  def gframe(self):
    if self.disabled:
      raise Exception('Camera {} is disabled'.format(self.cam_num))
    elif self.gframe_current:
      return self._gframe
    else:
      self._gframe = cv2.cvtColor(self.cframe, cv2.COLOR_BGR2GRAY)
      self.gframe_current = True
      return self._gframe

  @property
  def pre_roll(self):
    preroll = self.AE_PREROLL if self.auto_exposure else self.ME_PREROLL
    logging.debug('CAM{}-Using Preroll: {}'.format(self.cam_num, preroll))
    return preroll

  @property
  def hist_borders(self):
    return (self.hist_nz[0], self.hist.size - self.hist_nz[-1] -1)

  @property
  def hist_offset(self):
    hb = self.hist_borders
    return hb[0] - hb[1]

  def saturation(self, v=None):
    if v is None:
      return self.cap.get(cv2.CAP_PROP_SATURATION)
    else:
      self.cap.set(cv2.CAP_PROP_SATURATION, v)

  def brightness(self, v=None):
    if v is None:
      return self.cap.get(cv2.CAP_PROP_BRIGHTNESS)
    else:
      self.bdiff = v - self.brightness
      self.cap.set(cv2.CAP_PROP_BRIGHTNESS, v)
      logging.debug('CAM{}-Setting Brightness: {}'.format(self.cam_num, v))
      if v <= -64 or v >= 11:
        self.calibrating_brightness = False

  def exposure(self, v=None):
    if v is None:
      return self.cap.get(cv2.CAP_PROP_EXPOSURE)
    elif self.auto_exposure:
      self.auto_exposure = False
    self.cap.set(cv2.CAP_PROP_EXPOSURE, v)
    logging.debug('CAM{}-Setting Exposure: {}'.format(self.cam_num, v))

  def auto_exposure(self, v=None):
    if v is None:
      ae = self.cap.get(cv2.CAP_PROP_AUTO_EXPOSURE)
      return True if ae == 3 else False
    else:
      ae = 3 if v else 1
      self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, ae)
      logging.debug('CAM{}-Setting Auto Exposure: {}'.format(self.cam_num, v))
      return True

  cframe = property(cframe, cframe)
  saturation = property(saturation, saturation)
  brightness = property(brightness, brightness)
  exposure = property(exposure, exposure)
  auto_exposure = property(auto_exposure, auto_exposure)

def video_out_writer():
  t = time.strftime('%Y%m%d-%H%M%S')
  fourcc = cv2.VideoWriter_fourcc(*'mp4v')
  return cv2.VideoWriter('{}/video{}-{}.mkv'.format(OUT_DIR, 'all', t), fourcc, 10.0, (W*2,H*2))

def record_all():
  """ Record all cameras to a 2x2 grid while continually calibrating the camera settings """
  grid = np.zeros([H*2, W*2, 3], np.uint8)
  cams = {}
  for cam_num in [0, 2, 4, 6]:
    cams[cam_num] = Camera(cam_num)
    cams[cam_num].grab(count=cam_num*2)
  out = video_out_writer()
  out_start_time = time.time()
  try:
    while True:
      for cam in cams.values():
        if not cam.grab():
          continue
        elif cam.calibrating_brightness:
          cam.calibrate_brightness()
        elif cam.frame_num % cam.CALIBRATION_INTERVAL == 0:
          cam.check_calibration()
      grid[0:H, 0:W] = cams[0].frame
      grid[0:H, W:W*2] = cams[2].frame
      grid[H:H*2, 0:W] = cams[4].frame
      grid[H:H*2, W:W*2] = cams[6].frame
      out.write(grid)
      if time.time() >= out_start_time + RECORDING_SECONDS:
        out.release()
        out = video_out_writer()
        out_start_time = time.time()
  except Exception as ex:
    logging.error('Stopped with: {}'.format(ex))
  except:  # Keyboard
    pass
  out.release()


def calibrate_cameras():
  """ Calibrate each camera and return """
  for c in range(0, 7, 2):
    calibrate_camera(c)

def calibrate_camera(cam_num):
  """ Calibrate a single camera """
  cam = Camera(cam_num)
  cam.calibrate()

def record_camera(cam_num, secs=None):
  """ Record a given camera while continually calibrating the camera settings
  to give the best image.  Record for given number of secs.  If sec are  not given,
  we record continuously with separate 10 minute files.
  
  Note: Previous calibration is reset when Camera() is initialized.
  """
  cam = Camera(cam_num)
  if secs is not None:
    cam.record(secs)
  else:
    while True:
      cam.record(10 * 60)

def driving_test():
  while True:
    for c in range(0,7,2):
      #calibrate_camera(c)
      cam = Camera(c)
      cam.record(2 * 60)
    #time.sleep(10)

