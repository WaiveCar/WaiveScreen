#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

CODE=$DIR/../Linux/fai-config

while [ 0 ]; do
  sudo cp -pru $CODE/* /srv/fai/config
  sudo chown -R root.root /srv/fai/config/scripts
  ssh screen "./dcall sync_scripts"

  date +%X | osd_cat \
      -c white \
      -p top -A right \
      -l 1 \
      -o 10 \
      -d 1 \
      -f lucidasanstypewriter-bold-14 &

  date +%s > /tmp/last-sync
  echo -n "."
  inotifywait -qe close_write,attrib,modify,move,move_self,create,delete,delete_self -r $CODE
done
