#!/bin/bash
# Copyright (c) 2015, Cortex Systems LLC
set -o pipefail
set -o errexit
set -o nounset

if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root" 1>&2
    exit 1
fi

TARGET=/opt/cortex/player
UPDATE_DIR=/opt/cortex/update
REMOTE="https://fleet.cortexpowered.com/download/latest/json"
ARCH=

case `arch` in
    "x86_64")
        ARCH=x64
        ;;
    i?86)
        ARCH=ia32
        ;;
    arm*)
        ARCH=arm
        ;;
    *)
        echo "Unsupported architecture: `arch`"
        exit 1
esac

function usage() {
    cat <<EOF
    Usage: $0 [options]

    Installs the latest version of the Cortex player under ${TARGET}.

    -u <username>   Both the Cortex player and the Watchdog processes will run as <username>.
    [-n]            No Watchdog or autostart on login.
    [-i]            Install the version with interactive support.

EOF
}

USER=
NOWATCHDOG=
INTERACTIVE=

while getopts ":u:in" opt; do
    case $opt in
        u)
            USER=$OPTARG
            ;;
        i)
            INTERACTIVE=1
            ;;
        n)
            NOWATCHDOG=1
            ;;
        \?)
            echo "Invalid option: -$OPTARG" >&2
            exit 1
            ;;
        :)
            echo "Option -$OPTARG requires an argument." >&2
            exit 1
            ;;
    esac
done

if [ -z "$USER" ]
then
    usage
    exit 1
fi

if id -u "$USER" >/dev/null 2>&1; then
    mkdir -p $TARGET
    chown -R $USER $TARGET
else
    echo "Unknown user: $USER"
    exit 1
fi

apt-get update
apt-get install curl xdotool unclutter libudev1 python -y

if [ ! -z $INTERACTIVE ];
then
    ARCH="${ARCH}nosdk"
fi

DOWNLOAD_URL=`curl $REMOTE -# 2>/dev/null | grep "player/linux/$ARCH/url" | awk -F'"' '{print $4}'`
VERSION=`curl $REMOTE -# 2>/dev/null | grep "version" | awk -F'"' '{print $4}'`

if [[ -z "$DOWNLOAD_URL" || -z "$VERSION" ]]
then
    echo "Failed to get version details from Cortex server."
    exit 1
fi

mkdir -p $TARGET/${VERSION}
mkdir -p $UPDATE_DIR

echo "Downloading the latest Cortex player version (v${VERSION}) from $DOWNLOAD_URL"
curl $DOWNLOAD_URL -# | tar zxv -C ${TARGET}/${VERSION}

if [ -e ${TARGET}/current ]
then
    rm ${TARGET}/current
fi

ln -s ${TARGET}/${VERSION} ${TARGET}/current

if [ ! -f /etc/ld.so.conf.d/cortex.conf ];
then
    echo "${TARGET}/current/lib" > /etc/ld.so.conf.d/cortex.conf
    ldconfig
fi

chown -R $USER $TARGET
chown -R $USER $UPDATE_DIR

UHOME=$( getent passwd "$USER" | cut -d: -f6 )

if [ ! -z $NOWATCHDOG ];
then
    su -c "mkdir -p $UHOME/.config/autostart" $USER
    su -c "echo '' > $UHOME/.config/autostart/cortex.desktop" $USER
    su -c "echo '[Desktop Entry]' >> $UHOME/.config/autostart/cortex.desktop" $USER
    su -c "echo 'Type=Application' >> $UHOME/.config/autostart/cortex.desktop" $USER
    su -c "echo 'Exec=${TARGET}/current/CortexPlayer' >> $UHOME/.config/autostart/cortex.desktop" $USER
    su -c "echo 'Hidden=false' >> $UHOME/.config/autostart/cortex.desktop" $USER
    su -c "echo 'NoDisplay=false' >> $UHOME/.config/autostart/cortex.desktop" $USER
    su -c "echo 'X-GNOME-Autostart-enabled=true' >> $UHOME/.config/autostart/cortex.desktop" $USER
    su -c "echo 'Name=CortexPlayer' >> $UHOME/.config/autostart/cortex.desktop" $USER
    su -c "echo 'Comment=Cortex player' >> $UHOME/.config/autostart/cortex.desktop" $USER

    su -c "mkdir -p $UHOME/.cortex" $USER
    su -c "echo '--disable-watchdog' >> $UHOME/.cortex/flags" $USER
    su -c "echo '--disable-alerts' >> $UHOME/.cortex/flags" $USER
    FLAGS=`cat $UHOME/.cortex/flags | tr ' ' '\n' | sort | uniq | grep -v -e '^$'`
    su -c "echo \"$FLAGS\" > $UHOME/.cortex/flags" $USER
fi

echo -e "\e[32mCortex player is installed under ${TARGET}/current."
echo -e "\e[32mCortex player will auto-configure once you complete the registration."
echo -e "\e[32mRun the \"${TARGET}/current/CortexPlayer\" command on your terminal as a normal user to start the player."
if [ -z $NOWATCHDOG ];
then
    echo -e "\e[32mAutostart config written to \"${UHOME}/.config/autostart/cortex.desktop\"."
fi
echo -en "\033[0m"
