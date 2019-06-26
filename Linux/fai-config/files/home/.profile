# If not running interactively, don't do anything
case $- in
    *i*) ;;
      *) return;;
esac

shopt -s histappend
HISTSIZE=1000
HISTFILESIZE=2000
shopt -s checkwinsize
PS1='\u@\h:\w\$ '

gousb() {
  for i in /sys/bus/usb/devices/*; do
    if [ -e $i/idProduct ]; then
      if [ $(cat $i/idVendor):$(cat $i/idProduct) = $1 ]; then
        cd $i
        return
      fi
    fi
  done
  echo "$1 not found :-("
}

alias pycall=$HOME/WaiveScreen/ScreenDaemon/dcall
PATH=$PATH:$HOME/.local/bin:$HOME:$HOME/WaiveScreen/
source $HOME/const.sh
