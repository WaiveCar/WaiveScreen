#!/bin/bash
set -x
compress=/tmp/backup.sql.bz2
sql=/tmp/backup.sql
db=/var/db/waivescreen/main.db
ssh waivescreen.com "sqlite3 $db .dump | bzip2 -c > $compress"
rm -f $compress $db $sql
scp -C waivescreen.com:$compress $compress
bunzip2 -d $compress 
sudo sqlite3 $db < $sql
sudo chown www-data.www-data $db
sudo chomod 0666 $db
rm $compress $sql
