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
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BRANCH=${BRANCH:-rpi-port}

die() {
  echo "${1}"
  exit 1
}

if [[ ! -f "${1}" ]]
then
  die "USAGE: ${0} rpi_image [sdcard_device]"
fi

# Create device mapping for the partition in the image
RPI_PART="$(sudo kpartx -av ${1}|grep -m2 'add map'|tail -n1|cut -d' ' -f3)"

if [[ -z "${RPI_PART}" ]]
then
  die "Unable to find partition in provided RPi image: ${1}"
fi

# Mount the image's root partition in a temp folder
RPI_MOUNT="$(mktemp -d)"

if sudo mount "/dev/mapper/${RPI_PART}" "${RPI_MOUNT}"; then
  # Copy key and config for Github access
  sudo rsync -vP ${DIR}/../../Linux/fai-config/files/home/.ssh/{config,github} "${RPI_MOUNT}/root/.ssh/"
  sudo chmod 0700 "${RPI_MOUNT}/root/.ssh/"
  sudo chmod 0600 "${RPI_MOUNT}/root/.ssh/"{config,github}

  # Copy and install WaiveScreen setup scripts
  sudo rsync -avP --chown=root:root "${DIR}/../../Linux/rpi/" "${RPI_MOUNT}/root/rpi/"
  sudo cp "${RPI_MOUNT}/root/rpi/waivescreen-install.service" "${RPI_MOUNT}/lib/systemd/system/"
  sudo ln -s "${RPI_MOUNT}/lib/systemd/system/waivescreen-install.service" "${RPI_MOUNT}/etc/systemd/system/multi-user.target.wants/"

  # Remove image's default autologin
  sudo rm "${RPI_MOUNT}"/etc/systemd/system/{autologin@.service,getty@tty1.service.d/autologin.conf}

  # Only grow the filesystem to 3GB
  echo '6000000s' | sudo tee "${RPI_MOUNT}/root/.rootfs_resize"

  # Cleanup after ourselves
  cd "${DIR}"
  sudo umount "${RPI_MOUNT}"
  sudo kpartx -dv "${1}"
  rmdir "${RPI_MOUNT}"
else
  sudo kpartx -dv "${1}"
  rmdir "${RPI_MOUNT}"
  die "Unable to mount the image partition: /dev/mapper/${RPI_PART} -> ${RPI_MOUNT}"
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
