Some terms:

  * Contract - What someone has paid us for displaying in a specific region at a specific time range. There's assets and an account associated with it. It's either satisfying, completed, failed, or pending.
  * Screen - The thing that sits on top of the car
  * Server - Machine(s) living off in the cloud with Peter Pan, may be distributed with a load balancer

The SCREEN parts:

  * Screen display 
    * Displays advertisements on the screen. 
    * In charge of making sure it has the assets to display cached and has the content on the screen that it's been told to display.
    * Records when and how long a display was shown to report back to the screen daemon.
  * Time daemon
    * Syncs timestamps and records the last time it was sync'd via an incrementing counter stored on disk. Should be simple
  * Screen sensor 
    * Records the DoF, temperature, accelerometer, GPS, and video data from the screen and stores it in appropriate ways so that arbitrary timeslices can be reconstituted.  
    * Responsible for making sure it doesn't store too much historical data that it eats up the disk space and is responsible for knowing what historical records it has.
  * Power daemon 
    * Makes sure that the screen and various power systems are either off or on depending on a variety of factors. 
    * Knows whether the car is plugged in, the ignition is on, and what strategies to execute based on the power draw, which it talks to the screen sensor to get.
    * It's also responsible for recording these states in a timestamped way so that they can be retrieved later.
  * Screen daemon
    * Instruments and works with the screen sensor to pass readings over the network.
    * Works with the Ad daemon: 
      * Sends over gps readings from the Screen sensor and retrieves assets to display
      * Talks to the Screen display to display specific assets
      * Gets the duration of time an asset was displayed on the screen and reports back to the Ad daemon

The SERVER parts:

  * Ad daemon
    * Has contracts which states when and where ads should be displayed.
    * Gets gps requests rom the Screen daemon and then responds with ad descriptions and terms to be displayed.
    * Keeps track of who satisfied what part of the contract. This is a message passing model in distributed computing terms.
  * Report system
    * Talks with the Ad daemon and can generate real time "reports" of the current state of a contract. 
    * FUTURE: Permits a user to change the terms of a contract, talking to the Ad daemon.
    * Sends out reports at the end of a contract on whether it's completed or failed. 

Things currently not covered:

  * Upgrade strategies
  * Installation management
  * Failure detection 

Some notes:

  * These are mostly ontological distinctions which may or may not manifest themselves in code or distinctly separate projects. For instance, there may not be "time-daemon.py" that does a bunch of stuff. It may just be a cronjob to a few shell scripts. The satisfiability of need is the requirement, not the existence of a siloed project.
  * The overall goal is to keep each component 
    * Good only at one thing
    * Stupid at everything else  
    * Not required to make judgements or have a dscriminatory power 
    * A "vessel of intention" that chaperones contracts and physical records between end-points

