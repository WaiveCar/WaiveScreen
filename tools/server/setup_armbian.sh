#!/usr/bin/env bash

#  We're using an Armbian image, based off of Debian Buster.
#  Image and instructions from here: https://docs.armbian.com
#  Once flashed and booted up, we can ssh to the root account and do our updates.

if [[ -z "$1" ]]
then
  echo "You must provide an IP address or hostname of the SBC to setup." && exit 2
fi

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SSH_KEY="${DIR}/../../Linux/keys/ScreenAccess.pub"
SBC="root@${1}"
SSH="ssh ${SBC} "

read -p "Please enter the root password for the SBC when prompted. [Press Enter to continue]"
ssh-copy-id -f -i ${SSH_KEY} ${SBC} 

if ! ${SSH} echo "We\'re in"
then
  echo "Unable to install the ssh key for access to the SBC" && exit 1
fi

scp ${DIR}/../../Linux/fai-config/files/home/.ssh/{config,github} ${SBC}:.ssh/
${SSH} << EOF
chmod 0600 .ssh/github
apt update && apt full-upgrade -y && apt install -y rsync fai-client git gpg sudo python3-pip python3-setuptools python3-dev python3-numpy
git clone git@github.com:WaiveCar/WaiveScreen.git
cd WaiveScreen && git checkout armbian-port && cd ..
mkdir -p /srv/fai/config
sed -i '/^\(opencv\|pandas\|numpy\)/d' WaiveScreen/ScreenDaemon/requirements.txt
NONET=1 WaiveScreen/tools/server/syncer.sh pip
fai -v -N -c DEBIAN -s file:///srv/fai/config softupdate
systemctl disable rk3399-bluetooth
#systemctl disable location-daemon hostapd isc-dhcp-server
#rm -rf /root/WaiveScreen
#rm /root/.ssh/{config,github}
EOF

