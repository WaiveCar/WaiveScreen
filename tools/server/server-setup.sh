#!/bin/sh

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BASE=$(dirname $(dirname  $DIR ))
DEST=/var/www/
PHP=7.3
OWNER=www-data

deps() {
  sudo apt install -y apache2 curl zip unzip sqlite3\
    php$PHP php$PHP-xml php$PHP-sqlite3 php$PHP-mbstring php-curl php-intl\
    mariadb-server mariadb-client
}
dirs() {
  sudo mkdir -p /var/db/waivescreen /var/states $DEST
  sudo chmod 0777 /var/db/waivescreen /var/states $DEST
  sudo chown $OWNER.$OWNDER $DEST
}
install() {
  set -x

  # deps
  # dirs

  # composer {
  cd /tmp/
  curl -s https://getcomposer.org/installer | php
  sudo mv composer.phar /usr/local/bin/composer
  cd $BASE/AdDaemon/
  composer install
  # }

  sudo phpenmod sqlite3
  sudo a2enmod php$PHP rewrite headers
  sudo apachectl restart

  sudo cp $BASE/tools/server/server-backup.sh /etc/cron.daily/server-backup
  sudo mkdir -p $BASE/MadisonAve/static/snap/
  sudo chmod 0777 $BASE/MadisonAve/static/snap/
}

sshuser() {
  useradd -m sshbounce
  chsh -s /usr/sbin/nologin sshbounce 
  mkdir ~sshbounce/.ssh
  chown sshbounce.sshbounce -R ~sshbounce/.ssh
  cat $BASE/Linux/keys/KeyBounce.pub >> ~sshbounce/.ssh/authorized_keys
  echo "Set GatewayPorts Yes in sshd_config"
}


install
#sshuser
