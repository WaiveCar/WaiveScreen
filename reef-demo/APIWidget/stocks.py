import requests
from datetime import date, timedelta


API_KEY = 'EKP37AWJBNZG9FE2'
url = 'https://www.alphavantage.co/query'


def get_daily_stock_movement(symbol):
    """
    Returns daily stock movement for a given <symbol>

    Args:
        symbol - stock symbol string, ex: 'MSFT' for Microsoft
    Excepts:
        when today does not exist in the returned data, it tries yesterday, if yesterday doesnt exist it returns 0
        this can occur for: bad symbol, bad API_KEY
    Returns:
        0 if response is not good
        dictionary of daily movement with the following keys:
            date - the date of the movement data (today's or yesterday's date)
            symbol - repeat of the symbol entered, taken from the response for validation
            open - opening price
            close - closing price
            high - daily high price
            low - daily low price
            volume - daily trading volume
    """
    params = {
        'function': 'TIME_SERIES_DAILY',
        'symbol': symbol,
        'outputsize': 'compact',
        'datatype': 'json',
        'apikey': API_KEY
    }
    response = requests.request('GET', url=url, params=params)
    if response.status_code != 200:
        print('bad response', response.status_code)
        return 0
    res = response.json()
    try:
        today = date.today().strftime('%Y-%m-%d')
        daily = res['Time Series (Daily)'][today]
    except KeyError:
        # if today does not exist as a key, try yesterday, if that doesn't work, give up.
        try:
            today = (date.today()-timedelta(1)).strftime('%Y-%m-%d')
            daily = res['Time Series (Daily)'][today]
        except KeyError:
            return 0

    daily_movement = {
        'date': today,
        'symbol': res['Meta Data']['2. Symbol'],
        'open': daily['1. open'],
        'close': daily['4. close'],
        'high': daily['2. high'],
        'low': daily['3. low'],
        'volume': daily['5. volume']
    }
    return daily_movement
