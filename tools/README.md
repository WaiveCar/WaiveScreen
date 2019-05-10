Most control happens through the `screen` program which has a number of command line arguments that can be instrumented
to control a screen that's connected via a local network, assuming that you are an FAI host and have access to the
TP-Link smart plug

The other important thing here is the "syncer.sh" which essentially has an inotify running on the files and then copies them over to the /srv directory (which is what FAI seems to have a love affair with) along with running an rsync to update it immediately on the remote host.  This is similar to the vagrant model where you can modify a file on the host machine and then have it updated on the client.

It's all instrumented from the host in this case
