import requests
from datetime import date, timedelta


def get_MLB_scores(day_offset=0):
    """
    Get Baseball Scores

    Args:
        day_offset: specifies which day's scores to get.  -1 = yesterday, 0 = today, 1 = tomorrow, etc...
            default = 0, yesterday

    Returns:
        0 on failed request
        daily games dictionary on success with the following keys:
            league - abbreviation of league (MLB)
            games - list of individual game dictionaries for the day. each dictionary may have the following keys:
                status - game status, ex: scheduled, inprogress, closed
                home - home team abbreviation
                away - away team abbreviation
                home_score - score for the home team
                away_score - score for the away team
                start_time - scheduled start date and time of the game
                if the game is in progress:
                    inning - current inning
                    top_bot - top or bottom of the inning, 'T' or 'B'
    """
    url = 'http://api.sportradar.us/mlb/trial/v6.5/en/games/'
    url_end = '/boxscore.json'
    api_key = 'ch4hcjs9qp4kt2xycshp8dva'
    target_date = date.strftime(date.today()+timedelta(int(day_offset)), '%Y/%m/%d')
    params = {
        'api_key': api_key
    }
    send_url = url+target_date+url_end
    print(send_url)
    response = requests.request('GET', url=send_url, params=params)
    if response.status_code != 200:
        return 0
    res = response.json()
    daily_games = {'league': res['league']['alias'],
                   'games': []}
    for game in res['league']['games']:
        lean_game = {
            'status': game['game']['status'],
            'home': game['game']['home']['abbr'],
            'home_score': game['game']['home']['runs'],
            'away': game['game']['away']['abbr'],
            'away_score': game['game']['away']['runs'],
            'start_time': game['game']['scheduled']
        }
        if lean_game['status'] == 'inprogress':
            lean_game['inning'] = game['game']['outcome']['current_inning']
            lean_game['top_bot'] = game['game']['outcome']['current_inning_half']
        daily_games['games'].append(lean_game)
    return daily_games


def get_NFL_scores(week, year=2019, sched='REG'):
    """
    Get NFL Scores

    Args: enter which season, schedule, and week to get nfl schedule and scores
        for example, get_NFL_scores(1, 2019, 'REG') returns the 2019 regular season week 1
        week = which week of the season
        year - year of the games
        sched - 'REG' = regular season, 'PRE' = preseason, 'POST' = postseason

    Returns:
        0 on failed request
        weekly games dictionary on success with the following keys:
            league - abbreviation of league (NFL)
            games - list of individual game dictionaries for the week. each dictionary may have the following keys:
                status - game status, ex: scheduled, inprogress, closed
                home - home team abbreviation
                away - away team abbreviation
                home_score - score for the home team
                away_score - score for the away team
                start_time - scheduled start date and time of the game

    """
    url = 'http://api.sportradar.us/nfl/official/trial/v5/en/games/'
    url_end = '/schedule.json'
    api_key = 'zr9t33tnnwmpkryg3xv75svd'
    sched_wk = str(year) + '/' + sched + '/' + str(week)
    params = {
        'api_key': api_key
    }
    send_url = url + sched_wk + url_end
    print(send_url)
    response = requests.request('GET', url=send_url, params=params)
    if response.status_code != 200:
        return 0
    res = response.json()
    daily_games = {
        'year': res['year'],
        'sched': res['type'],
        'week': res['week']['title'],
        'games': []
    }
    for game in res['week']['games']:
        lean_game = {
            'status': game['status'],
            'home': game['home']['alias'],
            'home_score': game['scoring']['home_points'],
            'away': game['away']['alias'],
            'away_score': game['scoring']['away_points'],
            'start_time': game['scheduled']
        }
        if lean_game['status'] == 'inprogress':
            print('YOU HAVE A GAME IN PROGRESS, CHECK NOW FOR HOW TO HANDLE')
        daily_games['games'].append(lean_game)
    return daily_games

