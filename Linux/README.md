This things uses FAI and will eventually be on a USB stick. The fai-config is where the screen install magic lives.

### Installing fai
This is mostly to make this part reproducible at a future date.

```
# fai-setup -v
# fai-chboot -IFv -u nfs://faiserver/srv/fai/config screen
... TODO ..
```
Sometimes the bootdisk installer iso may not actually boot. 
I've found the best way to fix things is to blow away /srv and then run fai-setup -v again and then try to 
remake the bootdisk. Some confusion usually happens from an initrd update

The file sources.list in the current directory might be best moved to /etc/fai/apt.  The archive server is quite a bit slower then the main server.


### Creating bootdisks/updating
The tools and documentation of how to make upgrades and boot disks is at `tools/server`

#### Network install
Network install notes:

  TFTP server options:

  /usr/sbin/in.tftpd --listen --user tftp --address 0.0.0.0:69 --secure /srv/tftp --verbosity 5 -L -p

FAI notes

  I really fucking hate this thing but it appears to be the best 
  solution for our needs. The documentation is ambiguous atrocious
  and terrible.  I have nothing good to say about it but it appears
  to be able to get the job done.  

  * Additional scripts have to have 0777 permissions and be owned by root

  * Softupdates are done from the client

  * The client has to have fai and nfs-common on it in order to do a softupdate

  * The PWD the scripts are run from is /var/lib/fai/config/scripts

  * The shell output goes into an obscurely documented file called shell.log
