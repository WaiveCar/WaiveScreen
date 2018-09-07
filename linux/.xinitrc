xrandr --newmode "1920x675_60.00"  104.25  1920 2008 2200 2480  675 678 688 702 -hsync +vsync
xrandr --addmode HDMI-1 "1920x675_60.00"
xrandr --addmode HDMI-2 "1920x675_60.00"
xrandr --output HDMI-1 --mode "1920x675_60.00"
xrandr --output HDMI-2 --mode "1920x675_60.00"

xrandr --output HDMI-2 --same-as HDMI-1
#xrandr --output HDMI-2 --reflect xy
xhost +
sudo -u chris twm&
unclutter -idle 1 -root &
/root/screen-dimmer.sh&
/root/slideshow.sh &
/root/network-setup.sh > /root/last-log
sleep 1000000
