#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

mkdir -p $DIR/../../ScreenDaemon/build

arduino --pref build.path=$DIR/../../ScreenDaemon/build --verify $DIR/../../ScreenDaemon/sensors/sensors.ino

