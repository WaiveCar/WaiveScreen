resize() {
  eval $(xrandr -q | grep \ connected | awk ' { print "SC"NR"="$1 } ')
  xrandr --newmode "1920x675_60.00"  104.25  1920 2008 2200 2480  675 678 688 702 -hsync +vsync
  xrandr --addmode $SC1 "1920x675_60.00"
  xrandr --addmode $SC2 "1920x675_60.00"
  xrandr --output $SC1 --mode "1920x675_60.00"
  xrandr --output $SC2 --mode "1920x675_60.00"
  xrandr --output $SC1 --same-as $SC2
}

onebigscreen() {
  xrandr --output HDMI-2 --above HDMI-1
  xrandr --output HDMI-2 --reflect xy
}

resize

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
