#!/bin/bash
cd $HOME/content
while [ 0 ]; do
  mplayer -fs *.mp4&
  sleep 29
  for i in *.jpg; do
    display -window root $i
    sleep 10
  done
done
