# If not running interactively, don't do anything
case $- in
    *i*) ;;
      *) return;;
esac

shopt -s histappend
HISTSIZE=1000
HISTFILESIZE=2000
HISTTIMEFORMAT="%F%T"
shopt -s checkwinsize
PS1='\u@\h:\w\$ '

alias pycall=$HOME/WaiveScreen/ScreenDaemon/dcall
PATH=$PATH:$HOME/.local/bin:$HOME:$HOME/WaiveScreen/
source $HOME/const.sh

display_two() {
  eval $(xrandr -q | grep \ connected | tail -2 | awk ' { print "SC"NR"="$1 } ')
  xrandr --newmode "1920x675_60.00"  104.25  1920 2008 2200 2480  675 678 688 702 -hsync +vsync
  xrandr --addmode $SC1 "1920x675_60.00"
  xrandr --addmode $SC2 "1920x675_60.00"
  xrandr --output $SC1 --mode "1920x675_60.00"
  xrandr --output $SC2 --mode "1920x675_60.00"
  xrandr --output $SC1 --same-as $SC2
  pkill notion; notion&
}

display_one() {
  xrandr --output HDMI-2 --above HDMI-1
  xrandr --output HDMI-2 --reflect xy
  pkill notion; notion&
}

