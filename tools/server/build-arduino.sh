#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BASE=$DIR/../../ScreenDaemon/
SRC=$BASE/sensors
MIDDLE=$BASE/middle
BUILD=$BASE/build

for i in $MIDDLE $BUILD; do
  [[ -e $i ]] && sudo rm -fr $i
  mkdir -p $i
done

# This is a pre-processor step where we inject things into the code base ... in this case
# our version
version=$(git log -1 --date=short --pretty=format:%ad | sed 's/-//g')
sed "s/__VERSION__/$version/g" $SRC/sensors.ino > $MIDDLE/sensors.ino
arduino --pref build.path=$BUILD --verify $MIDDLE/sensors.ino
cp -puv $BUILD/sensors.ino.hex $DIR/../client

