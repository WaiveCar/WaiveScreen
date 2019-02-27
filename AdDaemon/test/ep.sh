#!/bin/bash

cmd=$1
verb=$2
host=screen
action=

if [ "$cmd" == "campaign" ]; then
  if [ "$verb" == "create" ]; then
    POST="duration=90&asset=test.jpg&lat=-118&lng=90&start_time=2019-02-18T08:44:59-08:00&end_time=2019-02-28T08:44:59-08:00"
    action="Creating campaigns"
  else
    action="Showing campaigns"
  fi
else
  echo Try one of the following arguments
  echo
  echo campaign - create a new campaign
  echo sow - declare a statement of work
  echo reset - reset the data and play again
  echo
  exit
fi

# Push this stuff to stderr so that a json parser can be run over stdout
echo $action >& 2

[ -n "$POST" ] && \
  curl http://$host/$cmd --data "$POST" || \
  curl http://$host/$cmd 

