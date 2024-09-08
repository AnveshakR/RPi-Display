import json
import requests
from datetime import datetime
import pytz
from PIL import Image, ImageTk
from io import BytesIO
import base64

# Load the wmo_codes.json file
with open('wmo_codes.json', 'r') as file:
    wmo_codes = json.load(file)

# Function to load Spotify credentials
def load_spotify_credentials():
    with open('spotify_token', 'r') as file:
        credentials = json.load(file)
    return credentials

def refresh_access_token():
    """Use the refresh token to get a new access token."""
    credentials = load_spotify_credentials()
    REFRESH_TOKEN = credentials["refresh_token"]
    SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
    CLIENT_ID = credentials["client_id"]
    CLIENT_SECRET = credentials["client_secret"]

    headers = {
        "Authorization": f"Basic {base64.b64encode(f'{CLIENT_ID}:{CLIENT_SECRET}'.encode()).decode()}"
    }
    data = {
        "grant_type": "refresh_token",
        "refresh_token": REFRESH_TOKEN
    }
    
    response = requests.post(SPOTIFY_TOKEN_URL, headers=headers, data=data)
    if response.status_code == 200:
        new_credentials = response.json()
        ACCESS_TOKEN = new_credentials["access_token"]
        with open('spotify_token', 'w') as file:
            json.dump({"access_token": ACCESS_TOKEN, "refresh_token": REFRESH_TOKEN, "client_id": CLIENT_ID, "client_secret": CLIENT_SECRET}, file)
        return ACCESS_TOKEN
    else:
        print("Failed to refresh access token")
        return None

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
