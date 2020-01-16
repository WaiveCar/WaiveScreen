#!/bin/bash

. ${HOME}/lib.sh

WATERMARK="${BASE}/explore/aws_video_streaming/watermark.png"

CES_STREAM_CHANNEL_ID="$(aws medialive list-channels | jq -r '.Channels[] | select(.Tags | has("ces_booth_stream")).Id')"
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
  return 1
}

ffmpeg_hw_encoding_enable() {
  ffmpeg -init_hw_device vaapi=foo:/dev/dri/renderD128
}

_ffmpeg_stream() {
  _info "Starting CES Stream..."
  # Hardware encoding
  ffmpeg -re -f v4l2 -video_size 1920x1080 -framerate 30 -input_format mjpeg \
          -vaapi_device /dev/dri/renderD128 \
          -i "${CES_CAPTURE_DEVICE}" -i "${WATERMARK}" \
          -filter_complex "overlay=x=(main_w-overlay_w):y=(main_h-overlay_h)[comp];[comp]format=nv12[nv];[nv]hwmap" \
          -c:v h264_vaapi -profile 578 -b:v 2M -maxrate 3M -bufsize 5M \
          -map 0 -f rtp_mpegts -fec prompeg=l=5:d=20 "$@" &
  local f_pid=$!
  set_event ces_live_stream $f_pid
  wait $f_pid
}

whitelist_my_ip() {
  export CES_STREAM_CHANNEL_ID="$(aws medialive list-channels | jq -r '.Channels[] | select(.Tags | has("ces_booth_stream")).Id')"
  export INPUT_ID="$(aws medialive describe-channel --channel-id ${CES_STREAM_CHANNEL_ID} | jq -r '.InputAttachments[0].InputId')"
  export SECURITY_ID="$(aws medialive describe-input --input-id ${INPUT_ID} | jq -r '.SecurityGroups[0]')"
  MY_PUBLIC_IP="$(curl -s 'https://ipecho.net/plain')"
  _log "Whitelisting IP: ${MY_PUBLIC_IP}"
  #aws medialive update-input-security-group --input-security-group-id ${SECURITY_ID} --whitelist-rules "Cidr=${MY_PUBLIC_IP}/32"
  aws medialive update-input-security-group --input-security-group-id ${SECURITY_ID} --whitelist-rules "Cidr=${MY_PUBLIC_IP}/24"
}

start_ces_video_stream() {
  while /bin/true; do
    if set_capture_device; then
      whitelist_my_ip
      for URL in $(aws medialive describe-input --input-id 557022 | jq -r '.Destinations[0].Url'); do
        _ffmpeg_stream "${URL}"
      done
    else
      sleep 25
    fi
    sleep 5
  done
}

ffmpeg_hw_encoding_enable
start_ces_video_stream
