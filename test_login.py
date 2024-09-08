from flask import Flask, request, redirect
from requests_oauthlib import OAuth2Session
from requests.auth import HTTPBasicAuth
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

AUTH_URL = 'https://accounts.spotify.com/authorize'
TOKEN_URL = 'https://accounts.spotify.com/api/token'
REDIRECT_URI = "http://localhost:8000/callback"
CLIENT_ID = os.getenv("SPOTIFY_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_SECRET")
SCOPE = [
    "user-read-playback-state user-modify-playback-state"
]


@app.route("/")
def login():
    spotify = OAuth2Session(CLIENT_ID, scope=SCOPE, redirect_uri=REDIRECT_URI)
    authorization_url, state = spotify.authorization_url(AUTH_URL)
    return redirect(authorization_url)

@app.route("/callback", methods=['GET'])
def callback():
    code = request.args.get('code')
    res = requests.post(TOKEN_URL,
        auth=HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET),
        data={
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': REDIRECT_URI
        })
    token_data = res.json()

    # Save token data in cookies
    with open("spotify_token", "w") as f:
        f.write(json.dumps(token_data))
    
    return "Done"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
