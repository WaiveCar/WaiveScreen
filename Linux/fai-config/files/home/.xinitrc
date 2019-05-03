xrandr --newmode "1920x675_60.00"  104.25  1920 2008 2200 2480  675 678 688 702 -hsync +vsync
xrandr --addmode HDMI-1 "1920x675_60.00"
xrandr --addmode HDMI-2 "1920x675_60.00"
xrandr --output HDMI-1 --mode "1920x675_60.00"
xrandr --output HDMI-2 --mode "1920x675_60.00"

#xrandr --output HDMI-2 --above HDMI-1
#xrandr --output HDMI-2 --reflect xy

xhost +
xset dpms 0 0 0
unclutter -idle 1 -root &
redshift & 
# I REALLY FUCKING WISH THIS WOULD WORK IN THE RC.LOCAL BUT
# IT DOES NOT ... AUGHHHHGHGHGH
/home/demo/manual-set-ipv4.sh > /tmp/output &
su -c "/home/demo/start-x-stuff.sh $DISPLAY" - demo 

sleep 10000000
