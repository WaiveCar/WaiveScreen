#!/bin/sh
git() {
  ssh screen "cd WaiveScreen;git pull"
}

reload() {
  ssh screen "./reload"
}

case $1 in
  git) git ;;
  reload) reload ;;
  *) echo "git reload"
esac
