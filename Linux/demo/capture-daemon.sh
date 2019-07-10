#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VID=/tmp/
mkdir -p $VID

pkill -9 ffmpeg
duration=600
while [ 0 ] ; do
  echo -e $$ > /tmp/capture.pid
  now=`date +%Y%m%d%H%M%S`
  for i in `seq 0 2 8`; do
    fname=$VID/camera-$now-$i.mkv

    ffmpeg -loglevel panic -nostats -hide_banner -f v4l2 -video_size 640x480 -y -i /dev/video$i -an -t $duration -c:v libx264 -preset ultrafast -crf 31 $fname&
  done
  sleep $(( duration + 1 ))
done
