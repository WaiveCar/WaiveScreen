#!/usr/bin/env bash

# TODO Write this nice summary.

set -x

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BRANCH=${BRANCH:-armbian-port}

die() {
  echo $1
  exit 1
}

if [[ ! -f "$1" ]]
then
  die "USAGE: ${0} armbian_image [sdcard_device]"
fi

ARM_PART="$(sudo kpartx -av ${1}|grep -m1 'add map'|cut -d' ' -f3)"

if [[ -z "${ARM_PART}" ]]
then
  die "Unable to find partition in provided Armbian image: ${1}"
fi

ARM_MOUNT="$(mktemp -d)"
sudo mount "/dev/mapper/${ARM_PART}" "${ARM_MOUNT}"

# Copy key and config for Github access
sudo rsync -vP ${DIR}/../../Linux/fai-config/files/home/.ssh/{config,github} "${ARM_MOUNT}/root/.ssh/"
sudo chmod 0700 "${ARM_MOUNT}/root/.ssh/"
sudo chmod 0600 "${ARM_MOUNT}/root/.ssh/"{config,github}

# Copy and install WaiveScreen setup scripts
sudo rsync -avP "${DIR}/../../Linux/armbian/" "${ARM_MOUNT}/root/armbian/"
sudo cp "${ARM_MOUNT}/root/armbian/waivescreen-install.service" "${ARM_MOUNT}/lib/systemd/system/"
sudo ln -s "${ARM_MOUNT}/lib/systemd/system/waivescreen-install.service" "${ARM_MOUNT}/etc/systemd/system/multi-user.target.wants/"

# Only grow the filesystem to 2.5GB
echo '5000000s' | sudo tee "${ARM_MOUNT}/root/.rootfs_resize"

# Disable bluetooth patchram daemon
sudo rm "${ARM_MOUNT}/etc/systemd/system/multi-user.target.wants/rk3399-bluetooth.service"

# Show the install process on the serial debug terminal too
sudo sed -i 's/verbosity=1/verbosity=7/' "${ARM_MOUNT}/boot/armbianEnv.txt"


# TODO cleanup
cd "${DIR}"
sudo umount "${ARM_MOUNT}"
sudo kpartx -dv "${1}"
rmdir "${ARM_MOUNT}"

if [[ "${2}" =~ ^.*/mmcblk[0-9]$ ]] && [[ -b "${2}" ]]
then
  echo "Writing modified image to sdcard..."
  sudo dd if="${1}" of="${2}" bs=1M status=progress
  sync
else
  echo "Modified image ready for writing to sdcard: ${1}"
fi

