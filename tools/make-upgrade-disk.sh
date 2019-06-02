#!/bin/bash
path=/tmp/upgradedisk
package=/tmp/upgrade.package
[ -e $path ] && rm -fr $path
mkdir $path
git clone git@github.com:WaiveCar/WaiveScreen.git $path
cd $path

#
# This is not a mistake, this was tested among xz, compress, bzip2, 
# and gzip
#
# After testing, xz was only a 2% space gain over boring straight .tar
# Also it was 26 seconds versus < 0.1. Since this is going to be
# on physical medium we want to minimize time, not space. Even in
# decompression we are talking 2 sec versus < 0.1. So we'll do
# generic bland .tar since it's 2 orders of magnitude faster
#
tar -cf $package .
echo "cleaning up"
rm -fr $path
echo "Upgrade package at $package"
