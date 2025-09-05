import os
import requests
from flask import Flask,jsonify,request,redirect,render_template ,session
from spotify_api_comm import spotify_client_access_token,authorize_user_request,request_api_token_request

app = Flask(__name__)

app.secret_key = os.getenv('SECRET_KEY')

@app.route('/')
def home():
    return render_template('basic_login.html')

# @app.route('/api/login', methods = ['POST'])
# def login():
#     return jsonify({"message": "{Login successful!}"})


@app.route('/api/artists/<artist_id>',methods = ['GET'])
def get_artist(artist_id):
    access_token = spotify_client_access_token()
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

@app.route('/api/callback')
def callback():
    error = request.args.get('error')
    state = request.args.get('state')
    code = request.args.get('code')
    if error:
         return render_template('error.html')
    elif code:
        req = request_api_token_request(code=code,redirect_uri='http://127.0.0.1:5000/api/callback')
        session['token_obj'] = {
            'access_token' : req.get('access_token'),
            'expires_in' : req.get('expires_in'),
            'scope' : req.get('scope')
        }
        
        return jsonify('Stored token :', session['token_obj'])
    
    
        
       