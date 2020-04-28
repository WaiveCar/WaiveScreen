#!/usr/bin/env bash

# This is meant to be run on a fresh Armbian image, prepared by
# tools/server/prepare_armbian_image.sh
#
# We run fai softupdate to install the WaiveScreen system and then prepare
# the installed image for cloning.

set -x
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
TMP_DIR="$(mktemp -d)"
BRANCH="armbian-port"

# sudo doesn't work with an expired password
chage -d 18330 root

# Wait for NTP time sync
chronyc waitsync

# Update the system and install some needed software packages
apt update && apt full-upgrade -y
apt update && apt install -y rsync fai-client git gpg sudo patch python3-pip python3-setuptools python3-dev python3-wheel

cd "${TMP_DIR}"
git clone git@github.com:WaiveCar/WaiveScreen.git
cd WaiveScreen && git checkout "${BRANCH}"

# Prepare for, and perform, an FAI softupdate
mkdir -p /srv/fai/config
NONET=1 tools/server/syncer.sh pip
fai -v -N -c DEBIAN -s file:///srv/fai/config softupdate

# Add our custom DeviceTree Overlay
rsync -avP "${DIR}/overlay-user/" /boot/overlay-user/
dtc -q -O dtb -o /boot/overlay-user/rockchip-i2c3.dtbo /boot/overlay-user/rockchip-i2c3.dts
echo "user_overlays=rockchip-i2c3" >> /boot/armbianEnv.txt

# Modify boot.cmd for USB booting
patch -N /boot/boot.cmd "${DIR}/boot.cmd.patch"
mkimage -C none -A arm -T script -d /boot/boot.cmd /boot/boot.scr

# Perform ssh key generation on next boot
systemctl enable armbian-firstrun

# Grow FS on next boot
systemctl enable armbian-resize-filesystem
rm /root/.rootfs_resize
sfdisk --delete /dev/mmcblk1 2

# Force updating UUID and hostname on next boot
rm -f /etc/UUID

# Remove Armbian hardcoded MAC address
rm -f /etc/NetworkManager/system-connections/*

# Cleanup
rm -f /root/.not_logged_in_yet /root/.desktop_autologin
rm -rf /srv/fai/config /root/.ssh
systemctl disable waivescreen-install

# Shutdown the system
echo "WaiveScreen Installation Finished.  Shutdown in 30 seconds..."
sleep 30
shutdown -P now
