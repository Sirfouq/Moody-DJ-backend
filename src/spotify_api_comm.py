import os
import requests
import urllib.parse
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')


def spotify_access_token():
    
    url = 'https://accounts.spotify.com/api/token'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    body={
        'grant_type': 'client_credentials',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }
    r = requests.post(url, headers=headers, data=body)
    print(type(r.json()))
    return r.json()['access_token']

def authorize_user_request():
    url = 'https://accounts.spotify.com/authorize'
    params = {
        'client_id': CLIENT_ID,
        'redirect_uri': 'http://127.0.0.1:5000/api/callback',
        'response_type': 'code',
        'scope': 'playlist-modify-private playlist-modify-public'
    }
    auth_url = f"{url}?{urllib.parse.urlencode(params)}"
    return auth_url