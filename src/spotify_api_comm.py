import os
import requests
import urllib.parse
import base64
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')


def spotify_client_access_token():
    
    url = 'https://accounts.spotify.com/api/token'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    body={
        'grant_type': 'client_credentials',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }
    req = requests.post(url, headers=headers, data=body)
    return req.json()['access_token']

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

def request_api_token_request(code : str , redirect_uri : str):
    auth_string = f'{CLIENT_ID}:{CLIENT_SECRET}'
    print(auth_string)
    auth_bytes = auth_string.encode('utf-8')
    auth_base64 = base64.b64encode(auth_bytes).decode('utf-8')
    url = 'https://accounts.spotify.com/api/token'
    headers = {
        'Authorization': f'Basic {auth_base64}',
        'Content-Type' : 'application/x-www-form-urlencoded' 

    }
    body = {
        'grant_type' : 'authorization_code',
        'code' : code,
        'redirect_uri' : redirect_uri
    }
    req = requests.post(url=url,headers=headers,data=body)
    return req.json()