The screen display is mostly just a clever HTML SPA. 

Ads constitute an LRU cache of DOM modules which get attached to the document when necessary.

A socket connection is kept open to the Screen Daemon which blindly instructs a "screenplay", in this case, a list of assets to display 

The screen display then reports back whenever it changes the ad.
