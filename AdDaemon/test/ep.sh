#!/bin/bash

cmd=$1
host=screen

if [ "$cmd" == "campaign" ]; then
  POST="duration=90&asset=test.jpg&lat=-118&lng=90&start_time=2019-02-18T08:44:59-08:00&end_time=2019-02-28T08:44:59-08:00"
else
  echo Try one of the following arguments
  echo
  echo campaign - create a new campaign
  echo sow - declare a statement of work
  echo reset - reset the data and play again
  echo
  exit
fi

curl --data "$POST" http://$host/$cmd
