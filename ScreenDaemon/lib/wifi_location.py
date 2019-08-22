import dbus
import requests
import json
import subprocess
import logging
import time
from . import db
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib

DBusGMainLoop(set_as_default=True)

WIFI_IF = 'wlp1s0'
WPA_BUS_NAME = 'fi.w1.wpa_supplicant1'
WPA_OBJECT_NAME = '/fi/w1/wpa_supplicant1'
WPA_IF_NAME = '{}.Interface'.format(WPA_BUS_NAME)
WPA_BSS_NAME = '{}.BSS'.format(WPA_BUS_NAME)
DBUS_PROPERTIES = 'org.freedesktop.DBus.Properties'

_bss_array = False
_cb_count = 0
_signals = []
_current_macs = set()
_previous_macs = set()
_last_location = {}

BUS = dbus.SystemBus()
_wpa_proxy = BUS.get_object(WPA_BUS_NAME, WPA_OBJECT_NAME)

def bytes_to_mac_addr(bytes_list):
  """ Converts the byte format, returned by the scan, to the
  more common hex format expected by MLS """
  return ':'.join(list(map( '{:02x}'.format, bytes_list)))

def is_same_scan_data():
  """ Check to see if the current scan results are similar enough
  to the previous scan (by 75%). """
  logging.debug('_previous_macs: {}\n_current_macs: {}'.format(_previous_macs, _current_macs))
  if len(_current_macs & _previous_macs) >= len(_current_macs) * 0.75:
    return True
  else:
    return False

def wifi_last_submission(set_it=False):
  if set_it:
    db.kv_set('wifi_last_submission', int(time.time()))
  else:
    t = db.kv_get('wifi_last_submission', use_cache=True)
    return 0.0 if t is None else float(t)

def wifi_scan_startup():
  """ Check if wpa_supplicant already has control of the wifi interface.
  If not, we shutdown hostapd (which locks the interface) and then create
  it in wpa_supplicant. """
  iface = dbus.Interface(_wpa_proxy, dbus_interface=WPA_BUS_NAME)
  try:
    iface.GetInterface(WIFI_IF)
  except: 
    logging.debug('hostapd was running')
    s = subprocess.run('sudo systemctl stop isc-dhcp-server', shell=True, timeout=5)
    s2 = subprocess.run('sudo systemctl stop hostapd', shell=True, timeout=5)
    try:
      iface.CreateInterface({'Ifname': WIFI_IF})
    except Exception as ex:
      logging.error('Error creating Wifi Interface in DBus wpa_supplicant: {}'.format(ex))
  
def wifi_scan_shutdown():
  """ Remove the interface from wpa_supplicant, then start hostapd. """
  iface = dbus.Interface(_wpa_proxy, dbus_interface=WPA_BUS_NAME)
  try:
    iface.RemoveInterface(iface.GetInterface(WIFI_IF))
  except Exception as ex:
    logging.error('Error removing Wifi Interface in DBus wpa_supplicant: {}'.format(ex))
  s = subprocess.run('sudo systemctl start hostapd', shell=True, timeout=5)
  s2 = subprocess.run('sudo systemctl start isc-dhcp-server', shell=True, timeout=5)

def dbus_wifi_if_array():
  props = dbus.Interface(_wpa_proxy, dbus_interface=DBUS_PROPERTIES)
  return props.Get(WPA_BUS_NAME, 'Interfaces')

def collect_scan_results(scan_done, iface, obj):
  global _bss_array, loop, _cb_count
  logging.debug('IN COLLECT: _bss_array: {}'.format(_bss_array))
  proxy = BUS.get_object(WPA_BUS_NAME, obj)
  props = dbus.Interface(proxy, dbus_interface=DBUS_PROPERTIES)
  _bss_array += props.Get(WPA_IF_NAME, 'BSSs')
  _cb_count -= 1
  if _cb_count == 0:
    logging.debug('Scan done, quitting the loop')
    loop.quit()

def generate_wifi_ap_dict():
  """ Loop through the scan results and retrieve the MAC and signal
  strength.  Return a dict in the format expected by MLS. """
  global _current_macs, _bss_array
  logging.debug('IN GENERATE: _bss_array: {}'.format(_bss_array))
  _current_macs.clear()
  l = []
  for bss in _bss_array:
    props = bss_props(bss)
    mac = bytes_to_mac_addr(props['BSSID'])
    l.append({ 'macAddress': mac, 'signalStrength': props['Signal'] })
    _current_macs.add(mac)
  return { 'wifiAccessPoints': l }

def bss_props(bss_object):
  proxy = BUS.get_object(WPA_BUS_NAME, bss_object)
  props = dbus.Interface(proxy, dbus_interface=DBUS_PROPERTIES)
  return props.GetAll(WPA_BSS_NAME)

def loop_killer():
  global loop
  logging.warning('Killing the Scan loop due to timeout')
  loop.quit()

def wifi_location(min_bss_count=2):
  global _cb_count, loop, _bss_array, _previous_macs, _last_location, _signals
  _bss_array = dbus.Array()
  _cb_count = 0
  try:
    wifi_scan_startup()

    # Initiate a scan on each wifi interface
    for wifi_if in dbus_wifi_if_array():
      logging.info('Scanning on interface: {}'.format(wifi_if))
      if_proxy = BUS.get_object(WPA_BUS_NAME, wifi_if)
      wpa_if = {
        'iface': dbus.Interface(if_proxy, dbus_interface=WPA_IF_NAME),
        'props': dbus.Interface(if_proxy, dbus_interface=DBUS_PROPERTIES)
      }
      wpa_if['iface'].Scan({'Type': 'active'})
      _signals.append( wpa_if['iface'].connect_to_signal('ScanDone', collect_scan_results, dbus_interface=WPA_IF_NAME, interface_keyword='iface', path_keyword='obj') )
      _cb_count += 1

    # If one or more scans are running, wait for them to finish or timeout after 10 seconds
    if _cb_count > 0:
      loop = GLib.MainLoop()
      timeout_id = GLib.timeout_add_seconds(10, loop_killer)
      loop.run()
      GLib.source_remove(timeout_id)
      for s in _signals:
        s.remove()

    d = generate_wifi_ap_dict()
    logging.debug('Scan Results: {}'.format(d))


    if len(d['wifiAccessPoints']) < min_bss_count:
      logging.warning("Minimum number of BSS stations ({}) not found: {}".format(min_bss_count, len(d)))
      wifi_scan_shutdown()
      return {}
    elif is_same_scan_data():
      logging.info("Scan data looks the same.  Skipping Submission")
      location = _last_location
    else:
      url = 'https://location.services.mozilla.com/v1/geolocate?key=test'
      r = requests.post(url, json=d)
      wifi_last_submission(True)
      if r.status_code == 200:
        location = json.loads(r.text)
        _last_location = location
        _previous_macs = _current_macs.copy()
      else:
        return {}

    return { 'Lat': location['location']['lat'], 'Lng': location['location']['lng'], 'accuracy': location['accuracy'], 'raw_response': location }
  except Exception as ex:
    logging.error('There was an error while determing our location via Wifi: {}'.format(ex))
    return {}

