import requests
from random import randint

url = 'https://cat-fact.herokuapp.com/facts'


def get_cat_fact():
    """
    Get random cat fact
    Args:
        None
    Returns:
        Random cat fact string
    """
    response = requests.request('GET', url=url)
    if response.status_code != 200:
        return 0
    res = response.json()
    return res['all'][randint(0,len(res['all']))]['text']
