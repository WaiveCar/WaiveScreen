import logging
import os
import collections
import glob
import lis3dh
from mpu6050 import mpu6050
from ADS1115 import ADS1115
from time import time
from numpy import interp
from . import dht11
from .lib import is_rpi

#TODO: proper logging integration

"""
Screen v3.0 sensors library for SOM-RK3399 and Raspberry Pi 4B.

SOM-RK3399:
  Wiring Diagram: WaiveScreen/docs/sensors_wiring-som_rk3399.png

  3-Axis Accelerometer: The carrier board has a built-in LIS3DH on the i2c-3 bus.
    We're using a python library that talks to it directly over the i2c bus because
    it gives us faster read times than the linux kernel driver did.

  Temp / Humidity: We're connecting a DHT-11 to the GPIO1_B1 and GPIO1_B2 pins.

  Voltage / Current / Light: These sensors are connected to board's the ADC inputs.

Raspberry Pi 4B:
  Wiring Diagram: WaiveScreen/docs/sensors_wiring-rpi_4b.png

  6-DOF Accelerometer/Gyro/Temp: We're connecting an MPU-6050 to the i2c-1 bus.
    We're using a python library that talks to it directly over the i2c bus.  The
    sensor gives us Acceleration, Gyro and a Temperature reading.

  Temp / Humidity: We're connecting a DHT-11 to the GPIO0_17 and GPIO0_18 pins.

  Voltage / Current / Light: We're connecting an ADS1115 to the i2c-1 bus.  This
  gives us 4 ADC inputs.
  
"""

_sensors = None

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
    if raw:
      try:
        return [ (name, interp(float(raw), sensor.in_scale, sensor.out_scale)) ]
      except ValueError as ex:
        logging.error("ADC Value Error ({}): {}".format(sensor.file.name, ex))
  except OSError as ex:
    logging.error("ADC Read Error ({}): {}".format(sensor.file.name, ex))
  return None

def ads1115_read(sensor_tuple, pin):
  name, sensor = sensor_tuple
  try:
    #TODO: adjust voltage range and sample rate for production sensors
    raw = sensor.file.readADCSingleEnded(channel=pin, pga=4096, sps=128)
    logging.debug("Raw ADC Read {}: {}".format(pin, raw))
    #TODO: REMOVE after demo
    if raw == 0 or raw == False:
      return [ (name, 0.0) ]
    try:
      return [ (name, interp(float(raw), sensor.in_scale, sensor.out_scale)) ]
    except ValueError as ex:
      logging.error("ADS1115 Value Error ({}): {}".format(name, ex))
  except OSError as ex:
    logging.error("ADS1115 - Unable to read from pin {}: {}".format(pin, ex))
  return None

def lis3dh_read(sensor_tuple):
  name, sensor = sensor_tuple
  try:
    x, y, z = sensor.file.read_all_axes()
    return [('Accel_x', x), ('Accel_y', y), ('Accel_z', z)]
  except Exception as ex:
    logging.error("Unable to read from LIS3DH sensor: {}".format(ex))
  return None

def mpu6050_read(sensor_tuple):
  name, sensor = sensor_tuple
  try:
    a_x, a_y, a_z = sensor.file.get_accel_data().values()
    g_x, g_y, g_z = sensor.file.get_gyro_data().values()
    t = sensor.file.get_temp()
    return [('Accel_x', a_x), ('Accel_y', a_y), ('Accel_z', a_z), 
            ('Gyro_x', g_x), ('Gyro_y', g_y), ('Gyro_z', g_z), 
            ('Temp_2', t) ]
  except OSError as ex:
    logging.error("Unable to read from MPU6050 sensor: {}".format(ex))
  return None

def dht_read(sensor_tuple):
  name, sensor = sensor_tuple
  sensor_dict = sensor.file.read()
  return [ (k, v) for k, v in sensor_dict.items() if v is not None ]

def get_sensors():
  """ Assemble a dict of Sensor tuples for our platform """

  sensors = {}
  Sensor = collections.namedtuple('Sensor', ['reader', 'file', 'in_scale', 'out_scale'])

  if is_rpi():
    # Initialize sensors for Raspberry Pi 4B
    dht_pin_in = (0, 17)
    dht_pin_out = (0, 18)

    try:
      ads = ADS1115()
      # TODO: set appropriate scales for production sensors
      for pin, name, out_scale in [(0, 'Light', [100, 0]), (2, 'Voltage', [0, 30]), (3, 'Current', [-15, 15])]:
        try:
          v = ads.readADCSingleEnded(channel=pin)
          reader = lambda x, p=pin: ads1115_read(x, p)
          sensors[name] = Sensor(reader, ads, [0, 3300], out_scale)
        except OSError as ex:
          logging.error("ADS1115 - Error reading from pin {}: {}".format(pin, ex))
    except Exception as ex:
      logging.error("Failure to setup ADS1115 sensor: {}".format(ex))

    try:
      mpu = mpu6050(0x68)
      sensors['6Dof'] = Sensor(mpu6050_read, mpu, None, None)
    except OSError as ex:
      logging.error("Failure to setup MPU6050 sensor: {}".format(ex))

  else:
    # Initialize sensors for SOM-RK3399
    dht_pin_in = (1, 10)
    dht_pin_out = (1, 9)

    try:
      registers = lis3dh.device()
      # TODO: Test on car what scale we should be using.
      lis = lis3dh.LIS3DH(port=3, scale=registers.CTRL_REG4.SCALE_16G, data_rate=registers.CTRL_REG1.ODR_50Hz)
      if lis.read_dummy_register() == lis.NO_ERROR:
        lis.enable_axes(registers.CTRL_REG1.Xen | registers.CTRL_REG1.Yen | registers.CTRL_REG1.Zen)
        lis.registers = registers
        sensors['3Accel'] = Sensor(lis3dh_read, lis, None, None)
    except Exception as ex:
      logging.error("Failure to setup LIS3DH sensor: {}".format(ex))

    adc_dev = iio_device_path('ff100000.saradc')
    if adc_dev:
      # TODO: set appropriate scales for production sensors
      for pin, name, out_scale in [(0, 'Light', [0, 100]), (2, 'Voltage', [0, 30]), (3, 'Current', [-15, 15])]:
        f = sensor_sysfs_open("{}/in_voltage{}_raw".format(adc_dev, pin))
        if f:
          sensors[name] = Sensor(adc_read, f, [0, 1023], out_scale)

  try:
    dht = dht11.DHT11(dht_pin_in, dht_pin_out)
    dht.start_reader()
    sensors['dht11'] = Sensor(dht_read, dht, None, None)
  except Exception as ex:
    logging.error("Failure to setup DHT11 sensor: {}".format(ex))

  return sensors

def sensors_read():
  """ Get the list of Sensor tuples if needed.  Then call each Sensor's read
      method and return the results. """
  t_start = time()
  global _sensors
  if _sensors is None:
    logging.debug("getting _sensors")
    _sensors = get_sensors()
  s = {}
  for name, sensor in _sensors.items():
    reading_list = sensor.reader((name, sensor))
    if reading_list is None:
      # If a sensor stops working, we just drop it.
      del _sensors[name]
      continue
    for n, v in reading_list:
      s[n] = v
      logging.debug("{}: {}".format(n, v))
    #logging.debug("{}: {}".format(name, sensor.reader((name, sensor))))
    #logging.debug("TIME: {}".format(time() - t_start))
  return s
