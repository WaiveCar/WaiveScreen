#!/usr/bin/env bash

# This is meant to be run on a fresh Armbian image, prepared by
# tools/server/prepare_rpi_image.sh
#
# We run fai softupdate to install the WaiveScreen system and then prepare
# the installed image for cloning.

set -x
#set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
TMP_DIR="$(mktemp -d)"
BRANCH="rpi-port"


# change default "pi" user to adorno
usermod --login adorno --home /home/adorno --move-home pi
groupmod --new-name adorno pi

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

# Set adorno user password
. Linux/fai-config/class/FAIBASE.var
usermod -p "${USERPW}" adorno

# Set screen resolution
#echo -e 'hdmi_cvt=1920 538 60 6\nhdmi_group=2\nhdmi_mode=87\nhdmi_drive=2' >> /boot/firmware/usercfg.txt

# Enable i2c-1 bus and disable overscan on HDMI output
echo -e 'dtparam=i2c_arm=on\ndisable_overscan=1' >> /boot/config.txt

# Enable sshd
systemctl enable ssh

# Modify boot.cmd for USB booting

# Perform ssh key generation on next boot
systemctl enable regenerate_ssh_host_keys

# Grow FS on next boot

# Force updating UUID and hostname on next boot
rm -f /etc/UUID

# Set Wifi Country
echo 'country=US' >> /etc/wpa_supplicant/wpa_supplicant.conf
rfkill unblock 0

# Cleanup
#rm -f /root/.not_logged_in_yet /root/.desktop_autologin
#rm -rf /srv/fai/config /root/.ssh
systemctl disable waivescreen-install

# Shutdown the system
echo "WaiveScreen Installation Finished.  Shutdown in 30 seconds..."
#sleep 30
#shutdown -P now
