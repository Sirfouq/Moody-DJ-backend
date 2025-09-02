
import os
import requests

def spotify_access_token():
    client_id = os.getenv('CLIENT_ID')
    client_secret = os.getenv('CLIENT_SECRET')
    url = 'https://accounts.spotify.com/api/token'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    body={
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret
    }
    r = requests.post(url, headers=headers, data=body)
    print(type(r.json()))
    return r.json()['access_token']