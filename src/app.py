import os
import requests
from flask import Flask,jsonify,request 
app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({"displayed_message": f"New Journey!!! Backend Working..."} )

@app.route('/api/login', methods = ['POST'])
def login():
    return jsonify({"message": "{Login successful!}"})


@app.route('/api/artists/<artist_id>',methods = ['GET'])
def get_artist(artist_id):
    access_token = get_access_token()
    url = f'https://api.spotify.com/v1/artists/{artist_id}'
    headers = {"Authorization": f"Bearer {access_token}"}
    request= requests.get(url = url,headers= headers)
    return request.json()


def get_access_token():
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



