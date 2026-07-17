import os

# --- App route paths (used in @app.route decorators) ---
API_BASE = '/api'
API_AUTH_STATUS = f'{API_BASE}/auth/status'
API_LOGIN = f'{API_BASE}/login'
API_ME = f'{API_BASE}/me'
API_CALLBACK = f'{API_BASE}/callback'
API_GENERATE = f'{API_BASE}/generate'
API_ARTISTS = f'{API_BASE}/artists'
API_LOGOUT = f'{API_BASE}/logout'

# --- Spotify accounts service (OAuth: login + token exchange/refresh) ---
SPOTIFY_ACCOUNTS_BASE = 'https://accounts.spotify.com'
SPOTIFY_AUTHORIZE_URL = f'{SPOTIFY_ACCOUNTS_BASE}/authorize'
SPOTIFY_TOKEN_URL = f'{SPOTIFY_ACCOUNTS_BASE}/api/token'

# --- Spotify Web API (data endpoints) ---
SPOTIFY_API_BASE = 'https://api.spotify.com/v1'
SPOTIFY_SEARCH_URL = f'{SPOTIFY_API_BASE}/search'
SPOTIFY_ME_URL = f'{SPOTIFY_API_BASE}/me'
SPOTIFY_ARTISTS_URL = f'{SPOTIFY_API_BASE}/artists'


FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://127.0.0.1:5173')
SPOTIFY_REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI', 'http://127.0.0.1:5000/api/callback')