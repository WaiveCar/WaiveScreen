This things uses FAI and will eventually be on a USB stick. The fai-config is where the screen install magic lives.


Network install notes:

  TFTP server options:

  /usr/sbin/in.tftpd --listen --user tftp --address 0.0.0.0:69 --secure /srv/tftp --verbosity 5 -L -p

FAI notes

  I really fucking hate this thing but it appears to be the best 
  solution for our needs. The documentation is ambiguous atrocious
  and terrible.  I have nothing good to say about it but it appears
  to be able to get the job done.  Here's the mirror command I used

  fai-mirror -v -cDEBIAN,DEMO,FAIBASE /srv/debian

  * Additional scripts have to have 0777 permissions and be owned by root

  * Softupdates are done from the client

  * The client has to have fai and nfs-common on it in order to do a softupdate

  * The PWD the scripts are run from is /var/lib/fai/config/scripts

  * The shell output goes into an obscurely documented file called shell.log
