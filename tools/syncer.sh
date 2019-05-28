#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

CODE=$DIR/../Linux/fai-config

while [ 0 ]; do
  #sudo cp -pru $CODE/* /srv/fai/config
  sudo rsync -azvr $CODE/ /srv/fai/config
  sudo rsync -azvr $CODE/ --delete /srv/fai/config
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
  inotifywait -qe close_write,attrib,modify,move,move_self,create,delete,delete_self -r $CODE
done
