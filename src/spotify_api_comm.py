import os
import requests
import urllib.parse
import base64
import time
from flask import session
from src.util.searchQueryModel import SearchQuery
from openai_api_comm import search_query_layer
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')


def access_client_token():
    
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
    scopes = ['playlist-read-private',
        'playlist-modify-private',
        'playlist-modify-public',
        'streaming',
        'user-read-playback-state',
        'user-modify-playback-state',
        'user-read-currently-playing',
        'user-top-read',
]
    url = 'https://accounts.spotify.com/authorize'
    params = {
        'client_id': CLIENT_ID,
        'redirect_uri': 'http://127.0.0.1:5000/api/callback',
        'response_type': 'code',
        'scope': ' '.join(scopes)

    }
    auth_url = f"{url}?{urllib.parse.urlencode(params)}"
    return auth_url

def request_api_token_request(code : str , redirect_uri : str):
    auth_string = f'{CLIENT_ID}:{CLIENT_SECRET}'
    # print(auth_string)
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

def refresh_api_token_request(refresh_token :str):
    auth_string = f'{CLIENT_ID}:{CLIENT_SECRET}'
    # print(auth_string)
    auth_bytes = auth_string.encode('utf-8')
    auth_base64 = base64.b64encode(auth_bytes).decode('utf-8')
    url = 'https://accounts.spotify.com/api/token'
    headers = {
        'Authorization': f'Basic {auth_base64}',
        'Content-Type' : 'application/x-www-form-urlencoded' 
    }

    body = {
        'grant_type':'refresh_token',
        'refresh_token' : refresh_token
    }

    req = requests.post(url=url,headers=headers,data=body)
    return req.json()

def request_generated_list(spotify_tracks_list : list[SearchQuery]):
    pass
    


def check_status():
    token_info = session.get('token_info')
    if not token_info:
        return None
    now = time.time()
    is_expired = token_info.get('expires_at',0) < now
    if(is_expired):
        refresh_token = token_info.get('refresh_token')
        try:
            refresh_token_request = refresh_api_token_request(refresh_token=refresh_token)
            session['token_info'] = {
            'access_token' : refresh_token_request.get('access_token'),
            'expires_at' : now + refresh_token_request.get('expires_in'),
            'scope' : refresh_token_request.get('scope'),
            'refresh_token': refresh_token_request.get('refresh_token') or token_info.get('refresh_token')
            }   
        except:
            session.clear()
            return None
    return session['token_info'].get('access_token')    
