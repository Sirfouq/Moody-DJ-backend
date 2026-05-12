import os
import requests
import time
from flask import Flask,jsonify,request,redirect,render_template ,session, url_for
from flask_cors import CORS
from spotify_api_comm import access_client_token,authorize_user_request,request_api_token_request,return_token,request_generated_list
from openai_api_comm import search_query_layer
app = Flask(__name__)
CORS(app=app,
     supports_credentials=True,
     origins=['http://127.0.0.1:5173'],)

app.secret_key = os.getenv('SECRET_KEY')



@app.route('/')
def home():
    return render_template('basic_login.html')

@app.route('/api/auth/status')
def auth_check_status():
    token = return_token()
    if token:
        return jsonify({'isLoggedIn': True, 'access_token': token})
    return jsonify({'isLoggedIn': False}), 401

@app.route('/api/artists/<artist_id>',methods = ['GET'])
def get_artist(artist_id):
    access_token = access_client_token()
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
        return redirect('http://127.0.0.1:5173')


#****** FURTHER IMPLEMNTATIONS NEEDED FOR FINAL APP**********
@app.route('/api/generate',methods = ['POST'])
def generate_list():
    access_token = return_token()
    data = request.json
    user_input = data.get('user_input')
    genre = data.get('genre','')
    artist = data.get('artist','')
    if not access_token:
        return jsonify({'error' : 'Not logged in'}),401
    search_queries = search_query_layer(user_input=user_input,
                                        genre=genre,
                                        artist=artist)
    results = request_generated_list(spotify_tracks_list=search_queries,
                                     access_token=access_token)
    return jsonify([track.model_dump() for track in results])

    
    

    
if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)    
        
       