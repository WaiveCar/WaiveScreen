#!/bin/sh
useradd -m sshbounce
chsh -s /usr/sbin/nologin sshbounce 
mkdir ~sshbounce/.ssh
chown sshbounce.sshbounce -R ~sshbounce/.ssh
cat KeyBounce.pub >> ~sshbounce/.ssh/authorized_keys
