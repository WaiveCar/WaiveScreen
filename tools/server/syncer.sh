#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

CODE=$DIR/../../Linux/fai-config
GIT=$DIR/../../
LOCAL_HOME=$CODE/files/home
SRV_HOME=/srv/fai/config/files/home

if [ $# -gt 0 ]; then
  case $1 in
    pip)
      cd $DIR/../../ScreenDaemon
      mkdir -p $LOCAL_HOME/pip
      pip3 download -d $LOCAL_HOME/pip -r requirements.txt
      exit
      ;;
    loop)
      LOOP=0
  esac
fi

while [ 0 ]; do

  # This is needed to the get the git version
  cd $DIR

  newname=WaiveScreen-$(date +%Y%m%d%H%m%S)-$(git describe)

  #sudo cp -pru $CODE/* /srv/fai/config
  sudo rsync -azvr $CODE/ /srv/fai/config
  #sudo rsync -azvr $CODE/ --delete /srv/fai/config

  realname=$SRV_HOME/WaiveScreen
  if [ ! -e $SRV_HOME/WaiveScreen ]; then
    # It may be pointing nowhere
    [ -h $SRV_HOME/WaiveScreen ] && unlink $SRV_HOME/WaiveScreen
    fname=$SRV_HOME/WaiveScreen*
    if [ -n "$fname" ]; then
      realname=$fname
    else
      realname=$newname
    fi
  else    
    realname=$(readlink -f $SRV_HOME/WaiveScreen)
  fi

  sudo rsync -azvr $GIT $realname
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

  cd $SRV_HOME
  [ $realname != $newname ] && mv $realname $newname

  # not -e ... we expect this to be a broken linke now.
  [ -h WaiveScreen ] && unlink WaiveScreen
  ln -s $newname WaiveScreen

  if [ ! "$LOOP" ]; then
    exit
  fi

  inotifywait -qe close_write,attrib,modify,move,move_self,create,delete,delete_self -r $CODE
done
