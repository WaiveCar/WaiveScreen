#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
scp -C waivescreen.com:/var/www/WaiveScreen/db/main.db /tmp
sudo mv /tmp/main.db $DIR/../db/main.db
sudo chown www-data.www-data $DIR/../db/main.db

