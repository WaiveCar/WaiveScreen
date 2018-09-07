#!/bin/bash

while [ 0 ]; do
	now=`date +%H`
	echo $now
	case $now in
		19)
			xrandr --output HDMI-1 --brightness 0.90
			xrandr --output HDMI-2 --brightness 0.90
			redshift -O 4500 -m vidmode
		;;
		20)
			xrandr --output HDMI-1 --brightness 0.80
			xrandr --output HDMI-2 --brightness 0.80
			redshift -O 3500 -m vidmode
		;;
		21)
			xrandr --output HDMI-1 --brightness 0.60
			xrandr --output HDMI-2 --brightness 0.60
			redshift -O 3000 -m vidmode
		;;
		22)
			xrandr --output HDMI-1 --brightness 0.40
			xrandr --output HDMI-2 --brightness 0.40
			redshift -O 2500 -m vidmode
		;;
		23)
			xrandr --output HDMI-1 --brightness 0.25
			xrandr --output HDMI-2 --brightness 0.25
			redshift -O 2300 -m vidmode
		;;
		00)
			xrandr --output HDMI-1 --brightness 0.20
			xrandr --output HDMI-2 --brightness 0.20
			redshift -O 2100 -m vidmode
		;;
		0[1-4])
			xrandr --output HDMI-1 --brightness 0.15
			xrandr --output HDMI-2 --brightness 0.15
			redshift -O 1500 -m vidmode
		;;
		05)
			xrandr --output HDMI-1 --brightness 0.3 
			xrandr --output HDMI-2 --brightness 0.3
			redshift -O 2500 -m vidmode
		;;
		06)
			xrandr --output HDMI-1 --brightness 0.5 
			xrandr --output HDMI-2 --brightness 0.5
			redshift -O 3500 -m vidmode
		;;
		07)
			xrandr --output HDMI-1 --brightness 0.9 
			xrandr --output HDMI-2 --brightness 0.9
			redshift -O 4200 -m vidmode
		;;
		*)
			xrandr --output HDMI-1 --brightness 1
			xrandr --output HDMI-2 --brightness 1
			redshift -O 10000 -m vidmode
		;;
	esac
	sleep 600
done
