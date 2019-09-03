import logging
import os
import time
import threading
import traceback
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

CAM_NUMS = ( 0, 2, 4, 6 )
CAPTURE_RESOLUTIONS = { 480: (640,480), 
                        720: (1280, 720), 
                        1080: (1920, 1080) }
RECORDING_SECONDS = 60 * 10


class Camera():
  DEFAULT_BRIGHTNESS = -12
  DEFAULT_SATURATION = 60
  HIST_BINS = 32
  MAX_VALUE_PERCENTAGE = 0.15
  AE_SETTLE_SECS = 1.5
  ME_SETTLE_SECS = 0.2
  BRIGHTNESS_SECS = 0.1
  CALIBRATION_SECS = 3.0

  def __init__(self, cam_num, capture_res=720, output_scaling=1.0):
    device = '/dev/video{}'.format(cam_num)
    self.cap = cv2.VideoCapture(device, apiPreference=cv2.CAP_V4L2)
    self.cam_num = cam_num
    self.output_scaling = output_scaling
    self.cap_w, self.cap_h = CAPTURE_RESOLUTIONS[capture_res]
    self.out_w = int(self.cap_w * output_scaling)
    self.out_h = int(self.cap_h * output_scaling)
    self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.cap_w)
    self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.cap_h)
    self.auto_exposure = True
    self.brightness = self.DEFAULT_BRIGHTNESS
    self.saturation = self.DEFAULT_SATURATION
    self.frame_num = 0
    self.disabled = False
    self.capturing = False
    self.hist = None
    self.e_val = 0
    self.blank_frame = np.zeros([int(self.out_h), int(self.out_w), 3], np.uint8)
    self._cframe = self.blank_frame
    self.cframe_lock = threading.Lock()
    self.capture_thread = threading.Thread(target=self.capture_loop)
    self.calibrated_capture_thread = threading.Thread(target=self.calibrated_capture)
    self.calibrate_and_exit_thread = threading.Thread(target=self.calibrate_and_exit)

  def debug(self, msg):
    logging.debug('CAM_{}: {}'.format(self.cam_num, msg))

  def capture_loop(self):
    self.capturing = True
    self.capture_start_time = time.time()
    while self.capturing:
      ret, self.cframe = self.cap.read()
      if not ret:
        self.disabled = True
        self.capturing = False
      self.frame_num += 1
      self.debug('Frame: {} @ +{:.4f}'.format(self.frame_num, time.time() - self.capture_start_time))

  def calibrated_capture(self):
    self.e_val = 0
    if not self.capturing:
      self.capture_thread.start()
    while self.capturing:
      time.sleep(self.CALIBRATION_SECS)
      self.brightness_balance()
      self.evaluate_exposure()
      if self.e_val < -10:
        self.auto_exposure = True
      elif self.e_val > 10:
        self.exposure = 0

  def calibrate_and_exit(self):
    self.capture_thread.start()
    time.sleep(self.settle_secs)
    #self.save_frame('start')
    r = 0
    for i in range(3):
      self.evaluate_exposure()
      #self.save_frame('eval')
      time.sleep(0.1)
    if self.e_val > 0:
      self.exposure = 0
      time.sleep(self.settle_secs)
      self.calc_hist()
      if self.hist.max() > self.last_hist.max():
        self.auto_exposure = True
    self.brightness_balance()
    #self.save_frame('final')
    self.capturing = False

  def evaluate_exposure(self):
    self.calc_hist()
    if self.hist.max() / self.gframe.size > self.MAX_VALUE_PERCENTAGE:  # Under or Over Exposed
      if self.hist.argmax() < self.hist.size / 3:  # Under Exposed
        self.e_val -= 1
      elif self.hist.argmax() > (self.hist.size / 3) * 2:  # Over Exposed
        self.e_val += 1
    else:
      self.e_val = self.e_val / 2

  def brightness_balance(self):
    self.balancing_brightness = True
    self.b_diff = 0
    change_val = 4
    while self.balancing_brightness:
      self.calc_hist()
      #self.save_frame('bri')
      self.debug('hist_offset: {}'.format(self.hist_offset))
      if self.hist_offset < -1:
        if self.b_diff < 0:
          change_val = change_val / 2
          self.balancing_brightness = False
        self.brightness += change_val
      elif self.hist_offset > 1:
        if self.b_diff > 0:
          change_val = change_val / 2
          self.balancing_brightness = False
        self.brightness -= change_val
      else:
        self.balancing_brightness = False
      time.sleep(self.BRIGHTNESS_SECS)

  def calc_hist(self):
    self.last_hist = self.hist
    self.hist = cv2.calcHist([self.gframe], [0], None, [self.HIST_BINS], [0, 256])
    self.hist_nz = self.hist.nonzero()[0]

  def add_overlay(self, frame):
    exposure_string = 'Auto' if self.auto_exposure else self.exposure
    cam_settings_string = 'Cam{} - Exposure: {}  Brightness: {}  Frame: {}'.format(self.cam_num, exposure_string, self.brightness, self.frame_num)
    cv2.putText(frame, cam_settings_string, (10, 20), cv2.FONT_HERSHEY_PLAIN, 1.0, (100, 225, 40), lineType=cv2.LINE_AA)
    if self.hist is not None:
      hist_string = 'Hist Offset: {}  Hist Borders: {}  Hist Max: {} @ {}  E-val: {}'.format(self.hist_offset, self.hist_borders, self.hist.max(), self.hist.argmax(), self.e_val)
      cv2.putText(frame, hist_string, (10, 40), cv2.FONT_HERSHEY_PLAIN, 1.0, (100, 225, 40), lineType=cv2.LINE_AA)
    return frame

  def save_frame(self, tag):
    t = time.strftime('%Y%m%d-%H%M%S')
    frame = self.frame
    frame = self.add_overlay(frame)
    cv2.imwrite('{}/t_{}-cam_{}-{}-ea_{}-ex_{}-bri_{}.jpg'.format(OUT_DIR, t, self.cam_num, tag, self.auto_exposure, self.exposure, self.brightness), frame)

  @property
  def hist_borders(self):
    return (self.hist_nz[0], self.hist.size - self.hist_nz[-1] -1)

  @property
  def hist_offset(self):
    hb = self.hist_borders
    return hb[0] - hb[1]

  @property
  def settle_secs(self):
    return self.AE_SETTLE_SECS if self.auto_exposure else self.ME_SETTLE_SECS

  @property
  def fps(self):
    return self.cap.get(cv2.CAP_PROP_FPS)

  @property
  def gframe(self):
    return cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)
  
  @property
  def oframe(self):
    return self.add_overlay(self.frame)

  @property
  def frame(self):
    if self.output_scaling == 1:
      return self.cframe
    else:
      return cv2.resize(self.cframe, (self.out_w, self.out_h))

  def cframe(self, v=None):
    if v is None:
      if self.disabled:
        return self.blank_frame
      else:
        self.cframe_lock.acquire()
        cframe = self._cframe
        self.cframe_lock.release()
        return cframe
    else:
      self.cframe_lock.acquire()
      self._cframe = v
      self.cframe_lock.release()

  def saturation(self, v=None):
    if v is None:
      return self.cap.get(cv2.CAP_PROP_SATURATION)
    else:
      self.cap.set(cv2.CAP_PROP_SATURATION, v)

  def brightness(self, v=None):
    if v is None:
      return self.cap.get(cv2.CAP_PROP_BRIGHTNESS)
    else:
      self.b_diff = v - self.brightness
      self.debug('Setting Brightness: {}'.format(v))
      self.cap.set(cv2.CAP_PROP_BRIGHTNESS, v)
      if v <= -64 or v >= 20:
        self.balancing_brightness = False

  def exposure(self, v=None):
    if v is None:
      return self.cap.get(cv2.CAP_PROP_EXPOSURE)
    elif self.auto_exposure:
      self.auto_exposure = False
    self.debug('Setting Exposure: {}'.format(v))
    self.cap.set(cv2.CAP_PROP_EXPOSURE, v)

  def auto_exposure(self, v=None):
    if v is None:
      ae = self.cap.get(cv2.CAP_PROP_AUTO_EXPOSURE)
      return True if ae == 3 else False
    else:
      ae = 3 if v else 1
      self.debug('Setting Auto Exposure: {}'.format(v))
      self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, ae)

  cframe = property(cframe, cframe)
  saturation = property(saturation, saturation)
  brightness = property(brightness, brightness)
  exposure = property(exposure, exposure)
  auto_exposure = property(auto_exposure, auto_exposure)


