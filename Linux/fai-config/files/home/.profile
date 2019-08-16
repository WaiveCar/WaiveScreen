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
