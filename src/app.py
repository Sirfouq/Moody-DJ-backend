import os
import requests
import time
from src import config
from flask import Flask,jsonify,request,redirect ,session
from src.spotify_api_comm import authorize_user_request,request_api_token_request,return_token,request_generated_list
from src.openai_api_comm import search_query_layer

app = Flask(__name__)



app.secret_key = os.getenv('SECRET_KEY')
if not app.secret_key :
    raise RuntimeError('SECRET_KEY env variable is not set.')

IS_PRODUCTION = os.getenv('FLASK_ENV')== 'production' 

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=IS_PRODUCTION,
    SESSION_COOKIE_SAMESITE = 'Lax'
    )



@app.route('/')
def home():
    return redirect(f'{config.FRONTEND_URL}')

@app.route(config.API_AUTH_STATUS)
def auth_check_status():
    token = return_token()
    if token:
        return jsonify({'isLoggedIn': True, 'access_token': token})
    return jsonify({'isLoggedIn': False}), 401



@app.route(config.API_LOGIN, methods=['GET'])
def login():
    auth_url = authorize_user_request()
    return redirect(auth_url)

@app.route(config.API_LOGOUT,methods=['POST'])
def logout():
    session.clear()
    return jsonify({'isLoggedIn' : False})



@app.route(config.API_ME,methods = ['GET'])
def fetchProfile():
    token =  return_token()
    if not token : 
        return jsonify({'error': 'Not logged in'}),401
    request_params = {
        'url' : config.SPOTIFY_ME_URL,
        'headers' : {"Authorization" : f'Bearer {token}'}}
    response = requests.get(**request_params)
    return response.json(),response.status_code

@app.route(config.API_CALLBACK,methods = ['GET'])
def callback():
    state = request.args.get('state')
    if not state or state!= session.pop('oauth_state',None):
        return jsonify({'error' : 'Invalid state parameter'}),403
    if request.args.get('error'):
         return redirect(f'{config.FRONTEND_URL}?error=auth_denied')
    code = request.args.get('code')
    if not code:
        return redirect(f'{config.FRONTEND_URL}?error=missing_auth_code')
    
    req = request_api_token_request(code=code,redirect_uri=config.SPOTIFY_REDIRECT_URI)
    if 'access_token' not in req:
        return redirect(f'{config.FRONTEND_URL}?error=auth_failed')
    session['token_info'] = {
            'access_token' : req.get('access_token'),
            'expires_at' :time.time() +req.get('expires_in'),
            'scope' : req.get('scope'),
            'refresh_token' : req.get('refresh_token')
        }
    return redirect(config.FRONTEND_URL)


#****** FURTHER IMPLEMNTATIONS NEEDED FOR FINAL APP**********
@app.route(config.API_GENERATE,methods = ['POST'])
def generate_list():
    access_token = return_token()
    if not access_token:
        return jsonify({'error' : 'Not logged in'}),401
    data = request.json or {}
    user_input = (data.get('user_input') or '').strip()
    if not user_input or len(user_input) > 500:
        return jsonify({'error': 'Invalid input'}), 400
    genre = data.get('genre','')
    artist = data.get('artist','')
    search_queries = search_query_layer(user_input=user_input,
                                        genre=genre,
                                        artist=artist)
    results = request_generated_list(spotify_tracks_list=search_queries,
                                     access_token=access_token)
    return jsonify([track.model_dump() for track in results])

    
    

    
if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)    
        
       