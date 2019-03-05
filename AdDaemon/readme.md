Screens are assigned tasks and timelines for completion.
Screens query the server for at most, the next (for now) 15 minutes of ads

API:

POST /sow

This is a "statement of work" which does the following:
  * Tells the server where the screen is
  * Tells the server how much of a job has been complete
  * Updates the most recently seen timestamp for an id
  * Hands out "jobs" for advertising which are subdivisions of contracts

Request payload:

```
{
  id: ... id of screen ...
  lat: current latitude
  lng: current longitude
  work: [
    {
      id: ... unique id as assigned by the adserver ...
      done: percentage done as a float between 0 and 1
    }
    ...
  ]
}
```

Response payload:

```
{
  res: true (if success)
  (err: err code if failure)
  jobs: [
    { 
      campaign_id: unique id for the campaign
      asset: string
      goal_seconds: time in seconds assigned to display asset
      job_start: utc earliest time to display
      job_end: utc last time to display
      geofence: [ lat/lng ... ],
      job_id: unique id for this specific request
    }
  ]
}
```

Notes (Subject to change):

The screen doesn't have any "working memory" of previous work after the response comes back. It records timestamps when a 
particular job was satisfied and then moves on.  Even if it's only say 10% done with the job, it may be given the same campaign
to "continue" to do the work, but it shouldn't care. The ScreenDisplay is tasked with caching the assets in an LRU and should 
be fine.

This tries to keep the consistency among the screens easy to deal with so that the workload can be realistically distributed 
without particular screens going "rogue" and trying to be "efficient".
