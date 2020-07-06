## Raspberry Pi Platform

We are currently targeting the [Raspberry Pi 4B](https://www.raspberrypi.org/products/raspberry-pi-4-model-b/specifications/).

[Raspberry Pi OS (64-bit)](https://www.raspberrypi.org/forums/viewtopic.php?t=275370) is currently in Beta, but is slated to be the supported OS going forward.  The Beta image is a full Desktop installation, but in the future we will be using the Minimal image.

### WaiveScreen Image Preparation:

After downloading the OS image, the next step is prepare it for WaiveScreen to be installed on it.  This is done with the script `WaiveScreen/tools/server/prepare_rpi_image.sh`.

I will typically copy the Pi OS image to `/tmp/` and run the following command:

`./prepare_rpi_image.sh /tmp/2020-05-27-raspios-buster-arm64.img /dev/mmcblk0`

This will prepare the image and write it to the SD card.

### WaiveScreen Installation:

The next step is to put the SD card from the last step into the Raspberry Pi 4B and boot it up.  Make sure the board has an ethernet connection.

On boot, it will begin the install process, running the `WaiveScreen/Linux/rpi/waivescreen-install.sh` script.  This will install WaiveScreen and perform an FAI softupdate to install the needed software and configure the system.

Upon completion, the system will shutdown.

The SD card is now ready for copying and distribution onto new systems.

<!--
---

### Miscellaneous Notes

-->
