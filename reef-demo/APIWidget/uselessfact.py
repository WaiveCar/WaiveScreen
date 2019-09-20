import requests

url = 'https://uselessfacts.jsph.pl/random.json?language=en'


def get_random_fact():
    """
    Get a random fact

    Args:
        None
    Returns:
        0 on unsuccessful request
        fact dict on success with keys:
            fact - the fact
            source - source of the fact
    """
    response = requests.request('GET', url=url)
    if response.status_code != 200:
        return 0
    res = response.json()
    fact = {'fact': res['text'], 'source': res['source']}
    return fact
