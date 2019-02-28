#!/bin/bash

cmd=$1
verb=$2
host=screen
action=

if [ "$cmd" == "campaign" ]; then
  if [ "$verb" == "create" ]; then
    now=`date +%s`

    # 60 day
    past=`date -d @$(( now - 60 * 24 * 60 * 60 )) -Iminutes`
    future=`date -d @$(( now + 60 * 24 * 60 * 60 )) -Iminutes`

    POST="duration=90&asset=test.jpg&lat=-118&lng=90&start_time=$past&end_time=$future"
    action="Creating campaigns"
  else
    action="Showing campaigns"
  fi
elif [ "$cmd" == "reset" ]; then
  action="Resetting data"
elif [ "$cmd" == "sow" ]; then
  id=`uuidgen`
  POST="uid=$id&lat=-118&lng=90"
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

