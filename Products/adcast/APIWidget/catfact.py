from cached_request import request
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
    response = request('GET', url=url)
    if not isinstance(response, dict):
        if response.status_code != 200:
            return 0
        res = response.json()
        return res['all'][randint(0,len(res['all']))]['text']
    else: 
        return response['all'][randint(0,len(response['all']))]['text']

