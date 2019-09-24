from catfact import get_cat_fact 
from darkskyweather import get_forecast, get_hourly, get_current_weather 
from newsheadlines import get_news_stories
from sports import get_MLB_scores, get_NFL_scores
from stocks import get_daily_stock_movement
from traffic import get_traffic_incidents
from uselessfact import get_random_fact
import hashlib, json, geocoder
latlng = geocoder.ip("me").latlng

def fetch_info():
    raw_json = {
        "catfact": get_cat_fact(),
        "forecast": get_current_weather(get_forecast()),
        "news": get_news_stories(),
        "mlb_scores": get_MLB_scores(),
        "nfl_scores": get_NFL_scores(2),
        "stocks": get_daily_stock_movement("MSFT"),
        "random_fact": get_random_fact(),
        "traffic": get_traffic_incidents(latlng[0], latlng[1], 5)
    }
    with open("./widgetfiles/parsed_widget_data.json", "w+") as f:
        json.dump(raw_json, f)

    parsed = {}
    parsed["catfact"] = {
        "feed": [{
            "text": raw_json["catfact"],
            "image": None
        }], 
        "source": "https://cat-fact.herokuapp.com/facts",
        "expiration": None
    }

    forecast = raw_json["forecast"]
    parsed["forecast"] = {
        "feed": [{
            "text": "Today's forcast: {} with an actual temperature of {} degrees and a wind speed of {} mph.".format(forecast["summary"], forecast["temp"], forecast["wind_speed"]),
            "image": None
        }], 
        "source": "https://dark-sky.p.rapidapi.com/",
        "expiration": None
    }

    parsed["news"] = {
        "feed": list(map(lambda obj: {
            "text": "{}: {}".format(obj["source_name"], obj["description"]),
            "image": obj["image_url"]
        }, raw_json["news"])),
        "source": "https://newsapi.org/v2/top-headlines",
        "expiration": None
    }

    parsed["mlb_scores"] = {
        "feed": list(map(lambda obj: {
            "text": "{} vs. {}: {}-{}".format(obj["home"], obj["away"], obj["home_score"], obj["away_score"]),
            "image": None
        }, raw_json["mlb_scores"]["games"])),
        "source": "http://api.sportradar.us/mlb/trial/v6.5/en/games/",
        "expiration": None
    }

    parsed["nfl_scores"] = {
        "feed": list(map(lambda obj: {
            "text": "{} vs. {}: {}-{}".format(obj["home"], obj["away"], obj["home_score"], obj["away_score"]),
            "image": None
        }, raw_json["nfl_scores"]["games"])),
        "source": "http://api.sportradar.us/nfl/official/trial/v5/en/games/",
        "expiration": None
    }

    parsed["random_fact"] = {
        "feed": [{
            "text": raw_json["random_fact"],
            "image": None
        }], 
        "source": "https://uselessfacts.jsph.pl/random.json?language=en",
        "expiration": None
    }

    stocks = raw_json["stocks"]
    parsed["stocks"] = {
        "feed": [{
            "text": "{}: Open: {}, Close: {}, High: {}, Low: {}".format(stocks["symbol"], stocks["open"], stocks["close"], stocks["high"], stocks["low"]), 
            "image": None
        }],
        "source": "https://www.alphavantage.co/query",
        "expiration": None
    }

    parsed["traffic"] = {
        "feed": list(map(lambda obj: {
            "text": "{} {}".format(obj["LOCATION"]["INTERSECTION"]["ORIGIN"]["STREET1"]["ADDRESS1"] if "INTERSECTION" in obj["LOCATION"] else obj["LOCATION"]["DEFINED"]["ORIGIN"]["ROADWAY"]["DESCRIPTION"][0]["content"], obj["TRAFFICITEMDESCRIPTION"][0]["content"]),
            "image": None
        }, raw_json["traffic"])),
        "source": "https://traffic.api.here.com/traffic/6.0/incidents.json",
        "expiration": None
    }

    with open("./widgetfiles/parsed_widget_data.json", "w+") as f:
        json.dump(parsed, f)

    return raw_json

if __name__ == "__main__":
    fetch_info()
