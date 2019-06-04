resize() {
  xrandr --newmode "1920x675_60.00"  104.25  1920 2008 2200 2480  675 678 688 702 -hsync +vsync
  xrandr --addmode HDMI-1 "1920x675_60.00"
  xrandr --addmode HDMI-2 "1920x675_60.00"
  xrandr --output HDMI-1 --mode "1920x675_60.00"
  xrandr --output HDMI-2 --mode "1920x675_60.00"

  xrandr --output HDMI-1 --same-as HDMI-2
}

onebigscreen() {
  xrandr --output HDMI-2 --above HDMI-1
  xrandr --output HDMI-2 --reflect xy
}

if [ $( xrandr | grep \ connected | wc -l) -ne 1 ]; then
  resize
fi

WHO=adorno

xhost +

# Prevent the screen from turning off
xset dpms 0 0 0
xset -dpms
xset s off
xset dpms force on

# Hide the mouse cursor
unclutter -idle 1 -root &

su -c "/home/$WHO/start-x-stuff.sh $DISPLAY $$" - $WHO

sleep 10000000
