xrandr --newmode "1920x675_60.00"  104.25  1920 2008 2200 2480  675 678 688 702 -hsync +vsync
xrandr --addmode HDMI-1 "1920x675_60.00"
xrandr --addmode HDMI-2 "1920x675_60.00"
xrandr --output HDMI-1 --mode "1920x675_60.00"
xrandr --output HDMI-2 --mode "1920x675_60.00"

#xrandr --output HDMI-2 --above HDMI-1
#xrandr --output HDMI-2 --reflect xy
xhost +
su -c "DISPLAY=:0 xterm" - demo 
su -c "DISPLAY=:0 chromium --app=file:///home/demo/WaiveScreen/ScreenDisplay/display.html"
xset dpms 0 0 0
unclutter -idle 1 -root  &
redshift&
#sudo -u chris notion&
sleep 10000000
