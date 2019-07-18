import dbus
import requests
import json
import subprocess
import logging
from time import sleep
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib

DBusGMainLoop(set_as_default=True)

WIFI_IF = 'wlp1s0'
WPA_BUS_NAME = 'fi.w1.wpa_supplicant1'
WPA_OBJECT_NAME = '/fi/w1/wpa_supplicant1'
WPA_IF_NAME = '{}.Interface'.format(WPA_BUS_NAME)
WPA_BSS_NAME = '{}.BSS'.format(WPA_BUS_NAME)
DBUS_PROPERTIES = 'org.freedesktop.DBus.Properties'

_bss_array = dbus.Array()
_cb_count = 0

BUS = dbus.SystemBus()
_wpa_proxy = BUS.get_object(WPA_BUS_NAME, WPA_OBJECT_NAME)

def bytes_to_mac_addr(bytes_list):
  return ':'.join(list(map( '{:02x}'.format, bytes_list)))

def wifi_scan_startup():
  s = subprocess.run('sudo systemctl stop hostapd', shell=True)
  iface = dbus.Interface(_wpa_proxy, dbus_interface=WPA_BUS_NAME)
  try:
    iface.CreateInterface({'Ifname': WIFI_IF})
  except Exception as ex:
    logging.warning('Error creating Wifi Interface in DBus wpa_supplicant: {}'.format(ex))
  
def wifi_scan_shutdown():
  iface = dbus.Interface(_wpa_proxy, dbus_interface=WPA_BUS_NAME)
  try:
    iface.RemoveInterface(iface.GetInterface(WIFI_IF))
  except Exception as ex:
    logging.warning('Error removing Wifi Interface in DBus wpa_supplicant: {}'.format(ex))
  s = subprocess.run('sudo systemctl start hostapd', shell=True)

def dbus_wifi_if_array():
  props = dbus.Interface(_wpa_proxy, dbus_interface=DBUS_PROPERTIES)
  return props.Get(WPA_BUS_NAME, 'Interfaces')

def collect_scan_results(scan_done, iface, obj):
  global _bss_array, loop, _cb_count
  proxy = BUS.get_object(WPA_BUS_NAME, obj)
  props = dbus.Interface(proxy, dbus_interface=DBUS_PROPERTIES)
  _bss_array += props.Get(WPA_IF_NAME, 'BSSs')
  _cb_count -= 1
  if _cb_count == 0:
    loop.quit()

def generate_wifi_ap_dict():
  l = []
  for bss in _bss_array:
    props = bss_props(bss)
    l.append({ 'macAddress': bytes_to_mac_addr(props['BSSID']), 'signalStrength': props['Signal'] })
  return { 'wifiAccessPoints': l }

def bss_props(bss_object):
  proxy = BUS.get_object(WPA_BUS_NAME, bss_object)
  props = dbus.Interface(proxy, dbus_interface=DBUS_PROPERTIES)
  return props.GetAll(WPA_BSS_NAME)

def wifi_location():
  global _cb_count, loop
  try:
    wifi_scan_startup()

    for wifi_if in dbus_wifi_if_array():
      print(wifi_if)
      if_proxy = BUS.get_object(WPA_BUS_NAME, wifi_if)
      wpa_if = {
        'iface': dbus.Interface(if_proxy, dbus_interface=WPA_IF_NAME),
        'props': dbus.Interface(if_proxy, dbus_interface=DBUS_PROPERTIES)
      }
      wpa_if['iface'].Scan({'Type': 'active'})
      wpa_if['iface'].connect_to_signal('ScanDone', collect_scan_results, dbus_interface=WPA_IF_NAME, interface_keyword='iface', path_keyword='obj')
      _cb_count += 1

    if _cb_count > 0:
      loop = GLib.MainLoop()
      timeout_id = GLib.timeout_add_seconds(10, loop.quit)
      loop.run()
      GLib.source_remove(timeout_id)

    d = generate_wifi_ap_dict()

    wifi_scan_shutdown()

    url = 'https://location.services.mozilla.com/v1/geolocate?key=test'
    r = requests.post(url, json=d)
    if r.status_code == 200:
      location = json.loads(r.text)
    else:
      return {}

    return { 'Lat': location['location']['lat'], 'Lng': location['location']['lat'] }
  except Exception as ex:
    logging.warning('There was an error while determing our location via Wifi: {}'.format(ex))
    return {}

