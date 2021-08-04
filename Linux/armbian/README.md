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

Before building the image, we add a kernel patch that allows us to set a custom output resolution.  From this repo, copy the file `userpatches/hdmi-allow_all_modes.patch` to `userpatches/kernel/rockchip64-current/` on the build system.

Builds are made with the following command (as a user with sudo privileges):

`./compile.sh  BOARD=nanopim4v2 BRANCH=current RELEASE=buster BUILD_MINIMAL=yes BUILD_DESKTOP=no KERNEL_ONLY=no KERNEL_CONFIGURE=no BUILD_KSRC=yes INSTALL_KSRC=yes`

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

---

### Miscellaneous Notes

## Recompiling kernel modules:

Steps taken from [this blog post](http://blog.vmsplice.net/2018/01/how-to-modify-kernel-modules-without.html).

If you built your image with the BUILD_KSRC and INSTALL_KSRC options above, you will have the tarred up sources in /usr/src/ on your image.  Make an appropriate directory and untar the source files.

```
cd /usr/src
mkdir 5.4.41-rockchip64
cd 5.4.41-rockchip64
tar xvf ../linux-source-5.4.41-rockchip64.tar.xz
```

Make the changes you want to the source of the module you're working on (for example drivers/gpu/drm).  Then compile the module.

```
cd /usr/src/5.4.41-rockchip64
make oldconfig
sed -i 's/^CONFIG_LOCALVERSION=.*$/CONFIG_LOCALVERSION="-rockchip64"/' .config
make modules_prepare
make -j4 M=drivers/gpu/drm modules
```

## Serial Console (U-Boot access and troubleshooting)

Accessible through the DBG_UART pins on the carrier board.  The baud rate is a very strange 1500000.  Not all USB to TTL adapters support such a high rate, so you may need to check the specs for your adapter's chip if you have trouble.  You can use the following command to connect:

`minicom -D /dev/ttyUSB0 -b 1500000`

The system will start booting from the sdcard if present, then the emmc.  You can interrupt U-Boot for a brief second to access the boot prompt.  When you see the beginning of the following section, repeatedly press the space bar to stop the boot process.

```
U-Boot 2020.04-armbian (Jun 02 2020 - 00:24:52 -0700)

Model: FriendlyElec NanoPi M4V2
DRAM:  2 GiB
PMIC:  RK808
MMC:   dwmmc@fe320000: 1, sdhci@fe330000: 0
Loading Environment from MMC... *** Warning - bad CRC, using default environment

In:    serial
Out:   vidconsole
Err:   vidconsole
Model: FriendlyElec NanoPi M4V2
Net:   eth0: ethernet@fe300000
Hit any key to stop autoboot:
```

From the prompt, you can change the boot device (among other things):

```
=> mmc list
dwmmc@fe320000: 1
sdhci@fe330000: 0 (eMMC)
=> setenv devnum 0
=> run mmc_boot
```