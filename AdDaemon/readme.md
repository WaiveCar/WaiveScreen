### redesign

The php diy system has been ok up to this point but its hitting the limit and some kind of frameworky-ish thing should be used. My current thoughts are

 * jinja        - templates
 * flask        - routing
 * flask-login  - user management
 * sqlalchemy   - orm/routing

There's also zend, slim, and django

Installation:

  See ../tools/server/server-setup.sh

Screens are assigned tasks and timelines for completion.
Screens query the server for at most, the next (for now) 15 minutes of ads


Notes (Subject to change):

The screen doesn't have any "working memory" of previous work after the response comes back. It records timestamps when a particular job was satisfied and then moves on.  Even if it's only say 10% done with the job, it may be given the same campaign to "continue" to do the work, but it shouldn't care. The ScreenDisplay is tasked with caching the assets in an LRU and should be fine.

This tries to keep the consistency among the screens easy to deal with so that the workload can be realistically distributed without particular screens going "rogue" and trying to be "efficient".

Installation notes:

  Remember to increase the max upload file size in the php.ini


