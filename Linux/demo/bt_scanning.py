import time
import multiprocessing
from scapy.layers.bluetooth import *
from scapy.layers import bluetooth4LE, bluetooth

#  First we need to initialize the usb module with: sudo hciconfig hci1 up
d = {}
q = multiprocessing.Queue()

def bt_packet_handler(packet):
  global d
  p = packet[3][1]
  #bt_packet_q.put(p)
  print('{} @ {}dBi - {} {}'.format(p.addr, p.rssi, p.type, p.atype))
  q.put(p)

def q_consumer(queue):
  while not queue.empty():
    p = queue.get()
    if p.addr in d:
      d[p.addr] += 1
    else:
      d[p.addr] = 1

bt = BluetoothHCISocket(0)

while True:
  bt.sr(HCI_Hdr() / HCI_Command_Hdr() / HCI_Cmd_LE_Set_Scan_Parameters(type=1))
  bt.sr(HCI_Hdr() / HCI_Command_Hdr() / HCI_Cmd_LE_Set_Scan_Enable(enable=True, filter_dups=False))
  bt.sniff(lfilter=lambda p: HCI_LE_Meta_Advertising_Reports in p, prn=bt_packet_handler, timeout=5)
  bt.sr(HCI_Hdr() / HCI_Command_Hdr() / HCI_Cmd_LE_Set_Scan_Enable(enable=False))
  time.sleep(2)


