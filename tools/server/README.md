Most control happens through the `screen` program which has a number of command line arguments that can be instrumented
to control a screen that's connected via a local network, assuming that you are an FAI host and have access to the
TP-Link smart plug

The other important thing here is the "syncer.sh" which essentially has an inotify running on the files and then copies them over to the /srv directory (which is what FAI seems to have a love affair with) along with running an rsync to update it immediately on the remote host.  This is similar to the vagrant model where you can modify a file on the host machine and then have it updated on the client.

`clone-db.sh` copies the database from the production server and installs it locally
It's all instrumented from the host in this case

 * make-upgrade-disk - This will create an upgrade that hopefully will be automagically read by a screen, recognized and upgraded.
 * make-install-disk - This will take an existing FAI install and create a bootable iso from it. Currently it has only been run on the janky laptop in the garage so if it's on a different machine you'd probably have to set up an FAI network install first.
   * Note before running this you may need to add the gpg key [like so](https://fai-project.org/download/):`gpg -a --recv-keys 2BF8D9FE074BCDE4; gpg -a --export 2BF8D9FE074BCDE4 | sudo apt-key add -` 
 * graph.gnu - a gnuplot script that can be run with power-monitor.js for smart plug power monitoring.
 * syncer.sh - In a local-area network debugged version of the screen (ran through dcall dev_setup) this tool will help sync stuff from the server to the test screen. It also makes a local archive of the pip whls for the make-*-disk tools.
