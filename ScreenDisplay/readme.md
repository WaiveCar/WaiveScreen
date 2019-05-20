The screen display is mostly just a clever HTML SPA. 

Ads constitute an LRU cache of DOM modules which get attached to the document when necessary.

The *simpler* model here is to not have a push model that can override a schedule but instead to have a pull model that sits as the other half of the reporting end point, this will be the v1 here:

 * Screen reports back the status of the displayed ad during some interval when it gets a new set of jobs to satisfy.

This model avoids web-sockets, which avoids a "complicated" system where the web-server is doing stuff between requests ... which is generally seen as a "bad" "sacriligeous" thing so it's needlessly complicated`because frameworks provide features by crippling systems without empowering.

The even easier model is to be super-duper-dumb and only be aware of what's next ... as in have no schedule at all and always nag the server (which is the same computer) for the next thing to display.  Under this model whenever an ad displays we guarantee 1 cycle of display for the cyclic duration (not to be obtuse, but this is up for debate - probably about 15 seconds).  This avoids any need for a web-socket or intelligent two-way communication.

API:

The api here matches the AdDaemon api for sow, refer to it for the information.

### Future:

  A socket connection is kept open to the Screen Daemon which blindly instructs a "screenplay", in this case, a list of assets to display 

  The screen display then reports back whenever it changes the ad.


Note : subslice video ffmpeg -i input.mp4 -c copy -map 0 -segment_time 00:20:00 -reset_timestamps 1 -f segment output%03d.mp4
