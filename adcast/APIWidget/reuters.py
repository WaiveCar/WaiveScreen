import requests, os, json, hashlib
from xml.etree import ElementTree

url = 'http://feeds.reuters.com/Reuters/worldNews'

def get_reuters_stories():
    response = requests.request('GET', url=url)
    return [ {'title': x.text, 'image': None} for x in  ElementTree.fromstring(response.content).findall(".//item//title")]

