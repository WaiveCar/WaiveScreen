import requests, os, json

def request(verb, url):
    if not os.path.exists('./widgetsfile'):
        response = requests.request(verb, url)
        with open('./widgetsfile', 'w+') as f:
            json.dump(response.json(), f)
        return response
    else:
        print(os.open('./widgetsfile', os.O_RDONLY))
        with open('widgetsfile') as json_file:
            return json.load(json_file)
