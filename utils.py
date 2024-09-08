import json
import requests
from datetime import datetime
import pytz
from PIL import Image, ImageTk
from io import BytesIO
from dotenv import load_dotenv
import os

load_dotenv()

SPOTIFY_ID = os.getenv("SPOTIFY_ID")
SPOTIFY_SECRET = os.getenv("SPOTIFY_SECRET")
TOKEN_URL = 'https://accounts.spotify.com/api/token'

# Load the wmo_codes.json file
with open('wmo_codes.json', 'r') as file:
    wmo_codes = json.load(file)

# Function to load Spotify credentials
def load_spotify_credentials():
    with open('spotify_token', 'r') as file:
        credentials = json.load(file)
    return credentials

# Function to get weather description and image based on weather code
def get_weather_info(weather_code, is_day):
    code_info = wmo_codes.get(str(weather_code), {})
    period = 'day' if is_day == 1 else 'night'
    description = code_info.get(period, {}).get('description', 'No data')
    image_url = code_info.get(period, {}).get('image', '')
    return description, image_url

# Convert time to 24-hour format in Chicago timezone
def format_time(iso_time):
    tz = pytz.timezone('America/Chicago')
    utc_time = datetime.fromisoformat(iso_time.replace('Z', '+00:00'))
    local_time = utc_time.astimezone(tz)
    return local_time.strftime('%H:%M')

def refresh_spotify_token():
    creds = load_spotify_credentials()
    refresh_token = creds['refresh_token']

    # Request body for refreshing the token
    payload = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'client_id': SPOTIFY_ID,
        'client_secret': SPOTIFY_SECRET
    }

    # Make the request to refresh the token
    response = requests.post(TOKEN_URL, data=payload)

    if response.status_code == 200:
        new_token_data = response.json()

        # Update the credentials
        creds['access_token'] = new_token_data['access_token']
        creds['expires_in'] = new_token_data['expires_in']
        
        # If a new refresh token is returned, update it as well
        if 'refresh_token' in new_token_data:
            creds['refresh_token'] = new_token_data['refresh_token']

        # Save the updated credentials back to the file
        with open('spotify_token', 'w') as f:
            json.dump(creds, f, indent=4)

        print("Access token refreshed successfully!")
    else:
        print(f"Failed to refresh token. Status code: {response.status_code}, Response: {response.text}")


def get_current_track_info(headers):
    """Poll the Spotify API to check if a song is playing and get the album art, song name, and artist."""
    try:
        response = requests.get("https://api.spotify.com/v1/me/player", headers=headers)
        
        if response.status_code == 200:
            track_info = response.json()
            if track_info['is_playing']:
                album_art_url = track_info['item']['album']['images'][0]['url']
                song_name = track_info['item']['name']
                artist_name = ", ".join(artist['name'] for artist in track_info['item']['artists'])
                return album_art_url, song_name, artist_name, True
            else:
                return None, None, None, False
        elif response.status_code == 401:
            # Refresh the token
            refresh_spotify_token()

            # Load the new credentials and update the headers with the new access token
            creds = load_spotify_credentials()
            headers['Authorization'] = f"Bearer {creds['access_token']}"

            # Retry the request with the updated headers
            response = requests.get("https://api.spotify.com/v1/me/player", headers=headers)
            if response.status_code == 200:
                track_info = response.json()
                if track_info['is_playing']:
                    album_art_url = track_info['item']['album']['images'][0]['url']
                    song_name = track_info['item']['name']
                    artist_name = ", ".join(artist['name'] for artist in track_info['item']['artists'])
                    return album_art_url, song_name, artist_name, True
            else:
                print(f"Failed to fetch playback information after token refresh: {response.status_code}")
                return None, None, None, False
        else:
            print(f"Failed to fetch playback information: {response.status_code}")
            return None, None, None, False
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None, None, None, False


def show_album_art(album_label, img_data, player_width):
    """Display an image (album art or fallback) resized to fit the player_frame width."""
    img = Image.open(BytesIO(img_data)) if isinstance(img_data, bytes) else Image.open(img_data)
    img = img.resize((player_width, int(player_width * img.height / img.width)), Image.Resampling.LANCZOS)
    album_art_img = ImageTk.PhotoImage(img)
    album_label.config(image=album_art_img)
    album_label.image = album_art_img

def scroll_text(label, text):
    """Scroll the text horizontally if it's too long for the label, with extra spaces at the end."""
    text_with_spaces = text + "   "

    def update_text():
        nonlocal text_with_spaces
        label.config(text=text_with_spaces)
        text_with_spaces = text_with_spaces[1:] + text_with_spaces[0]  # Circular scrolling
        label.after(200, update_text)

    if len(text) > 20:
        update_text()

def update_album_art(headers, album_label, song_label, artist_label, play_pause_button):
    """Update the album art, song name, and artist in the player_frame if a song is playing, else show fallback."""
    album_art_url, song_name, artist_name, is_playing = get_current_track_info(headers)

    if album_art_url:
        response = requests.get(album_art_url)
        if response.status_code == 200:
            show_album_art(album_label, response.content, 200)
        else:
            show_album_art(album_label, 'spotify_logo.jpg', 200)
    else:
        show_album_art(album_label, 'spotify_logo.jpg', 200)

    if song_name and artist_name:
        song_label.config(text=song_name)
        artist_label.config(text=artist_name)
        scroll_text(song_label, song_name)
        scroll_text(artist_label, artist_name)
    else:
        song_label.config(text="No song playing")
        artist_label.config(text="")

    play_pause_button.config(text="Pause" if is_playing else "Play")

def skip_next(headers):
    """Skip to the next track."""
    requests.post("https://api.spotify.com/v1/me/player/next", headers=headers)

def skip_previous(headers):
    """Skip to the previous track."""
    requests.post("https://api.spotify.com/v1/me/player/previous", headers=headers)

def play_pause(headers, play_pause_button):
    """Toggle between play and pause."""
    current_state = play_pause_button['text']
    if current_state == "Play":
        requests.put("https://api.spotify.com/v1/me/player/play", headers=headers)
    else:
        requests.put("https://api.spotify.com/v1/me/player/pause", headers=headers)
