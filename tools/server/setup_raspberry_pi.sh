#!/bin/bash

#  We're using a Debian image, rather than Raspbian to maximize compatibility and ease of installation.
#  Image and instructions from here: https://wiki.debian.org/RaspberryPiImages
#  Once flashed and booted up, we can ssh to the root account and do our updates.

if [[ -z "$1" ]]
then
  echo "You must provide an IP address or hostname of the Raspberry Pi" && exit 2
fi

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
T_DIR="$(mktemp -d)"
T_KEY="${T_DIR}/temp"
RPI="root@${1}"
SSH="ssh -i ${T_KEY} ${RPI} "
SCP="scp -i ${T_KEY} "

ssh-keygen -q -N '' -f ${T_KEY}

read -p "Please enter password 'raspberry' when prompted. [Press Enter to continue]"
ssh-copy-id -f -i ${T_KEY}.pub ${RPI} 

if ! ${SSH} echo "We\'re in"
then
  echo "Unable to install the temp ssh key for access to the Raspberry Pi" && exit 1
fi

${SCP} ${DIR}/../../Linux/fai-config/files/home/.ssh/{config,github} ${RPI}:.ssh/
${SSH} << EOF
chmod 0600 .ssh/github
dd if=/dev/zero of=/swapfile bs=1024 count=1048576
chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile
echo "/swapfile       none    swap sw 0 0" >> /etc/fstab
apt update && apt dist-upgrade -y && apt install -y rsync fai-client git gpg sudo python3-pip
git clone git@github.com:WaiveCar/WaiveScreen.git
mkdir -p /srv/fai/config
sed -i '/^\(pandas\|opencv\|numpy\)/d' WaiveScreen/ScreenDaemon/requirements.txt
NONET=1 WaiveScreen/tools/server/syncer.sh pip
fai -v -N -c DEBIAN -s file:///srv/fai/config softupdate
EOF

# Cleanup after we're done
#${SSH} << EOF
#rm -rf WaiveScreen
#rm -f .ssh/*
#EOF

