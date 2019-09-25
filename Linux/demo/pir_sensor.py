import RPi.GPIO as gpio
import time
import datetime
from random import randint
import probemon


gpio.setmode(gpio.BCM)
gpio.setup(17, gpio.OUT)
gpio.setup(24, gpio.IN)

assets = [
    '/home/adorno/WaiveScreen/Linux/demo/assets/Slide1.JPG',
    '/home/adorno/WaiveScreen/Linux/demo/assets/Slide2.JPG',
    '/home/adorno/WaiveScreen/Linux/demo/assets/Slide3.JPG',
    '/home/adorno/WaiveScreen/Linux/demo/assets/Slide4.JPG'
    ]
q = probemon.start_scanning_module()

class WelcomePopUp():

  def __init__(self):
    print('setting up')
    self.known_users = [{'mac': 0, 'target': -1}]

  def show_ad(self, target):
    if not target == -1:
      gpio.output(17, True)
      print('Displaying asset: ', assets[target])
      time.sleep(15)
      gpio.output(17, False)

  def get_motion_reading(self):
    return gpio.input(24)

  def get_low_mac(self, list_of_mac):
    # find the lowest (in dBm) signal strength, and return that user.  Try to filter out known close beacons (when the sensor not tripped)
    low_rssi = -200
    max_count = 0
    print("length of q list = ",len(list_of_mac))
    for each in list_of_mac:
      max_count = max(each['seen_count'],max_count)
      if each['mac_addr'] == 'c8:3c:85:96:30:4f':
        print('\n\n\n *******************JAMES*****************', each, '*********************************\n\n\n')
    for mac in list_of_mac:
      print('age: {:.4f} seen: {} \t\t\tmac: {}'.format((time.time()-mac['last_seen']), mac['seen_count'], mac['mac_addr']))
      if not mac['ssid'] and mac['seen_count'] < max_count/3 and time.time() - mac['last_seen'] < 30:
        print("*********************************")
        print(mac['cur_rssi'], mac['mac_addr'], mac['seen_count'], max_count)
        return mac['mac_addr']
    return 0

  def get_macs(self):
    return q.get()

  def check_mac(self, mac):
    if len(self.known_users):
      for user in self.known_users:
        print(user)
        if mac == user['mac']:
          return user['target']
    target = len(self.known_users)%4
    print("creating user {} with target {}".format(mac, target))
    self.known_users.append({'mac': mac, 'target': target})
    return target


def main():
  pop = WelcomePopUp()
  try: 
    time.sleep(2)
    while True: 
      if pop.get_motion_reading():
        pop.show_ad(pop.check_mac(pop.get_low_mac(pop.get_macs())))
        time.sleep(5)
  except Exception as e:
    print('exception, cleaning up gpio')
    gpio.cleanup()
    raise(e)


if __name__ == '__main__':
  main()
