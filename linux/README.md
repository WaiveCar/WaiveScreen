
 * 45-arduino.rules - udev rules, go in /etc/udev/rules.d
 * screen.log - logrotate rules, go in /etc/logrotate.d
 * dot_ssh - ssh key and config rules to connect to the screen server

You'll need to manually copy 
  * ModemManager/data/org.freedesktop.ModemManager1.conf to /etc/dbus-1/system.d/org.freedesktop.ModemManager1.conf manually
  * ModemManager/data/org.freedesktop.ModemManager1.service to /etc/systemd/system/dbus-org.freedesktop.ModemManager1.service
