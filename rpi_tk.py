import tkinter as tk
from tkinter import Label, Frame, Button
from utils import (
    load_spotify_credentials,
    get_weather_info,
    format_time,
    update_album_art,
    skip_next,
    skip_previous,
    play_pause,
)
import requests
from PIL import Image, ImageTk
import io

# Load the JSON from the token file
credentials = load_spotify_credentials()
ACCESS_TOKEN = credentials["access_token"]

# Spotify API headers
headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}"
}

# Define constants
WINDOW_WIDTH = 480
WINDOW_HEIGHT = 320
WEATHER_FRAME_WIDTH = 280
WEATHER_FRAME_HEIGHT = WINDOW_HEIGHT
BORDER_WIDTH = 2
IMAGE_SIZE = 50  # Size for the weather icon
TEMP_FONT_SIZE = 10  # Font size for max and min temperatures
SPACING = 2  # Reduced padding between rows
TIME_FONT_SIZE = 10  # Font size for the time label
BOTTOM_PADDING = 10  # Padding to add at the bottom of the bottom_frame

# Fetch weather data
response = requests.get("https://api.open-meteo.com/v1/forecast?latitude=41.80968&longitude=-87.5968&current=temperature_2m,relative_humidity_2m,apparent_temperature,is_day,precipitation,rain,showers,snowfall,weather_code,cloud_cover,wind_speed_10m,wind_direction_10m,wind_gusts_10m&daily=weather_code,temperature_2m_max,temperature_2m_min,sunrise,sunset,daylight_duration,precipitation_hours&timezone=America%2FChicago&forecast_days=1")
weather_data = response.json()
current_weather = weather_data['current']
daily_weather = weather_data['daily']

# Get weather description and image URL
description, image_url = get_weather_info(current_weather['weather_code'], current_weather['is_day'])

# Create the main window
root = tk.Tk()
root.attributes('-fullscreen',True)
root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
root.resizable(False, False)

# Create the weather_frame with fixed size
weather_frame = Frame(root, width=WEATHER_FRAME_WIDTH, height=WEATHER_FRAME_HEIGHT, bg="black", bd=BORDER_WIDTH, relief="solid")
weather_frame.place(x=WINDOW_WIDTH-WEATHER_FRAME_WIDTH, y=0, width=WEATHER_FRAME_WIDTH, height=WEATHER_FRAME_HEIGHT)

# Create a subframe for the last four rows
bottom_frame = Frame(weather_frame, bg="black")
bottom_frame.grid(row=7, column=0, columnspan=3, sticky='ew')

# Display 24hr data
time_label = Label(weather_frame, text=f"{format_time(current_weather['time'])}hrs", bg="black", fg="lightgrey", font=("Helvetica", TIME_FONT_SIZE), anchor='e')
time_label.grid(row=0, column=2, padx=(0, SPACING), pady=SPACING, sticky='e')

# Display weather image
if image_url:
    response = requests.get(image_url)
    img_data = response.content
    image = Image.open(io.BytesIO(img_data))
    image = image.resize((IMAGE_SIZE, IMAGE_SIZE))
    photo = ImageTk.PhotoImage(image)
    image_label = Label(weather_frame, image=photo, bg="black")
    image_label.image = photo
    image_label.grid(row=1, column=0, padx=SPACING, pady=SPACING, rowspan=2)

# Display current temperature
temp_label = Label(weather_frame, text=f"{current_weather['temperature_2m']} °C", bg="black", fg="white", font=("Helvetica", 16, "bold"))
temp_label.grid(row=1, column=1, padx=SPACING, pady=SPACING)

# Display weather description
description_label = Label(weather_frame, text=description, bg="black", fg="lightgrey", font=("Helvetica", 10))
description_label.grid(row=2, column=1, padx=SPACING, pady=SPACING)

# Display max and min temperatures horizontally
temp_max_label = Label(weather_frame, text=f"🔺 {daily_weather['temperature_2m_max'][0]} °C", bg="black", fg="lightgrey", font=("Helvetica", TEMP_FONT_SIZE))
temp_min_label = Label(weather_frame, text=f"🔻 {daily_weather['temperature_2m_min'][0]} °C", bg="black", fg="lightgrey", font=("Helvetica", TEMP_FONT_SIZE))
temp_max_label.grid(row=3, column=1, padx=SPACING, pady=SPACING, sticky='w')
temp_min_label.grid(row=3, column=2, padx=SPACING, pady=SPACING, sticky='w')

# Display daylight duration with 'Daylight' text
daylight_duration_hours = round(daily_weather['daylight_duration'][0] / 3600, 2)
daylight_label = Label(weather_frame, text=f"{daylight_duration_hours} hrs Daylight", bg="black", fg="white", font=("Helvetica", 12))
daylight_label.grid(row=4, column=1, padx=SPACING, pady=SPACING, columnspan=2)

