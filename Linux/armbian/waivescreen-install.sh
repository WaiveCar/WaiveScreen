#!/usr/bin/env bash

# This is meant to be run on a fresh Armbian image, prepared by
# tools/server/prepare_armbian_image.sh
#
# We run fai softupdate to install the WaiveScreen system and then prepare
# the installed image for cloning.

set -x

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
TMP_DIR="$(mktemp -d)"
BRANCH=${BRANCH:-armbian-port}

# sudo doesn't work with an expired password
chage -d 18330 root

# Wait up to 30 seconds for NTP time sync
chronyc waitsync 3

apt update && apt full-upgrade -y && apt install -y rsync fai-client git gpg sudo patch python3-pip python3-setuptools python3-dev

cd "${TMP_DIR}"
git clone git@github.com:WaiveCar/WaiveScreen.git
cd WaiveScreen && git checkout "${BRANCH}"

mkdir -p /srv/fai/config
NONET=1 tools/server/syncer.sh pip
fai -v -N -c DEBIAN -s file:///srv/fai/config softupdate

# Modify boot.cmd for USB booting
patch -N /boot/boot.cmd "${DIR}/boot.cmd.patch"
mkimage -C none -A arm -T script -d /boot/boot.cmd /boot/boot.scr

# TODO ssh key generation on next boot
systemctl enable armbian-firstrun

# TODO grow fs on next boot
systemctl enable armbian-resize-filesystem
rm /root/.rootfs_resize
sfdisk --delete /dev/mmcblk1 2

# TODO cleanup
systemctl disable waivescreen-install
