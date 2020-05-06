import gpiod
import threading
import atexit
import logging
from time import sleep

# GPIO Pins are specified in the form (chip_number, pin_number)
GPIO_PIN_IN = (1, 10)
GPIO_PIN_OUT = (1, 9)


def bint(bin_list):
  return int(''.join(str(e) for e in bin_list), 2)


class DHT11():
  REQUEST_PULSE_MS = 18
  START_PULSE_NS = 80 * 1000
  ZERO_PULSE_NS = 27 * 1000
  ONE_PULSE_NS = 70 * 1000
  LOW_PULSE_NS = 54 * 1000

  def __init__(self, pin_in=GPIO_PIN_IN, pin_out=GPIO_PIN_OUT):
    self.chip_in = gpiod.Chip(str(pin_in[0]))
    self.pin_in = self.chip_in.get_line(pin_in[1])
    self.pin_in.request('dht11_in', gpiod.LINE_REQ_EV_BOTH_EDGES)

    self.chip_out = self.chip_in if pin_in[0] == pin_out[0] else gpiod.Chip(str(pin_out[0]))
    self.pin_out = self.chip_out.get_line(pin_out[1])
    self.pin_out.request('dht11_out', gpiod.LINE_REQ_DIR_OUT, gpiod.LINE_REQ_FLAG_OPEN_DRAIN)

    self.events = []
    self.msg = []
    self._temp = None
    self._humidity = None

    self.reader_running = False
    self.lock = threading.Lock()
    self.reader_thread = threading.Thread(target=self.reader_loop)

    self.start_margin_ns = 15 * 1000
    self.low_margin_ns = 5 * 1000
    self.data_margin_ns = 8 * 1000

  def pulse_in_margin(self, pulse_ns, target_ns, margin_ns):
    return True if target_ns - margin_ns <= pulse_ns <= target_ns + margin_ns else False

  def start_reader(self):
    self.reader_thread.start()
    atexit.register(self.stop_reader)

  def stop_reader(self):
    self.reader_running = False
    self.reader_thread.join()

  def reader_loop(self):
    if self.reader_running:
      logging.warning("A reader_thread is already running.  Aborting.")
      return
    self.reader_running = True

    while self.reader_running:
      sleep(2)

      self.read_sensor()
      self.process_events()
      reading = self.decode_msg(self.msg)
      if reading is not None:
        self.temp = reading['Temp']
        self.humidity = reading['Humidity']

  def read_sensor(self):
    self.events.clear()

    self.pin_out.set_value(0)
    sleep(self.REQUEST_PULSE_MS / 1000.0)
    self.pin_out.set_value(1)

    while len(self.events) < 100 and self.pin_in.event_wait(1):
      self.events.append(self.pin_in.event_read())

  def process_events(self):
    rising_error = 0
    last_nsec = 0
    last_type = gpiod.LineEvent.RISING_EDGE
    start_wait = True
    self.msg.clear()

    for e in self.events:
      if e.type == e.RISING_EDGE:
        rising_error = (e.nsec - last_nsec) - self.LOW_PULSE_NS
      elif e.type == e.FALLING_EDGE:
        pulse_length = e.nsec - last_nsec

        if start_wait:
          if self.pulse_in_margin(pulse_length, self.START_PULSE_NS, self.start_margin_ns):
            start_wait = False
          last_type = e.type
          last_nsec = e.nsec
          continue

        # Either a rising edge was missed or this edge was misclassified
        if e.type == last_type:
          if self.pulse_in_margin(pulse_length, self.LOW_PULSE_NS, self.low_margin_ns):
            # Probably a RISING misclassed as a FALLING
            last_nsec = e.nsec
            continue
          else:
            # Probably missed an edge, pretend it happened
            pulse_length -= self.LOW_PULSE_NS

        if self.pulse_in_margin(pulse_length, self.ZERO_PULSE_NS, self.data_margin_ns):
          self.msg.append(0)
        elif self.pulse_in_margin(pulse_length, self.ONE_PULSE_NS, self.data_margin_ns):
          self.msg.append(1)
        else:
          logging.debug("Unknown pulse length: {}us  {}".format(pulse_length/1000, e.nsec))
          logging.debug("Guessing based on rising_error")
          if abs(rising_error) > self.low_margin_ns:
            pulse_length += rising_error
          if pulse_length < 48500:
            self.msg.append(0)
          else:
            self.msg.append(1)
        logging.debug("{:2} {} - {}us  {}".format(len(self.msg), self.msg[-1], pulse_length/1000, e.nsec))
      last_type = e.type
      last_nsec = e.nsec

  def decode_msg(self, msg):
    if len(msg) < 40:
      logging.debug("Not enough packets received: {}".format(len(self.msg)))
      return None
    elif len(msg) > 40:
      for i in range(len(msg) - 40 + 1):
        r = self.decode_msg(msg[i:40+i])
        if r is not None:
          return r
      return None

    humidity_int = bint(msg[0:8])
    if humidity_int > 100:
      logging.debug("Impossible humidity: {}".format(humidity_int))
      return None
    humidity_dec = bint(msg[8:16])
    if msg[16] == 1:
      temp_int = - bint([0] + msg[17:24])
    else:
      temp_int = bint(msg[16:24])
    temp_dec = bint(msg[24:32])
    checksum = bint(msg[32:40])
    if (humidity_int + humidity_dec + temp_int + temp_dec) != checksum:
      logging.debug("Incorrect checksum")
      return None
    return {  'Temp': float("{}.{}".format(temp_int, temp_dec)),
              'Humidity': float("{}.{}".format(humidity_int, humidity_dec)) }

  def debug_events(self, e_list):
    last_nsec = 0
    for e in e_list:
      edge = '/' if e.type == 1 else '\\'
      print("{} - {}us   {}".format(edge, (e.nsec - last_nsec) / 1000, e.nsec))
      last_nsec = e.nsec

  def read(self):
    return { 'Temp': self.temp, 'Humidity': self.humidity }

  def temp(self, v=None):
    self.lock.acquire()
    if v is None:
      tmp_val = self._temp
      self.lock.release()
      return tmp_val
    else:
      self._temp = v
      self.lock.release()

  def humidity(self, v=None):
    self.lock.acquire()
    if v is None:
      tmp_val = self._humidity
      self.lock.release()
      return tmp_val
    else:
      self._humidity = v
      self.lock.release()

  temp = property(temp, temp)
  humidity = property(humidity, humidity)


