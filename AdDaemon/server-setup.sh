#!/bin/sh

composer() {
  sudo apt install -y curl php7.3-xml zip unzip sqlite3 php7.3-sqlite3
  curl -s https://getcomposer.org/installer | php
  sudo mv composer.phar /usr/local/bin/composer
  composer install
  sudo phpenmod sqlite3
  sudo a2enmod php7.3
  sudo apachectl restart
}
sshuser() {
  useradd -m sshbounce
  chsh -s /usr/sbin/nologin sshbounce 
  mkdir ~sshbounce/.ssh
  chown sshbounce.sshbounce -R ~sshbounce/.ssh
  cat ../Linux/keys/KeyBounce.pub >> ~sshbounce/.ssh/authorized_keys
  echo "Set GatewayPorts Yes in sshd_config"
}

sudo mkdir -p /var/db/waivescreen
sudo chmod 0777 /var/db/waivescreen

composer
sshuser
