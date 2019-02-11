The screen display is mostly just a clever HTML SPA. 

Ads constitute an LRU cache of DOM modules which get attached to the document when necessary.

### Future:

  A socket connection is kept open to the Screen Daemon which blindly instructs a "screenplay", in this case, a list of assets to display 

  The screen display then reports back whenever it changes the ad.

The *simpler* model here is to not have a push model that can override a schedule but instead to have a pull model that sits as the other half of the reporting end point, this will be the v1 here:

 * Screen reports back the status of the displayed ad during some interval when it gets a new set of jobs to satisfy.

This model avoids web-sockets, which avoids a "complicated" system where the web-server is doing stuff between requests ... which is generally seen as a "bad" "sacriligeous" thing so it's needlessly complicated`because frameworks provide features by crippling systems without empowering.

