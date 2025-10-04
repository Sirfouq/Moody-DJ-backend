import os
import requests
import time
from flask import Flask,jsonify,request,redirect,render_template ,session, url_for
from flask_cors import CORS
from spotify_api_comm import spotify_client_access_token,authorize_user_request,request_api_token_request,refresh_api_token_request

app = Flask(__name__)
CORS(app=app)

app.secret_key = os.getenv('SECRET_KEY')

@app.route('/')
def home():
    return render_template('basic_login.html')

# @app.route('/api/login', methods = ['POST'])
# def login():
#     return jsonify({"message": "{Login successful!}"})
@app.route('/api/auth/status')
def status_check():
    token_info = session.get('token_info')
    if not token_info:
        return redirect(url_for('home'))
    now = time.time()
    is_expired = token_info.get('expires_at',0) < now
    if(is_expired):
        refresh_token = token_info.get('refresh_token')
        refresh_token_request = refresh_api_token_request(refresh_token=refresh_token)
        try:
            session['token_info'] = {
            'access_token' : refresh_token_request.get('access_token'),
            'expires_at' : now + refresh_token_request.get('expires_in'),
            'scope' : refresh_token_request.get('scope'),
            'refresh_token': refresh_token_request.get('refresh_token') or token_info.get('refresh_token')
            }
            return jsonify({'message': 'Token has been refreshed successfully.'})
        except:
            session.clear()
            return render_template('error.html')
    return jsonify({'status':'200','message':'You are logged in and your token is valid!'})
            

    



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



@app.route('/api/callback',methods = ['GET'])
def callback():
    error = request.args.get('error')
    state = request.args.get('state')
    code = request.args.get('code')
    if error:
         return render_template('error.html')
    elif code:
        req = request_api_token_request(code=code,redirect_uri='http://127.0.0.1:5000/api/callback')
        session['token_info'] = {
            'access_token' : req.get('access_token'),
            'expires_at' :time.time() +req.get('expires_in'),
            'scope' : req.get('scope'),
            'refresh_token' : req.get('refresh_token')
        }
        print({'Stored token' : session['token_info']})
        return redirect(url_for('status_check'))
    
if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)    
        
       