resize() {
  if [ $# -ne 12 ]; then
    echo "resize: Unspecified mode"
    return 3
  else
    newmode="$*"
    modename="$1"
  fi
  eval $(xrandr -q | grep \ connected | tail -2 | awk ' { print "SC"NR"="$1 } ')
  xrandr --newmode $newmode
  xrandr --addmode $SC1 "$modename"
  xrandr --addmode $SC2 "$modename"
  xrandr --output $SC1 --mode "$modename"
  xrandr --output $SC2 --mode "$modename"
  xrandr --output $SC1 --same-as $SC2
}

onebigscreen() {
  xrandr --output HDMI-2 --above HDMI-1
  xrandr --output HDMI-2 --reflect xy
}

#if [ $(uname -m) = "aarch64" ]; then
#  resize 1920x538_59.00  79.92  1920 1984 2176 2432  538 539 542 557  -HSync +Vsync
#else
#  resize 1920x675_60.00  104.25  1920 2008 2200 2480  675 678 688 702 -hsync +vsync
#fi

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
