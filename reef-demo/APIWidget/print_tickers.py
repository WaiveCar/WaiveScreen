from catfact import get_cat_fact 
from darkskyweather import get_forecast, get_hourly 
from newsheadlines import get_news_stories
from sports import get_MLB_scores, get_NFL_scores
from stocks import get_daily_stock_movement
from traffic import get_traffic_incidents
from uselessfact import get_random_fact
import geocoder
latlng = geocoder.ip('me').latlng
print(latlng)

print('cat fact: ', get_cat_fact())
print('forecast: ', get_hourly(get_forecast()))
print('news: ', get_news_stories())
print('mlb scores: ', get_MLB_scores())
print('nfl scores', get_NFL_scores(2))
print('stocks: ', get_daily_stock_movement('MSFT'))
print('traffic: ', get_traffic_incidents(latlng[0], latlng[1], 3))
print('random fact: ', get_random_fact())
