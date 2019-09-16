#!/bin/bash

function deb_fix {
  if [[ -z "${1}" ]]
  then
    return 1
  fi
  SOURCE="${1}"
  DIR="$(dirname ${SOURCE})"
  sudo mv ${DIR} ${DIR}.tmp
  sudo mv ${DIR}.tmp/DEBIAN ${DIR}
  sudo rm -rf ${DIR}.tmp
}

cd /home/adorno
git clone git@github.com:WaiveCar/WaiveScreen.git

sudo rsync -avP --chown root:root WaiveScreen/Linux/fai-config/files/etc/ /etc/
for i in $(sudo find /etc/ -type f -name DEBIAN)
do
  deb_fix ${i}
done

cp -vuTr --preserve=mode,timestamps WaiveScreen/Linux/fai-config/files/home /home/adorno
chmod 0600 .ssh/KeyBounce .ssh/github .ssh/dev
chown -R adorno:adorno .
sudo mv .xinitrc /root/

sudo dd if=/dev/zero of=/swapfile bs=1024 count=1048576
sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile
echo "/swapfile       none    swap sw 0 0" >> /etc/fstab

sudo apt install -y $(sed 's/\(#.*$\)//g' WaiveScreen/Linux/fai-config/package_config/DEBIAN | egrep -v '^(P|$|grub-pc|grub-efi|linux-image-|memtest)' | tr '\n' ' ')
sudo pip3 install -r WaiveScreen/ScreenDaemon/requirements.txt



