import RPi.GPIO as gpio
import time
import datetime
from random import randint


gpio.setmode(gpio.BCM)
gpio.setup(17, gpio.OUT)
gpio.setup(24, gpio.IN)

welcome_img = '/home/adorno/proj_play/welcome.jpg'



class WelcomePopUp():

  def __init__(self):
    print('setting up')
    self.known_users = []

  def show_ad(self, target):
    gpio.output(17, True)
    print('Displaying asset: ', target)
    time.sleep(15)
    gpio.output(17, False)

  def get_motion_reading(self):
    return gpio.input(24)

  def get_low_mac(self):
    mac = 'test'+str(randint(0,6))
    return mac

  def check_mac(self, mac):
    for user in self.known_users:
      if mac in user['mac']:
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
        pop.show_ad(pop.check_mac(pop.get_low_mac()))
        time.sleep(5)
  except Exception as e:
    print('exception, cleaning up gpio')
    gpio.cleanup()
    print(e)


if __name__ == '__main__':
  main()
