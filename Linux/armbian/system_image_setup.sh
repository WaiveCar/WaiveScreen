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

systemctl --now disable rk3399-bluetooth

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

# TODO grow fs on next boot

# TODO cleanup
