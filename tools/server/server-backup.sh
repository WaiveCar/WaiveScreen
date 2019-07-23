#!/bin/bash

dir=/var/backup
backupfile=db-$(date +%Y%m%d).gz
db=/var/db/waivescreen/main.db
[ -e $dir ] || mkdir -p $dir
sqlite3 $db .dump | gzip -c > $dir/$backupfile
scp -P 5001 -i /root/backupKey -o StrictHostKeyChecking=accept-new $dir/$backupfile x0MfDySLQXmtuC6W9hA1xg@9ol.es:/raid/backup/waivescreen/
find $dir -ctime +7 -name \*.gz -exec rm -f {} \;
