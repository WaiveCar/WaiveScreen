## Armbian Platform

We are currently targeting the [FriendlyArm SOM-RK3399v2 Dev Kit](https://www.friendlyarm.com/index.php?route=product/product&product_id=281).  It consists of a [System on Module](http://wiki.friendlyarm.com/wiki/index.php/SOM-RK3399v2) and a [Carrier Board](http://wiki.friendlyarm.com/wiki/index.php/SOM-RK3399_Dev_Kit).  The SoC is a [Rockchip RK3399](http://opensource.rock-chips.com/wiki_Main_Page).

[Armbian](https://www.armbian.com/) does not (yet?) target this specific board, but I have had success using images built for the NanoPi-M4v2.

### Armbian Image Build Process:

Details on the build process can be found in the [Armbian Documentation](https://docs.armbian.com/Developer-Guide_Build-Preparation/).

I have been using an Ubuntu Bionic 18.04 x64 VM to build the images.

Check out the armbian build tools repo from Github:

```
git clone --depth 1 https://github.com/armbian/build
cd build
```

Builds are made with the following command (as a user with sudo privileges):

`./compile.sh  BOARD=nanopim4v2 BRANCH=current RELEASE=buster BUILD_MINIMAL=yes BUILD_DESKTOP=no KERNEL_ONLY=no KERNEL_CONFIGURE=yes BUILD_KSRC=yes INSTALL_KSRC=yes`

In the kernel configuration menu, we add the modules:

* Device Drivers -> Industrial I/O Support -> Accelerometers -> STMicroelectronics accelerometers 3-Axis Driver
* Device Drivers -> Industrial I/O Support -> Humidity sensors -> DHT11 (and compatible sensors) driver

The resutling image can be found in `output/images/`.

### WaiveScreen Image Preparation:

The next step is to take the Armbian image and prepare it for WaiveScreen to be installed on it.  This is done with the script `WaiveScreen/tools/server/prepare_armbian_image.sh`.

I will typically copy the Armbian image to `/tmp/` and run the following command:

`./prepare_armbian_image.sh /tmp/Armbian_20.05.0-trunk_Nanopim4v2_buster_current_5.4.25_minimal.img /dev/mmcblk0`

This will prepare the image and write it to the SD card.

### WaiveScreen Installation:

The next step is to put the SD card from the last step into the SOM-RK3399v2 and boot it up.  Make sure the board has an ethernet connection.

On boot, it will begin the install process, running the `WaiveScreen/Linux/armbian/waivescreen-install.sh` script.  This will install WaiveScreen and perform an FAI softupdate to install the needed software and configure the system.

Upon completion, the system will shutdown.

The SD card is now ready for copying and distribution onto new systems.
