#!/bin/bash

if [[ -z "$1" ]]
then
  echo "You must provide an IP address or hostname of the Raspberry Pi" && exit 2
fi

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
T_DIR="$(mktemp -d)"
T_KEY="${T_DIR}/temp"
RPI="root@${1}"
SSH="ssh -i ${T_KEY} ${RPI} "
SCP="scp -i ${T_KEY} "

ssh-keygen -q -N '' -f ${T_KEY}

read -p "Please enter password 'raspberry' when prompted. [Press Enter to continue]"
ssh-copy-id -f -i ${T_KEY}.pub ${RPI} 

if ! ${SSH} echo "We\'re in"
then
  echo "Unable to install the temp ssh key for access to the Raspberry Pi" && exit 1
fi

${SSH} "useradd -m -s /bin/bash -G sudo adorno && cp -a /root/.ssh /home/adorno/"
${SSH} "apt install -y git sudo rsync && echo \"adorno ALL=NOPASSWD: ALL\" >> /etc/sudoers"
${SCP} ${DIR}/../../Linux/fai-config/files/home/.ssh/{config,github} ${RPI}:/home/adorno/.ssh/
${SSH} "chown -R adorno:adorno /home/adorno/.ssh && chmod 600 /home/adorno/.ssh/{config,github}"

${SCP} ${DIR}/setup_raspberry_pi.sh ${RPI}:/tmp/
${SSH} "chmod +x /tmp/setup_raspberry_pi.sh"
ssh -i ${T_KEY} adorno@${1} "/tmp/setup_raspberry_pi.sh"


#${SSH} "rm .ssh/authorized_keys && passwd -d root"
