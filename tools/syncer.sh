#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

CODE=$DIR/../Linux/fai-config
GIT=$DIR/../
LOCAL_HOME=$CODE/files/home
SRV_HOME=/srv/fai/config/files/home

if [ $# -gt 0 ]; then
  case $1 in
    pip)
      cd $DIR/../ScreenDaemon
      mkdir -p $LOCAL_HOME/pip
      pip3 download -d $LOCAL_HOME/pip -r requirements.txt
      exit
      ;;
    loop)
      LOOP=0
  esac
fi

while [ 0 ]; do

  #sudo cp -pru $CODE/* /srv/fai/config
  sudo rsync -azvr $CODE/ /srv/fai/config
  #sudo rsync -azvr $CODE/ --delete /srv/fai/config

  [ -e $SRV_HOME/WaiveScreen ] || mkdir -p $SRV_HOME/WaiveScreen
  sudo rsync -azvr $GIT $SRV_HOME/WaiveScreen
  sudo chown -R root.root /srv/fai/config/scripts

  if [ ! "$NONET" ]; then
    if ssh screen "./dcall sync_scripts"; then
      fn=$(date +%X)
    else
      fn="!! Failure !!"
    fi
  fi
    
  echo $fn| osd_cat \
      -c white \
      -p top -A right \
      -l 1 \
      -o 10 \
      -d 1 \
      -f lucidasanstypewriter-bold-14 &

  date +%s > /tmp/last-sync

  if [ ! "$LOOP" ]; then
    exit
  fi

  inotifywait -qe close_write,attrib,modify,move,move_self,create,delete,delete_self -r $CODE
done
