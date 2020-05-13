import logging
import os
import collections
import glob
import lis3dh
from time import time
from numpy import interp
#from concurrent.futures import ThreadPoolExecutor

_sensors = False
#sensor_read_pool = ThreadPoolExecutor(max_workers=10)

def iio_device_path(device_name):
  for n in glob.glob('/sys/bus/iio/devices/*/name'):
    with open(n, 'r') as f:
      name = f.readline().strip()
      if name == device_name:
        return os.path.dirname(n)

def sensor_sysfs_open(filename):
  try:
    f = open(filename, 'r')
  except OSError as ex:
    logging.error("Unable to open Sensor ({}): {}".format(filename, ex))
    return False
  return f

def adc_read(sensor_tuple):
  name, sensor = sensor_tuple
  try:
    sensor.file.seek(0)
    raw = sensor.file.readline().strip()
  except OSError as ex:
    logging.error("ADC Read Error ({}): {}".format(sensor.file.name, ex))
  if raw:
    try:
      return [ (name, interp(float(raw), sensor.in_scale, sensor.out_scale)) ]
    except ValueError as ex:
      logging.error("ADC Value Error ({}): {}".format(sensor.file.name, ex))
  return name, None

def accel_read(sensor_tuple):
  name, sensor = sensor_tuple
  x, y, z = sensor.file.read_all_axes()
  return [('Accel_x', x), ('Accel_y', y), ('Accel_z', z)]

def sensor_read_old(sensor):
  raw = sensor.f.readline().strip()
  sensor.f.seek(0)
  if raw:
    try:
      return float(raw)
    except ValueError as ex:
      logging.error("Sensor Read Error ({}): {}".format(sensor.f.name, ex))
  return None

def get_sensors():
  sensors = {}
  Sensor = collections.namedtuple('Sensor', ['reader', 'file', 'in_scale', 'out_scale'])

  try:
    registers = lis3dh.device()
    # TODO: Test on car what scale we should be using.
    lis = lis3dh.LIS3DH(port=3, scale=registers.CTRL_REG4.SCALE_16G, data_rate=registers.CTRL_REG1.ODR_50Hz)
    if lis.read_dummy_register() == lis.NO_ERROR:
      lis.enable_axes(registers.CTRL_REG1.Xen | registers.CTRL_REG1.Yen | registers.CTRL_REG1.Zen)
      lis.registers = registers
      sensors['3Accel'] = Sensor(accel_read, lis, None, None)
  except Exception as ex:
    logging.error("Failure to setup LIS3DH sensor: {}".format(ex))

  adc_dev = iio_device_path('ff100000.saradc')
  if adc_dev:
    for pin, name, out_scale in [(0, 'Light', [0, 100]), (2, 'Voltage', [0, 30]), (3, 'Current', [-15, 15])]:
      f = sensor_sysfs_open("{}/in_voltage{}_raw".format(adc_dev, pin))
      if f:
        sensors[name] = Sensor(adc_read, f, [0, 1023], out_scale)

  try:
    dht = DHT11()
    dht.start_reader()
    sensors['dht11'] = Sensor(dht.read, None, None, None)
  except Exception as ex:
    logging.error("Failure to setup DHT11 sensor: {}".format(ex))

  return sensors

def sensors_read():
  t_start = time()
  global _sensors
  if not _sensors:
    logging.debug("getting _sensors")
    _sensors = get_sensors()
  s = {}
  for name, sensor in _sensors.items():
    reading_list = sensor.reader((name, sensor))
    for n, v in reading_list:
      s[n] = v
    logging.debug("{}: {}".format(name, sensor.reader((name, sensor))))
    logging.debug("TIME: {}".format(time() - t_start))
  return s
