#!/bin/bash

get_db() {
  compress=/tmp/backup.sql.bz2
  sql=/tmp/backup.sql
  db=/var/db/waivescreen/main.db
  ssh waivescreen.com "sqlite3 $db .dump | bzip2 -c > $compress"
  rm -f $compress $db $sql
  scp -C waivescreen.com:$compress $compress
  bunzip2 -d $compress 
  sudo sqlite3 $db < $sql
  sudo chown www-data.www-data $db
}

db_stage() {
  set -x
  db=/var/db/waivescreen/main.db
  ssh waivescreen.com "sqlite3 $db .dump > /tmp/sql"
  scp waivescreen.com:/tmp/sql staging.waivescreen.com:/tmp/sql
  ssh staging.waivescreen.com "sudo rm $db; sudo sqlite3 $db < /tmp/sql; sudo chown www-data.www-data $db"
}

if ! declare -f $1 > /dev/null; then
  echo "Woops, $1 is not defined"
  declare -F | sed s/'declare -f//g' | sort
  exit 1
fi

eval $*