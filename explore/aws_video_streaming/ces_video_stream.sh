#!/bin/bash

. ${HOME}/lib.sh

CES_STREAM_CHANNEL_ID="${CES_STREAM_CHANNEL_ID:-5987969}"

INPUT_ID="$(aws medialive describe-channel --channel-id ${CES_STREAM_CHANNEL_ID} | jq -r '.InputAttachments[0].InputId')"
SECURITY_ID="$(aws medialive describe-input --input-id ${INPUT_ID} | jq -r '.SecurityGroups[0]')"

set_capture_device() {
  for v in $(grep SPCA6500 /sys/class/video4linux/video*/name | cut -d ':' -f 1); do
    local cap_device="/dev/$(basename $(dirname $v))"
    if $(v4l2-ctl --all -d "${cap_device}" | grep -q 'Format Video Capture:'); then
      _log "Setting CES_CAPTURE_DEVICE to ${cap_device}"
      export CES_CAPTURE_DEVICE="${cap_device}"
      return 0
    fi
  done
  _warn "Unable to find the camera for streaming. Make sure it's plugged in and turned on"
  exit 1
}

ffmpeg_hw_encoding_enable() {
  ffmpeg -init_hw_device vaapi=foo:/dev/dri/renderD128
}

_ffmpeg_stream() {
  _info "Starting CES Stream..."
  # Software encoding
  #ffmpeg -re -f v4l2 -video_size 1920x1080 -framerate 30 -i "${CES_CAPTURE_DEVICE}" -vf scale=-1:720 -preset ultrafast -tune zerolatency -profile:v main -level 3.1 -pix_fmt yuv420p -c:v libx264 -x264opts "keyint=60:no-scenecut" -maxrate 2.5M -bufsize 5M -map 0 -f rtp_mpegts -fec prompeg=l=5:d=20 "$@" &
  # Hardware encoding
  ffmpeg -re -f v4l2 -video_size 1920x1080 -framerate 30 -input_format mjpeg \
          -hwaccel vaapi -hwaccel_device /dev/dri/renderD128 -hwaccel_output_format vaapi \
          -i "${CES_CAPTURE_DEVICE}" -vf 'scale_vaapi=format=nv12' \
          -c:v h264_vaapi -profile 578 -b:v 2M -maxrate 3M -bufsize 5M \
          -map 0 -f rtp_mpegts -fec prompeg=l=5:d=20 "$@" &
  local f_pid=$!
  set_event ces_live_stream $f_pid
  wait $f_pid
}

whitelist_my_ip() {
  MY_PUBLIC_IP="$(curl -s 'https://ipecho.net/plain')"
  _log "Whitelisting IP: ${MY_PUBLIC_IP}"
  aws medialive update-input-security-group --input-security-group-id ${SECURITY_ID} --whitelist-rules "Cidr=${MY_PUBLIC_IP}/32"
}

start_ces_video_stream() {
  while /bin/true; do
    whitelist_my_ip
    for URL in $(aws medialive describe-input --input-id 557022 | jq -r '.Destinations[].Url'); do
      _ffmpeg_stream "${URL}"
    done
    sleep 60
  done
}

set_capture_device
ffmpeg_hw_encoding_enable
start_ces_video_stream
