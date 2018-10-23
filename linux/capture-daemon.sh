pkill -9 ffmpeg
duration=300
now=`date +%Y%m%d%H%M%S`
while [ 0 ] ; do
	for i in `seq 0 2 8`; do
		ffmpeg -loglevel panic -nostats -hide_banner -f v4l2 -video_size 640x480 -y -i /dev/video$i -an -t $duration -c:v libx264 -preset ultrafast -crf 31 camera-$now-$i.mkv&
	#	ffmpeg -f v4l2 -input_format mjpeg -framerate 15 -video_size 640x480 -y -i /dev/video$i -an -t 600 -c:v libvpx-vp9  -cpu-used 8  -deadline realtime -crf 33  output$i.webm&
	done
	sleep $(( duration - 4 ))
done
