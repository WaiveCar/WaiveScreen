#!/bin/bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y python3 python3-numpy libfreetype6-dev libpng-dev sqlite3 nodejs npm
pip3 install --upgrade pip setuptools
sudo pip3 install -r requirements.txt
sudo npm -g install sass
npm install
