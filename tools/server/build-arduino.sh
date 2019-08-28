#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BuildDir=$DIR/../../ScreenDaemon/build
[[ -e $BuildDir ]] && sudo rm -fr $BuildDir
mkdir -p $BuildDir

arduino --pref build.path=$BuildDir --verify $DIR/../../ScreenDaemon/sensors/sensors.ino
cp -puv $BuildDir/sensors.ino.hex $DIR/../client

