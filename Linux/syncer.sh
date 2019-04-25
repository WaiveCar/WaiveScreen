#!/bin/bash

# I'll have a better solution eventually
while [ 0 ]; do
  echo -n .
  sudo cp -pru fai-config/* /srv/fai/config
  sleep 10
done
