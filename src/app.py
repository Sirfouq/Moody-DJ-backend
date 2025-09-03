import os
import requests
from flask import Flask,jsonify,request,redirect
from spotify_api_comm import spotify_access_token,authorize_user_request

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({"displayed_message": f"New Journey!!! Backend Working..."} )

# @app.route('/api/login', methods = ['POST'])
# def login():
#     return jsonify({"message": "{Login successful!}"})


@app.route('/api/artists/<artist_id>',methods = ['GET'])
def get_artist(artist_id):
    access_token = spotify_access_token()
    url = f'https://api.spotify.com/v1/artists/{artist_id}'
    headers = {"Authorization": f"Bearer {access_token}"}
    request= requests.get(url = url,headers= headers)
    return request.json()

@app.route('/api/login', methods=['GET'])
def login():
    auth_url = authorize_user_request()
    return redirect(auth_url)

# if __name__ == '__main__':
#     app.run(debug=True, port=5000)

