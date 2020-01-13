#!/bin/bash

. ${HOME}/lib.sh

stream_health_good() {
	local netout="$(stream_netout | jq '.MetricDataResults[0].Values[0] // 0' | cut -d '.' -f 1 )"
  echo "CES Stream NetworkOut: $netout"
  if (( $netout > 2000000 )); then
    return 0
  else
    return 1
  fi
}

stream_netout() {
	aws cloudwatch get-metric-data --metric-data-queries='[
        {
            "Id": "myRequest",
            "MetricStat": {
                "Metric": {
                    "Namespace": "MediaLive",
                    "MetricName": "NetworkOut",
                    "Dimensions": [
                        {
                            "Name": "ChannelId",
                            "Value": "822933"
                        },
                        {
                            "Name": "Pipeline",
                            "Value": "0"
                        }
                    ]
                },
                "Period": 30,
                "Stat": "Average"
            },
            "Label": "myRequestLabel",
            "ReturnData": true
        }
    ]' --start-time="$(date -Is -u -d '-60sec')" --end-time="$(date -Is -u -d '-30sec')"
}

monitor_stream() {
  local problem_count=0

  while sleep 10; do
    if stream_health_good; then
      problem_count=0
    else
      (( ++problem_count ))
      echo "Looks like trouble"
      if (( $problem_count > 2 )); then
        _log "CES stream looks down.  Restarting it."
        #ces_live_stream
        sleep 60
        problem_count=0
      fi
    fi
  done
}


monitor_stream
