from pprint import pprint

import requests

# res = requests.post('http://localhost:8000/register', json={'username': 'user1', 'password': '12345'})
# pprint(res.json())

res = requests.post('http://localhost:8000/token', data={'username': 'user1', 'password': '12345'})
pprint(res.json())

token = res.json()['access_token']

profile = requests.get('http://localhost:8000/profile', headers={'Authorization': f'Bearer {token}'})
pprint(profile.json())