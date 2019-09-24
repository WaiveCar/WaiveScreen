#!/usr/bin/python

import time
import datetime
import argparse
import netaddr
import sys
import logging
import os
import uuid
import socketserver
import json
from multiprocessing import Process, Queue
from scapy.sendrecv import sniff
from scapy.layers import dot11
from pprint import pprint

NAME = 'probemon'
DESCRIPTION = "a command line tool for logging 802.11 probe request frames"

RESPONSE_HEADER = "HTTP/1.1 200 OK\nConnection: keep-alive\nContent-Type: text/event-stream\nCache-Control: no-cache\nAccess-Control-Allow-Origin: *\n\n"

class Ssi(socketserver.BaseRequestHandler):
  def handle(self):
    req = self.request.recv(4048)
    #print(req)
    time.sleep(0.5)
    self.request.send(RESPONSE_HEADER.encode())
    time.sleep(0.5)
    while True:
      data = q.get()
      self.send_data(json.dumps(data))

  def send_data(self, msg_txt):
    data = 'data: {}'.format(msg_txt)
    msg = '{}\n\n'.format(data)
    #print('Sending: {}'.format(msg))
    self.request.send(msg.encode())


class Beacons():
  def __init__(self, max_device_age=120):
    self.devices = {}
    self.ingesting = False
    self.last_report = time.time()
    self.report_interval = 1
    self.max_device_age = max_device_age

  def ingestor(self, queue):
    self.ingesting = True
    while self.ingesting:
      try:
        packet = queue.get(True, 1)
        self.ingest_packet(packet)
      except:
        pass
      if time.time() - self.last_report > self.report_interval:
        self.prune_devices(self.max_device_age)
        device_list = self.sorted_devices(reverse=True)
        try:
          if q.full():
            q.get_nowait()
          q.put(device_list)
        except Exception as ex:
          print('Exception when adding sorted_devices to Queue: {}'.format(ex))
        self.last_report = time.time()

  def ingest_packet(self, packet):
    src_mac = packet.addr2
    if src_mac in self.devices:
      self.update_device(packet)
    else:
      rssi = packet.dBm_AntSignal
      t = time.time()
      self.devices[src_mac] = { 'first_seen': t, 'last_seen': t, 'seen_count': 1,
                                'cur_rssi': rssi, 'min_rssi': rssi, 'max_rssi': rssi,
                                'ssid': packet.info.decode(), 'mac_addr': src_mac }

  def update_device(self, packet):
    device = self.devices[packet.addr2]
    t = time.time()
    print('{} - Time between packets: {}'.format(packet.addr2, t - device['last_seen']))
    device['last_seen'] = t
    device['seen_count'] += 1
    rssi = packet.dBm_AntSignal
    device['cur_rssi'] = rssi
    device['min_rssi'] = rssi if rssi < device['min_rssi'] else device['min_rssi']
    device['max_rssi'] = rssi if rssi > device['max_rssi'] else device['max_rssi']
    device['ssid'] = packet.info.decode()

  def current_devices(self):
    return self.devices

  def sorted_devices(self, sort_field='cur_rssi', reverse=False, max_num=10):
    keys = sorted(self.devices, key=lambda x:self.devices[x][sort_field], reverse=reverse)[:max_num]
    l = []
    for k in keys:
      l.append(self.devices[k])
    print('sorted_devices: {}'.format(l))
    return l

  def prune_devices(self, max_age):
    t = time.time()
    for mac in list(self.devices):
      if t - self.devices[mac]['last_seen'] > max_age:
        print('Pruning device [{}]: {}'.format(mac, self.devices[mac]))
        del self.devices[mac]


def build_packet_callback(time_fmt, output, delimiter, mac_info, ssid, rssi, min_rssi, macs):
    def packet_callback(packet):
        if not packet.haslayer(dot11.Dot11):
            return

        # we are looking for management frames with a probe subtype
        # if neither match we are done here
        if packet.type != 0 or packet.subtype != 0x04:
            return
        elif len(macs) > 0 and packet.addr2 not in macs:
          return
        elif packet.dBm_AntSignal < min_rssi:
          return

        # list of output fields
        fields = []

        #print(packet.summary())
        #print(packet.show())
        #print(dir(packet))

        # determine preferred time format 
        if time_fmt == 'iso':
            log_time = datetime.datetime.now().isoformat()
        else:
            log_time = datetime.datetime.utcnow().strftime("%s")

        fields.append(log_time)

        # append the mac address itself
        fields.append(packet.addr2)

        # include the SSID in the probe frame
        if ssid:
            fields.append('{}'.format(packet.info))
                
        if rssi:
            #rssi_val = -(256-ord(packet.notdecoded[-4:-3]))
            #fields.append(str(rssi_val))
            fields.append('{}dBm'.format(packet.dBm_AntSignal))

        #q.put(delimiter.join(fields))
        packet_q.put(packet)

    return packet_callback

def writer(q, fname):
    while True:
        line = q.get()
        # This is to avoid file corruption on reboot
        fd = os.open(fname, os.O_WRONLY | os.O_APPEND | os.O_SYNC | os.O_CREAT)
        os.write(fd, line.encode() + b'\n')
        os.close(fd)

def ssi_listener():
	with socketserver.TCPServer(('0.0.0.0', 9998), Ssi) as server:
		server.serve_forever()

def sniff_wrap(iface, prn, store):
    while True:
        try:
            sniff(iface=iface, prn=prn, store=store)
        except Exception as ex:
            print(ex, iface)
            if ex.errno == 100:
                os.system("/sbin/iwconfig %s mode monitor" % iface)
                os.system("/sbin/ifconfig %s up" % iface)
            time.sleep(0.1)
            pass
def kill(p):
  p.terminate()
  p.join()

def main():
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument('-i', '--interface', help="capture interface")
    parser.add_argument('-t', '--time', default='iso', help="output time format (unix, iso)")
    parser.add_argument('-o', '--output', default='probemon.log', help="logging output location")
    parser.add_argument('-d', '--delimiter', default='\t', help="output field delimiter")
    parser.add_argument('-f', '--mac-info', action='store_true', help="include MAC address manufacturer")
    parser.add_argument('-s', '--ssid', action='store_true', help="include probe SSID in output")
    parser.add_argument('-r', '--rssi', action='store_true', help="include rssi in output")
    parser.add_argument('-m', '--macs', default='', help="only look for these MAC addresses (space separated)")
    parser.add_argument('-R', '--min-rssi', default=-200, type=int, help="filter out low rssi values (ex: -60)")
    args = parser.parse_args()

    if not args.interface:
        print("error: capture interface not given, try --help")
        sys.exit(-1)
    
    if len(args.macs) == 0:
      beacons = Beacons()
      mac_list = []
    else:
      beacons = Beacons(30)
      mac_list = args.macs.split(' ')

    built_packet_cb = build_packet_callback(args.time, args.output, 
        args.delimiter, args.mac_info, args.ssid, args.rssi, args.min_rssi, mac_list)


    # Start the sniffer and hb writer
    #Process(target = writer, args=(q,args.output)).start()
    Process(target = ssi_listener, args=()).start()
    Process(target = beacons.ingestor, args=(packet_q,)).start()
    sniff_p = Process(target = sniff_wrap, args=(args.interface, built_packet_cb, 0))
    sniff_p.start()
    sniff_p.join()


if __name__ == '__main__':
    q = Queue(1)
    packet_q = Queue()
    main()
