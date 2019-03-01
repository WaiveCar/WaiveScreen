Makes requests 

This can be 3 things

  1. grabs data from the board, puts it in database
  2. serves things to screen display, getting it from the database
  3. talks to ad daemon using most recent data from database for lat/lng

Separating these out into 3 "micro-services" may be the easiest approach using something like the database as the middleman --- I know I know that this requires sync to happen and we are looking at some seek time/slow/latency/eventual consistency issues ... sure ... but let's start there and then "optimize" into some kind of IPC (through either dbus, socket or pub/sub) when necessary.  This does use a database as ipc, I know ... I know ... but we also need to be recording things somewhere so it should be ok I guess.

It also makes it so that we don't need to worry about different "event loops" which is what many of these servers want ... they basically want you to use a process/thread system but this shouldn't be necessary.


