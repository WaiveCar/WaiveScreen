import requests

url = 'https://traffic.api.here.com/traffic/6.0/incidents.json'
APP_ID = '6da247D5KlUKVJgfiBM5'
APP_CODE = 'iBSSHQIsuGv8k0ICfSCECQ'


def get_traffic_incidents(lat, lon, radius=2, criticality=1):
    """
    Gets traffic incidents based on location, radius, and criticality.

    Args:
        lat: latitude as string or float
        lon: longitude as string or float
        radius: scan radius (in mi) as int or float
        criticality: lowest criticality returned
            0 - critical
            1 - major
            2 - minor
            3 - low impact

    Returns:
        0 on unsuccessful request
        List of Traffic incidents in format pulled.  Not easy to transmute into usable sentence so returning all.
    """
    crit = '0'
    for i in range(1, min(criticality, 3) + 1):
        crit += ',' + str(i)
    params = {
        'prox': str(lat) + ',' + str(lon) + ',' + str(int(radius*1600)),
        'criticality': '0,1',
        'app_id': APP_ID,
        'app_code': APP_CODE
    }
    response = requests.request('GET', url=url, params=params)
    if response.status_code != 200:
        return 0
    res = response.json()
    return res['TRAFFICITEMS']['TRAFFICITEM']
