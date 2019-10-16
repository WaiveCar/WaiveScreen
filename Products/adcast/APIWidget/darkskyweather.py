import requests
from cached_request import request


url = "https://dark-sky.p.rapidapi.com/"
HOST = "dark-sky.p.rapidapi.com"
API_KEY = "694c1c464bmsh3c9d82e8a40bc86p123a0fjsnc1d2618bc860"


def get_forecast(lat="35.6098", lon="-117.6781"):
    """
    Gets forecast response payload

    Args:
        lat - latitude as string or float
        lon - longitude as string or float
    Return:
        request response item
    """
    querystring = {"lang": "en", "units": "auto", "exclude": "minutely,daily,flags"}
    headers = {}
    headers['x-rapidapi-host'] = HOST
    headers['x-rapidapi-key'] = API_KEY
    response = request("GET", url+'/'+str(lat)+','+str(lon), headers=headers, params=querystring)
    return response

def get_hourly(response, hours=12, start=0):
    """
    Parses forecast response into hourly weather forecast

    Args:
        response - response generated from get_forecast()
        start - first hour of hourly forecast return, current hour = 0, default = 0
        hours - number of hours to forecast (max hours = 48 - start) default = 12
    Return:
        0 on unsuccessful request
        list of hourly forecast (in local units) dicts with the following keys:
            hour - hour of forecast relative to now
            summary - plain text description string of weather forecast, ex: 'light rain'
            temp - forecast temperature as float
            precip_chance - percent chance of rain as float between 0 and 1
            precip_type - if precip_chance > 0, this key is populated with type of precipitation, ex: rain, snow
            time - unix time code of utc hour
    """
    if response.status_code != 200:
        return 0
    res = response.json()
    hourly = []
    for i in range(min(start, 47), min(start + hours, 48)):
        hour = {
            'hour': i,
            'summary': res['hourly']['data'][i]['summary'],     # summary
            'temp': res['hourly']['data'][i]['temperature'],    # temperature
            'precip_chance': res['hourly']['data'][i]['precipProbability'],  # rain_chance
            'time': res['hourly']['data'][i]['time']            # unix time
        }
        if hour['precip_chance'] > 0:
            hour['precip_type'] = res['hourly']['data'][i]['precipType']    # rain/snow/hail
        hourly.append(hour)
    return hourly


def get_current_weather(response):
    """
    Parses forecast response into hourly weather forecast

    Args:
        response - response generated from get_forecast()
    Return:
        0 on unsuccessful request
        dict of current weather (in local units) with keys:
            summary - plain text summary string of current weather, ex: 'light rain'
            temp - current temperature
            feels_like - temperature feels like (wind chill, heat index factored)
            wind_speed - current average wind speed
            time - current time
    """
    res = None
    if not isinstance(response, dict):
        if response.status_code != 200:
            return 0
        res = response.json()
    else: res = response
    current = {
        'summary': res['currently']['summary'],         # current summary
        'temp': res['currently']['temperature'],        # current temp
        'feels_like': res['currently']['apparentTemperature'],  # feels like
        'wind_speed': res['currently']['windSpeed'],    # wind speed
        'time': res['currently']['time']                # time
    }
    return current

