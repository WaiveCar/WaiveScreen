This is not the readme or overview, this is the communication points between the modules.

## Website -> AdDaemon
### Deal

#### Request
`GET /deal` - Gets a price deal for a set of parameters
 * zone=*zone*|(lat=*latitude*|lng=*longitude*|radius=*meters*) - either an area or zone code:
    * 1 - daytime santa monica
    * 2 - weekend nights hollywood
    * 3 - weekday mornings near freeways
 * id=*session id*
 * price=*price*|perday=*seconds* price in cents the user wants to pay OR time in seconds the user wants to have per day
 * start=*date* 8601 UTC start date of the campaign (if empty, means now)
 * end=*date* 8601 UTC start date of the campaign
 * oldId=*quote to invalidate* If a user is updating their quote, this is the previous quote id.

#### Response
```
{
   id: *quote id of the offer*
   zone|lat,lng,radius: *area of the ad*
   start: *UTC start time*
   end: *UTC end time*
   price: *price in cents for the deal*
   perday: *time in seconds the ad will display per day*
}
```

### Capture

#### Request
`POST /capture` - Uses a payment gateway and id to capture a user paid for a service
 * id - Quote id to purchase
 * service - Currently "paypal"
 * assetId - id of asset
 * orderId - The unique orderId returned by the gateway

#### Response
The server independently verifies, based on the order id that the funds have been transferred.
```
{
   result: *success | error*,
   id: *unique id of the order*,
   message: *If error, what message to display to the user*,
   buyer: *personal info of buyer*
}
```


## ScreenDisplay <-> ScreenDaemon

Display -> Daemon

POST /sow

 * For initialization, an empty payload is sufficient.

## ScreenDaemon <-> AdDaemon

Screen -> Ad

POST /sow

This is a "statement of work" which does the following:
 * Tells the server where the screen is
 * Tells the server how much of a job has been complete
 * Updates the most recently seen timestamp for an id
 * Hands out "jobs" for advertising which are subdivisions of contracts

Request payload:

```
{
  id: unique id of screen,
  lat: current latitude,
  lng: current longitude,
  jobs: [
    {
      id: unique id as assigned by the AdServer,
      done: seconds displayed,
      err: (optional, if an error was encountered)*
    }
    ...
  ]
}
```

Error codes:
 * NOT_FOUND - The asset to display wasn't able to be displayed


## Ad -> Screen

Response payload:

```
{
  res: true (if success)
  (err: err code if failure)
  jobs: [
    { 
      job_id: unique id for this specific request,
      campaign_id: unique id for the campaign,
      goal: time in seconds assigned to display asset,

      job_start: utc earliest time to display,
      job_end: utc last time to display,
      // This is the schema for the campaign. Eventually
      // this can be "smart" and figure out how to be 
      // "optimal" but for now it's going to be stupid
      // and essentially map the database

      campaign: {
        id: unique id of campaign,
        asset: HTTP(s) url of the asset to display (probably png/jpg/mp4),
        duration_seconds: duration of the campaign,
        lat: latitude,
        lng: longitude,
        radius: meter radius,
        start_time: of the campaign,
        end_time: of the campaign
      }
    }
    ...
  ]
}
```
