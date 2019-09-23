import requests, os, json, hashlib

def request(verb, url, headers={}, params={}):
    checksum_name = hashlib.md5(url.encode('utf-8')).hexdigest()
    if not os.path.exists('./widgetfiles' + checksum_name):
        response = requests.request(verb, url, headers=headers, params=params)
        with open('./widgetfiles/' + checksum_name, 'w+') as f:
            json.dump(response.json(), f)
        return response
    else:
        print('getting cached response')
        with open('./widgetfiles' + checksum_name) as json_file:
            return json.load(json_file)
