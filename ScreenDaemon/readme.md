Makes requests 

This can be 3 things

  1. grabs data from the board, puts it in database
  2. serves things to screen display, getting it from the database
  3. talks to ad daemon using most recent data from database for lat/lng

Separating these out into 3 "micro-services" may be the easiest approach using something like the database as the middleman --- I know I know that this requires sync to happen and we are looking at some seek time/slow/latency/eventual consistency issues ... sure ... but let's start there and then "optimize" into some kind of IPC (through either dbus, socket or pub/sub) when necessary.  This does use a database as ipc, I know ... I know ... but we also need to be recording things somewhere so it should be ok I guess.

It also makes it so that we don't need to worry about different "event loops" which is what many of these servers want ... they basically want you to use a process/thread system but this shouldn't be necessary.

Note: This has been the most difficult part to write ... having a few failed attempts at refactoring my indycast codebase and then
  a few failed attempts to create a single version with websockets support using async. Each attempt was aborted due to complexity 
  and difficulty - this has to be, by the constraints of resources, a small thing to maintain and not a grand project.
  
Technically the effort was started in October 2018 and I'm now writing this in March 2019 ... do the math, this was hard.

The first attempt was bringing things in piecemeal which is probably the right way to go about it.

The "trick" I think is to use the piecemeal as a library between 3 separate applications - that's probably the most maintainable way to do it.
