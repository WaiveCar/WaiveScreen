#!/usr/bin/env bash

# The script will take a stock Armbian image and modify it so that WaiveScreen
# is installed when you boot it up.
#
# The first argument is the uncompressed Armbian image.  It will be modified
# in place, so make a copy if you want to keep the original.
#
# The (optional) second argument is the sdcard device to write the image to.
# Specify the disk device, not a disk partition.  For example: /dev/mmcblk0
#
# We are currently targeting the NanoPi M4v2 from FriendlyArm with the image:
# Armbian_20.05.0-trunk_Nanopim4v2_buster_current_5.4.25_minimal.img
#

# TODO remove
set -x

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BRANCH=${BRANCH:-armbian-port}

die() {
  echo "${1}"
  exit 1
}

if [[ ! -f "${1}" ]]
then
  die "USAGE: ${0} armbian_image [sdcard_device]"
fi

# Create device mapping for the partition in the image
ARM_PART="$(sudo kpartx -av ${1}|grep -m1 'add map'|cut -d' ' -f3)"

if [[ -z "${ARM_PART}" ]]
then
  die "Unable to find partition in provided Armbian image: ${1}"
fi

# Mount the image's root partition in a temp folder
ARM_MOUNT="$(mktemp -d)"

if sudo mount "/dev/mapper/${ARM_PART}" "${ARM_MOUNT}"; then
  # Copy key and config for Github access
  sudo rsync -vP ${DIR}/../../Linux/fai-config/files/home/.ssh/{config,github} "${ARM_MOUNT}/root/.ssh/"
  sudo chmod 0700 "${ARM_MOUNT}/root/.ssh/"
  sudo chmod 0600 "${ARM_MOUNT}/root/.ssh/"{config,github}

  # Copy and install WaiveScreen setup scripts
  sudo rsync -avP --chown=root:root "${DIR}/../../Linux/armbian/" "${ARM_MOUNT}/root/armbian/"
  sudo cp "${ARM_MOUNT}/root/armbian/waivescreen-install.service" "${ARM_MOUNT}/lib/systemd/system/"
  sudo ln -s "${ARM_MOUNT}/lib/systemd/system/waivescreen-install.service" "${ARM_MOUNT}/etc/systemd/system/multi-user.target.wants/"

  # Only grow the filesystem to 3GB
  echo '6000000s' | sudo tee "${ARM_MOUNT}/root/.rootfs_resize"

  # Disable bluetooth patchram daemon
  sudo rm "${ARM_MOUNT}/etc/systemd/system/multi-user.target.wants/rk3399-bluetooth.service"

  # Set verbose logging to the serial debug terminal
  sudo sed -i 's/verbosity=1/verbosity=7/' "${ARM_MOUNT}/boot/armbianEnv.txt"

  # Cleanup after ourselves
  cd "${DIR}"
  sudo umount "${ARM_MOUNT}"
  sudo kpartx -dv "${1}"
  rmdir "${ARM_MOUNT}"
else
  sudo kpartx -dv "${1}"
  rmdir "${ARM_MOUNT}"
  die "Unable to mount the image partition: /dev/mapper/${ARM_PART} -> ${ARM_MOUNT}"
fi

# Write the image to the sdcard if provided.
if [[ "${2}" =~ ^.*/mmcblk[0-9]$ ]] && [[ -b "${2}" ]]
then
  echo "Writing modified image to sdcard..."
  sudo dd if="${1}" of="${2}" bs=1M status=progress
  sync
else
  echo "Modified image ready for writing to sdcard: ${1}"
fi
