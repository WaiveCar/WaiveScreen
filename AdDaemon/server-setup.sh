#!/bin/sh

composer() {
  sudo apt install -y curl
  curl -s https://getcomposer.org/installer | php
  sudo mv composer.phar /usr/local/bin/composer
  composer install
}
sshuser() {
  useradd -m sshbounce
  chsh -s /usr/sbin/nologin sshbounce 
  mkdir ~sshbounce/.ssh
  chown sshbounce.sshbounce -R ~sshbounce/.ssh
  cat ../Linux/keys/KeyBounce.pub >> ~sshbounce/.ssh/authorized_keys
}

composer
sshuser
