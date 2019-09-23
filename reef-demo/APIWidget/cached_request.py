import requests, os, json

def request(verb, url, headers={}, params={}):
    if not os.path.exists('./widgetsfile'):
        response = requests.request(verb, url, headers=headers, params=params)
        with open('./widgetsfile', 'w+') as f:
            json.dump(response.json(), f)
        return response
    else:
        print('getting cached response')
        with open('widgetsfile') as json_file:
            return json.load(json_file)
