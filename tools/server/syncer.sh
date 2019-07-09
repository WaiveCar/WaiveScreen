#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

CODE=$DIR/../../Linux/fai-config
GIT=$DIR/../../
LOCAL_HOME=$CODE/files/home
SRV_HOME=/srv/fai/config/files/home

if [[ $1 = pip ]]; then
  cd $DIR/../../ScreenDaemon
  mkdir -p $LOCAL_HOME/pip
  rm -f $LOCAL_HOME/pip/*
  pip3 download -d $LOCAL_HOME/pip -r requirements.txt
  exit
fi

[[ $1 = loop ]] && LOOP=0

while true; do

  # This is needed to the get the git version
  cd $DIR

  newname=WaiveScreen-$(date +%Y%m%d%H%m%S)-$(git describe)
  sudo rsync -azvr $CODE/ /srv/fai/config

  realname=$SRV_HOME/WaiveScreen
  if [ ! -e $SRV_HOME/WaiveScreen ]; then
    # It may be pointing nowhere
    [[ -h $SRV_HOME/WaiveScreen ]] && unlink $SRV_HOME/WaiveScreen
    fname=$SRV_HOME/WaiveScreen*
    [[ -n "$fname" ]] && realname=$fname || realname=$newname
  else    
    realname=$(readlink -f $SRV_HOME/WaiveScreen)
  fi

  sudo rsync -azvr $GIT $realname
  sudo chown -R root.root /srv/fai/config/scripts

  if [[ ! "$NONET" ]]; then
    ssh screen "./dcall sync_scripts" && fn=$(date +%X) || fn="!! Failure !!"
  fi
    
  echo $fn | osd_cat \
    -c white -p top -A right \
    -l 1 -o 10 -d 1 \
    -f lucidasanstypewriter-bold-14 &

  date +%s | sudo tee /tmp/last-sync

  cd $SRV_HOME
  [[ $realname != $newname ]] && mv $realname $newname

  # not -e ... we expect this to be a broken linke now.
  [ -h WaiveScreen ] && unlink WaiveScreen
  ln -s $newname WaiveScreen

  [[ "$LOOP" ]] || exit

  inotifywait -qe close_write,attrib,modify,move,move_self,create,delete,delete_self -r $CODE
done
