#!/usr/bin/env bash

# TODO Write this
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
sudo chmod 0600 "${ARM_MOUNT}/root/.ssh/*"

# Copy and install WaiveScreen setup scripts
sudo rsync -avP "${DIR}/../../Linux/armbian/" "${ARM_MOUNT}/root/armbian/"

# Only grow the filesystem to 3GB
echo '6000000s' | sudo tee "${ARM_MOUNT}/root/.rootfs_resize"

# TODO systemd oneshot enable

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

