custom compile
  Here is known working SHA-1s 
  modemmanager    77387cf604c8033a44d62253cf685493cc5d556d
  libqmi          de362e9dd5e5466f9818de173436efa075fdc80c
  libmbim         c603ab385baf5050fdbd47af9bdf9d46d407b1ab
  NetworkManager  f3f5d5c900b8891591eccf2f8e8f5cf3da0907a1

scripts
  get online
  power management
  identification
  ssh hole punching

installs
  git
  chromium
  ffmpeg

Custom compile (maybe)
  modules needed:
  qmi_wwan
  cdc_wdm

There needs to be a test script to see if the sim card is active.

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
