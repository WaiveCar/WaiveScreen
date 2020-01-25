#!/bin/bash

DB=/var/db/waivescreen/main.db

get_db() {
  compress=/tmp/backup.sql.bz2
  sql=/tmp/backup.sql
  ssh waivescreen.com "sqlite3 $DB .dump | bzip2 -c > $compress"
  rm -f $compress $DB $sql
  scp -C waivescreen.com:$compress $compress
  bunzip2 -d $compress 
  sudo sqlite3 $DB < $sql
  sudo chown www-data.www-data $DB
}

db_stage() {
  set -x
  ssh waivescreen.com "sqlite3 $DB .dump > /tmp/sql"
  scp waivescreen.com:/tmp/sql staging.waivescreen.com:/tmp/sql
  ssh staging.waivescreen.com "sudo rm $DB; sudo sqlite3 $DB < /tmp/sql; sudo chown www-data.www-data $DB"
}

if ! declare -f $1 > /dev/null; then
  echo "Woops, $1 is not defined"
  declare -F | sed s/'declare -f//g' | sort
  exit 1
fi

eval $*
