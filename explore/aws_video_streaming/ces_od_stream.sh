#!/bin/bash

. ${HOME}/lib.sh

WATERMARK="${BASE}/explore/aws_video_streaming/watermark.png"

_ffmpeg_stream() {
  _log "Starting CES On Demand Stream..."
  # Hardware encoding
  ffmpeg -re -f v4l2 -video_size 1920x1080 -framerate 30 -input_format mjpeg \
          -vaapi_device /dev/dri/renderD128 \
          -i "${1}" -i "${WATERMARK}" \
          -filter_complex "overlay=x=(main_w-overlay_w):y=(main_h-overlay_h)[comp];[comp]format=nv12[nv];[nv]hwmap" \
          -c:v h264_vaapi -profile 578 -b:v 2M -maxrate 3M -bufsize 5M \
          -map 0 -f rtp_mpegts -fec prompeg=l=5:d=20 "${2}" &
  local f_pid=$!
  set_event ces_od_stream $f_pid
  wait $f_pid
}

_ffmpeg_stream "${1}" "${2}"
