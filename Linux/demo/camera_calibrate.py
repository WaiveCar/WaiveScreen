import logging
import os
import time
import cv2
from matplotlib import pyplot as plt

OUT_DIR = '/tmp/camera_test-{}/'.format(time.strftime('%H%M%S'))
os.mkdir(OUT_DIR)

format = '%(asctime)s %(levelname)s:%(message)s'
logging.basicConfig(filename='{}/test.log'.format(OUT_DIR), format=format, level=logging.DEBUG)
#logging.basicConfig(format=format, level=logging.DEBUG)

class Camera():
  MAX_PIXEL_THRESH_PERCENTAGE = 0.70
  MIN_DYNAMIC_RANGE = 0.80
  HIST_BINS = 32
  AE_PREROLL = 30
  ME_PREROLL = 5

  def __init__(self, cam_num):
    device = '/dev/video{}'.format(cam_num)
    self.cap = cv2.VideoCapture(device, apiPreference=cv2.CAP_V4L2)
    self.cam_num = cam_num
    self.saturation = 0.6
    self.frame = None
    self.cframe = None
    self.hist = None
    self.last_frame = None
    self.last_hist = None

  def sample_frame(self):
    for i in range(self.pre_roll):
      ret, frame = self.cap.read()
      if ret != True:
        return False
    self.last_frame = self.frame
    self.cframe = frame
    self.frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    self.last_hist = self.hist
    self.hist = cv2.calcHist([frame], [0], None, [self.HIST_BINS], [0,256])
    self.hist_nz = self.hist.nonzero()[0]
    return self.frame

  def save_frame(self, tag):
    t = time.strftime('%H%M%S')
    cv2.imwrite('{}/t_{}-cam_{}-ea_{}-ex_{}-bri_{}-{}.jpg'.format(OUT_DIR, t, self.cam_num, self.auto_exposure, self.exposure, self.brightness, tag), self.cframe)

  @property
  def pre_roll(self):
    return self.AE_PREROLL if self.auto_exposure else self.ME_PREROLL

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
      self.cap.set(cv2.CAP_PROP_BRIGHTNESS, v)

  def exposure(self, v=None):
    if v is None:
      return self.cap.get(cv2.CAP_PROP_EXPOSURE)
    else:
      self.cap.set(cv2.CAP_PROP_EXPOSURE, v)

  def auto_exposure(self, v=None):
    if v is None:
      ae = self.cap.get(cv2.CAP_PROP_AUTO_EXPOSURE)
      return True if ae == 0.75 else False
    else:
      ae = 0.75 if v else 0.25
      self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, ae)
      return True

  saturation = property(saturation, saturation)
  brightness = property(brightness, brightness)
  exposure = property(exposure, exposure)
  auto_exposure = property(auto_exposure, auto_exposure)


def calibrate_camera(cam_num):
  cam = Camera(cam_num)
  cam.auto_exposure = True
  cam.brightness = 0
  cam.sample_frame()
  cam.save_frame('first')
  if cam.frame.sum() > cam.frame.size * 255 * cam.MAX_PIXEL_THRESH_PERCENTAGE:
    logging.debug('Frame intensity too high: {}'.format(cam.frame.sum()))
    cam.exposure = 0
  if cam.hist_nz.size < cam.MIN_DYNAMIC_RANGE * cam.hist.size and \
      cam.hist_nz[-1] > cam.MIN_DYNAMIC_RANGE * cam.hist.size:
    logging.debug('Frame dynamic range too low: {}'.format(cam.hist))
    cam.exposure = 0
  brightness_calibration(cam)
  cam.sample_frame()
  cam.save_frame('final')

def brightness_calibration(cam):
  for b in range(5, -1, -1):
    b = b / 10.0
    cam.brightness = b
    logging.debug('Brightness set to: {}'.format(b))
    cam.sample_frame()
    cam.save_frame('bcal')
    logging.debug('Hist: {}'.format(cam.hist))
    logging.debug('Hist Offset: {}'.format(cam.hist_offset))
    if cam.hist_offset == 0:
      break
    elif cam.hist_offset < 0:
      if b == 0.5:
        break
      else:
        cam.brightness = b + 0.05
        break

def driving_test():
  while True:
    for c in range(0,7,2):
      calibrate_camera(c)
    time.sleep(10)
