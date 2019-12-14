#!/bin/bash
# libusb-0.1-4
echo "This doesn't actually work ... copy the avrdude from an arduino install at hardware/tools/avr/bin/avrdude over here."
exit
version=avrdude-6.3
sudo apt install libusb-1.0-0-dev libelf-dev libusb-dev build-essential bison flex
wget http://download.savannah.gnu.org/releases/avrdude/$version.tar.gz
tar xf $version.tar.gz
cd $version
./configure && make
strip avrdude
