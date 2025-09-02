import os
import requests
from flask import Flask,jsonify,request 
from spotify_api_comm import spotify_access_token
app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({"displayed_message": f"New Journey!!! Backend Working..."} )

@app.route('/api/login', methods = ['POST'])
def login():
    return jsonify({"message": "{Login successful!}"})


@app.route('/api/artists/<artist_id>',methods = ['GET'])
def get_artist(artist_id):
    access_token = spotify_access_token()
    url = f'https://api.spotify.com/v1/artists/{artist_id}'
    headers = {"Authorization": f"Bearer {access_token}"}
    request= requests.get(url = url,headers= headers)
    return request.json()





