from catfact import get_cat_fact 
from darkskyweather import get_forecast, get_hourly, get_current_weather 
from newsheadlines import get_news_stories
from sports import get_MLB_scores, get_NFL_scores
from stocks import get_daily_stock_movement
from traffic import get_traffic_incidents
from uselessfact import get_random_fact
import geocoder
import hashlib
latlng = geocoder.ip('me').latlng

def fetch_info():
    return {
        'catfact': get_cat_fact(),
        'forecast': get_current_weather(get_forecast()),
        'news': get_news_stories(),
        'mlb_scores': get_MLB_scores(),
        'nfl scores': get_NFL_scores(2),
        'stocks': get_daily_stock_movement('MSFT'),
        'random fact': get_random_fact()
    }

print('output: ', fetch_info())