def calibrate_cameras():
  cams = []
  for cam_num in CAM_NUMS:
    cams.append(Camera(cam_num))
  for cam in cams:
    cam.calibrate_and_exit_thread.start()
  for cam in cams:
    cam.calibrate_and_exit_thread.join()

def video_out_writer(w, h, fps, codec='mp4v', cam_num='all'):
  t = time.strftime('%Y%m%d-%H%M%S')
  fourcc = cv2.VideoWriter_fourcc(*codec)
  return cv2.VideoWriter('{}/cam_{}-{}.mkv'.format(OUT_DIR, cam_num, t), fourcc, fps, (int(w),int(h)))

def record_all(capture_res=720, scaling=0.5):
  """ Record all cameras to a 2x2 grid while continually calibrating the camera settings """
  cap_w, cap_h = CAPTURE_RESOLUTIONS[capture_res]
  out_w = int(cap_w * scaling)
  out_h = int(cap_h * scaling)
  grid = np.zeros([out_h*2, out_w*2, 3], np.uint8)
  cams = []
  for cam_num in CAM_NUMS:
    cams.append( Camera(cam_num, capture_res=capture_res, output_scaling=scaling) )
  fps = cams[0].fps
  out = video_out_writer(out_w*2, out_h*2, fps)
  try:
    for cam in cams:
      cam.calibrated_capture_thread.start()
    out_start_time = last_frame_time = time.time()
    frame_time = 1.0 / fps
    while True:
      grid[0:out_h, 0:out_w] = cams[0].frame
      grid[0:out_h, out_w:out_w*2] = cams[1].frame
      grid[out_h:out_h*2, 0:out_w] = cams[2].frame
      grid[out_h:out_h*2, out_w:out_w*2] = cams[3].frame
      out.write(grid)
      if time.time() >= out_start_time + RECORDING_SECONDS:
        out.release()
        out = video_out_writer(out_w*2, out_h*2, fps)
        out_start_time = time.time()
      sleep_time = (last_frame_time + frame_time) - time.time()
      logging.debug('sleep_time: {}'.format(sleep_time))
      if sleep_time > 0:
        time.sleep(sleep_time)
      last_frame_time = time.time()
  except Exception as ex:
    logging.error('Stopped with: {}'.format(ex))
    traceback.print_exception(type(ex), ex, ex.__traceback__)
  except:  # Keyboard
    pass
  for cam in cams:
    cam.capturing = False
  out.release()

