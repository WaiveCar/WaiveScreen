import logging
import os
import time
import cv2
from matplotlib import pyplot as plt
import numpy as np

OUT_DIR='/tmp/camera_recordings'
try:
  os.mkdir(OUT_DIR)
except:
  pass

log_format = '%(asctime)s %(levelname)s:%(message)s'
logging.basicConfig(filename='{}/camera.log'.format(OUT_DIR), format=log_format, level=logging.DEBUG)
#logging.basicConfig(format=log_format, level=logging.DEBUG)

class Camera():
  MAX_VALUE_PERCENTAGE = 0.15
  HIST_BINS = 32
  AE_PREROLL = 25
  ME_PREROLL = 5
  DEFAULT_SATURATION = 0.6
  DEFAULT_BRIGHTNESS = 0.4
  CALIBRATION_INTERVAL = 120  # Frames

  def __init__(self, cam_num):
    device = '/dev/video{}'.format(cam_num)
    self.cap = cv2.VideoCapture(device, apiPreference=cv2.CAP_V4L2)
    self.cam_num = cam_num
    self.saturation = self.DEFAULT_SATURATION
    self.auto_exposure = True
    self.brightness = self.DEFAULT_BRIGHTNESS
    self.frame = None
    self.cframe = None
    self.hist = None
    self.last_frame = None
    self.last_hist = None
    self.calibrating_brightness = False
    self.ae_req_count = 0
    self.frame_num = 1

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
    self.out = cv2.VideoWriter('{}/video{}-{}.mp4'.format(OUT_DIR, self.cam_num, t), fourcc, 30.0, (640,480))
    self.frame_num = 1
    if for_secs:
      last_frame = for_secs * 30
    try:
      while self.cap.isOpened() and self.frame_num <= last_frame:
        ret, self.cframe = self.cap.read()
        if ret:
          self.out.write(self.cframe)
        if self.calibrating_brightness:
          self.calibrate_brightness()
        elif self.frame_num % self.CALIBRATION_INTERVAL == 0:
          self.check_calibration()
        self.frame_num += 1
    except Exception as ex:
      logging.error('Stopped with: {}'.format(ex))
    except:  # Keyboard
      pass
    self.out.release()
  
  def check_calibration(self):
    switching = False
    self.frame = cv2.cvtColor(self.cframe, cv2.COLOR_BGR2GRAY)
    self.calc_hist()
    if self.hist.max() / self.frame.size > self.MAX_VALUE_PERCENTAGE:  # Over Exposed
      if self.hist.argmax() < self.hist.size / 2:
        logging.debug('Frame hist.max() too low: {} @ {}'.format(self.hist.max() / self.frame.size, self.hist.argmax()))
        switching = self.request_exposure('auto')
      else:
        logging.debug('Frame hist.max() too high: {} @ {}'.format(self.hist.max() / self.frame.size, self.hist.argmax()))
        switching = self.request_exposure('manual')
      if switching:
        logging.debug('Changing Exposure')
        self.brightness = 0.4
      self.cal_int = 0.1
    else:
      self.cal_int = 0.05
    self.bdiff = 0
    self.calibrating_brightness = True
    self.next_cal_frame_num = self.pre_roll + self.frame_num
    return switching

  def calibrate_brightness(self, force_run=False):
    if self.next_cal_frame_num == self.frame_num or force_run:
      self.frame = cv2.cvtColor(self.cframe, cv2.COLOR_BGR2GRAY)
      self.calc_hist()
      logging.debug('Hist Offset: {}'.format(self.hist_offset))
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
    for i in range(pre_roll):
      self.cap.grab()
    ret, self.cframe = self.cap.read()
    if ret != True:
      return False
    self.frame = cv2.cvtColor(self.cframe, cv2.COLOR_BGR2GRAY)
    self.calc_hist()
    return self.frame

  def calc_hist(self):
    self.last_hist = self.hist
    self.hist = cv2.calcHist([self.frame], [0], None, [self.HIST_BINS], [0,256])
    self.hist_nz = self.hist.nonzero()[0]

  def save_frame(self, tag):
    t = time.strftime('%Y%m%d-%H%M%S')
    cv2.imwrite('{}/t_{}-cam_{}-ea_{}-ex_{}-bri_{}-{}.jpg'.format(OUT_DIR, t, self.cam_num, self.auto_exposure, self.exposure, self.brightness, tag), self.cframe)
    logging.debug('Frame ({})- sum:{} hist_nz.size:{}/{} hist_nz:{}'.format(tag, self.frame.sum(), self.hist_nz.size, self.hist.size, self.hist_nz))

  def load_frame(self, fname):
    self.frame = cv2.imread(fname, 0)
    self.calc_hist()

  @property
  def pre_roll(self):
    preroll = self.AE_PREROLL if self.auto_exposure else self.ME_PREROLL
    logging.debug('Using Preroll: {}'.format(preroll))
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
      logging.debug('Setting Brightness: {}'.format(v))
      if v <= 0 or v >= 1:
        self.calibrating_brightness = False

  def exposure(self, v=None):
    if v is None:
      return self.cap.get(cv2.CAP_PROP_EXPOSURE)
    elif self.auto_exposure:
      self.auto_exposure = False
    self.cap.set(cv2.CAP_PROP_EXPOSURE, v)
    logging.debug('Setting Exposure: {}'.format(v))

  def auto_exposure(self, v=None):
    if v is None:
      ae = self.cap.get(cv2.CAP_PROP_AUTO_EXPOSURE)
      return True if ae == 0.75 else False
    else:
      ae = 0.75 if v else 0.25
      self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, ae)
      logging.debug('Setting Auto Exposure: {}'.format(v))
      return True

  saturation = property(saturation, saturation)
  brightness = property(brightness, brightness)
  exposure = property(exposure, exposure)
  auto_exposure = property(auto_exposure, auto_exposure)


def record_all():
  """ Record all cameras to a 2x2 grid while continually calibrating the camera settings """
  t = time.strftime('%Y%m%d-%H%M%S')
  w = 640
  h = 480
  fourcc = cv2.VideoWriter_fourcc(*'mp4v')
  out = cv2.VideoWriter('{}/video{}-{}.mkv'.format(OUT_DIR, 'all', t), fourcc, 30.0, (w*2,h*2))
  grid = np.zeros([h*2, w*2, 3], np.uint8)
  cams = {}
  for cam_num in [0, 2, 4, 6]:
    cams[cam_num] = Camera(cam_num)
    cams[cam_num].frame_num = 1
  try:
    while True:
      for cam in cams.values():
        ret, cam.cframe = cam.cap.read()
        if not ret:
          pass
        elif cam.calibrating_brightness:
          cam.calibrate_brightness()
        elif cam.frame_num % cam.CALIBRATION_INTERVAL == 0:
          cam.check_calibration()
        cam.frame_num += 1
      grid[0:h, 0:w] = cams[0].cframe
      grid[0:h, w:w*2] = cams[2].cframe
      grid[h:h*2, 0:w] = cams[4].cframe
      grid[h:h*2, w:w*2] = cams[6].cframe
      out.write(grid)
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