# Move sunrise and sunset times to bottom_frame
sunrise_time = format_time(daily_weather['sunrise'][0])
sunset_time = format_time(daily_weather['sunset'][0])
sunrise_label = Label(bottom_frame, text=sunrise_time, bg="black", fg="white", font=("Helvetica", 12))
sunset_label = Label(bottom_frame, text=sunset_time, bg="black", fg="white", font=("Helvetica", 12))
sunrise_label.grid(row=0, column=0, padx=SPACING, pady=SPACING)
sunset_label.grid(row=0, column=1, padx=SPACING, pady=SPACING)

# Display 'Sunrise' and 'Sunset' text in bottom_frame
sunrise_text_label = Label(bottom_frame, text="Sunrise", bg="black", fg="lightgrey", font=("Helvetica", 10))
sunset_text_label = Label(bottom_frame, text="Sunset", bg="black", fg="lightgrey", font=("Helvetica", 10))
sunrise_text_label.grid(row=1, column=0, padx=(0, SPACING), pady=(0, SPACING))
sunset_text_label.grid(row=1, column=1, padx=(0, SPACING), pady=(0, SPACING))

# Move precipitation and related labels to bottom_frame
precipitation_label = Label(bottom_frame, text=f"{current_weather['precipitation']} mm", bg="black", fg="white", font=("Helvetica", 12))
precipitation_hours_label = Label(bottom_frame, text=f"{daily_weather['precipitation_hours'][0]} h", bg="black", fg="white", font=("Helvetica", 12))
precipitation_label.grid(row=2, column=0, padx=SPACING, pady=SPACING, sticky='w')
precipitation_hours_label.grid(row=2, column=1, padx=SPACING, pady=SPACING, sticky='w')

# Display 'Current PP' and 'PP Hours' text in bottom_frame
current_pp_label = Label(bottom_frame, text="Current PP", bg="black", fg="lightgrey", font=("Helvetica", 10))
pp_hours_label = Label(bottom_frame, text="PP Hours", bg="black", fg="lightgrey", font=("Helvetica", 10))
current_pp_label.grid(row=3, column=0, padx=(0, SPACING), pady=(0, SPACING), sticky='w')
pp_hours_label.grid(row=3, column=1, padx=(0, SPACING), pady=(0, SPACING), sticky='w')

# Ensure bottom_frame is centered at the bottom of weather_frame with padding
bottom_frame.update_idletasks()
bottom_frame_width = bottom_frame.winfo_width()
bottom_frame_height = bottom_frame.winfo_height()
weather_frame.update_idletasks()
weather_frame_width = weather_frame.winfo_width()

# Set position of bottom_frame
bottom_frame.place(x=(weather_frame_width - bottom_frame_width) // 2, y=WEATHER_FRAME_HEIGHT - bottom_frame_height - BOTTOM_PADDING, anchor='nw')

# Create a frame for the Spotify player
player_frame = Frame(root, bg="black")
player_frame.place(x=0, y=0, width=WINDOW_WIDTH-WEATHER_FRAME_WIDTH, height=WINDOW_HEIGHT)

# Create album art label
album_label = Label(player_frame, bg="black")
album_label.pack()

# Create labels for song and artist
song_label = Label(player_frame, text="No song playing", bg="black", fg="white", font=("Helvetica", 16))
song_label.pack()
artist_label = Label(player_frame, text="", bg="black", fg="lightgrey", font=("Helvetica", 12))
artist_label.pack()

# Create skip previous button
skip_previous_button = tk.Button(player_frame, text="Previous", command=lambda: skip_previous(headers), bg="grey", fg="white")
skip_previous_button.pack(side='left')

# Create play/pause button
play_pause_button = tk.Button(player_frame, text="Play", command=lambda: play_pause(headers, play_pause_button), bg="grey", fg="white")
play_pause_button.pack(side='left')

# Create skip next button
skip_next_button = tk.Button(player_frame, text="Next", command=lambda: skip_next(headers), bg="grey", fg="white")
skip_next_button.pack(side='left')

# Create close button
close_button = Button(root, text="X", command=root.destroy, bg="red", fg="white", font=("Helvetica", 12, "bold"))
close_button.place(x=WINDOW_WIDTH - 30, y=5, width=25, height=25)

# Update album art and track info every 5 seconds
def update():
    update_album_art(headers, album_label, song_label, artist_label, play_pause_button)
    root.after(5000, update)

update()

# Start the Tkinter main loop
root.mainloop()
