This things uses FAI and will eventually be on a USB stick. The fai-config is where the screen install magic lives.

You'll need to manually copy 
  * ModemManager/data/org.freedesktop.ModemManager1.conf to /etc/dbus-1/system.d/org.freedesktop.ModemManager1.conf manually
  * ModemManager/data/org.freedesktop.ModemManager1.service to /etc/systemd/system/dbus-org.freedesktop.ModemManager1.service


Here's the SystemD layout


```
-rw-r--r-- 1 root root 416 Sep 14 17:01 ./system/ModemManager.service
lrwxrwxrwx 1 root root  40 Sep 14 17:05 ./system/multi-user.target.wants/ModemManager1.service -> /lib/systemd/system/ModemManager.service
lrwxrwxrwx 1 root root  40 Sep 14 17:07 ./system/multi-user.target.wants/ModemManager.service -> /etc/systemd/system/ModemManager.service
lrwxrwxrwx 1 root root  40 Sep 14 17:07 ./system/dbus-org.freedesktop.ModemManager1.service -> /etc/systemd/system/ModemManager.service
```
