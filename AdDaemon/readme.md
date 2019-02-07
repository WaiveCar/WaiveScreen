Screens are assigned tasks and timelines for completion.

{ 
  asset: string
  duration: seconds (float)
  startTime: utc
  endTime: utc
  now: utc
  completion: 0-1 (float)
  jobid: int
  campaignid: int
}


Screens query the server for at most, the next (for now) 15 minutes of ads

Notes:

 MySQL spatial extension
