import json
import requests
from flask import Flask, request, render_template, redirect, url_for, jsonify
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from twitchio.ext import commands
import time
import os
import threading
import commandhandler
import plaque_board_controller
from tts_module import gotts
import app

def save_secrets(secrets):
    with open("secrets.json", 'w') as file:
        json.dump(secrets, file, indent=4)

def load_secrets():
    with open("secrets.json", 'r') as file:
        return json.load(file)

secrets = load_secrets()

def load_json_data():
    with open("plaques.json", "r") as file:
        return json.load(file)


def check_name_in_data(display_name):
    if not display_name:
        return None
    data = load_json_data()
    for person in data:
        if person["YT_Name"] == display_name or person.get("twitchusername") == display_name:
            return person
    return None

def handle_message(display_name, message_text, is_superchat=False):
    person_info = check_name_in_data(display_name)
    if person_info:
        threading.Thread(
            target=plaque_board_controller.set_leds_for_user,
            args=(person_info['name'], 5),  # Duration is set to 10 as in the original code
        ).start()

    iscommand = False
    commands = app.load_commands()
    for base_command in commands.keys():
        if base_command in message_text.lower():
            iscommand = True
            commandhandler.execute_command(
                message_text.lower(), display_name, is_superchat
            )
            break
    if message_text.lower().startswith("!dec"):
        dec_text = message_text[5:].strip()
        if dec_text:
            ttstext = f"{display_name} said: {dec_text}"
            threading.Thread(target=gotts, args=(ttstext,False,), daemon=True).start()
        return
    
    if not iscommand:
        ttstext = f"{display_name} said: {message_text}"
        threading.Thread(target=gotts, args=(ttstext,), daemon=True).start()



class TwitchBot(commands.Bot):
    def __init__(self, token, channel):
        super().__init__(token=token, prefix="!", initial_channels=[channel])

    async def event_ready(self):
        print(f"Logged in as {self.nick}")

    async def event_message(self, message):
        if message.author is None or message.author.name == self.nick:
            return
        handle_message(message.author.name, message.content)


def refresh_twitch_oauth_token(secrets):
    """
    Uses the stored refresh token to get a fresh access token,
    then writes both access_token and new refresh_token back to secrets.json.
    """
    client_id     = secrets.get("TWITCH_CLIENT_ID")
    client_secret = secrets.get("TWITCH_CLIENT_SECRET")
    refresh_token = secrets.get("TWITCH_REFRESH_TOKEN")
    if not (client_id and client_secret and refresh_token):
        print("Twitch OAuth refresh credentials missing, skipping refresh.")
        return secrets.get("TWITCH_OAUTH_TOKEN")

    url = "https://id.twitch.tv/oauth2/token"
    params = {
        "grant_type":    "refresh_token",
        "refresh_token": refresh_token,
        "client_id":     client_id,
        "client_secret": client_secret
    }

    resp = requests.post(url, params=params)
    if resp.status_code == 200:
        data = resp.json()
        new_access  = data["access_token"]
        new_refresh = data.get("refresh_token")
        print("✅ Twitch token refreshed successfully.")
        # update and persist
        secrets["TWITCH_OAUTH_TOKEN"]   = new_access
        if new_refresh:
            secrets["TWITCH_REFRESH_TOKEN"] = new_refresh
        save_secrets(secrets)
        return new_access
    else:
        print(f"❌ Failed to refresh Twitch token: {resp.status_code} {resp.text}")
        return secrets.get("TWITCH_OAUTH_TOKEN")

# Function to get live chat messages from YouTube and execute commands
def print_live_chat_messages(live_chat_id):
    secrets = load_secrets()
    youtube = build('youtube', 'v3', developerKey=secrets['api_key'])
    request = youtube.liveChatMessages().list(liveChatId=live_chat_id, part='id,snippet,authorDetails')
    first_request = True
    processed_message_ids = set()
    while True:
        try:
            response = request.execute()
            if not first_request:
                for item in response['items']:
                    notacommand = True
                    message_id = item['id']
                    if message_id in processed_message_ids:
                        continue
                    processed_message_ids.add(message_id)
                    message_text = item['snippet']['displayMessage']
                    display_name = item['authorDetails']['displayName']
                    is_superchat = item['snippet'].get('superChatDetails') is not None
                    handle_message(display_name, message_text, is_superchat)
            time.sleep(5)
            first_request = False
            request = youtube.liveChatMessages().list_next(request, response)
            if not request:
                print("No more live chat messages available.")
                break
        except HttpError as e:
            print(f"Error retrieving live chat messages: {e}")
            break

def get_live_video_id(api_key, channel_id):
    """
    Fetches the active live video ID from a given YouTube channel.
    Returns None if no live stream is found.
    """
    try:
        youtube = build("youtube", "v3", developerKey=api_key)
        request = youtube.search().list(
            part="id",
            channelId=channel_id,
            eventType="live",  # Only active live streams
            type="video",
            maxResults=1
        )
        response = request.execute()

        if "items" in response and len(response["items"]) > 0:
            return response["items"][0]["id"]["videoId"]
    except HttpError as e:
        print(f"Error fetching live video ID: {e}")
    
    return None  # No live video found

def get_live_chat_id(video_id, secrets):
    """
    Fetch the live chat ID for the given video.
    Falls back to API_KEY_Backup if the primary key fails.
    """
    api_keys = [secrets['api_key'], secrets['api_key_backup']]
    last_exception = None

    for api_key in api_keys:
        try:
            youtube = build("youtube", "v3", developerKey=api_key)
            request = youtube.videos().list(part="liveStreamingDetails", id=video_id)
            response = request.execute()

            live_chat_id = (
                response.get("items", [])[0]
                .get("liveStreamingDetails", {})
                .get("activeLiveChatId")
            )

            if live_chat_id:
                #print(f"Successfully retrieved live chat ID using API key: {api_key}")
                return live_chat_id

        except HttpError as e:
            last_exception = e
            #print(f"API key {api_key} failed with error: {e}")
        except Exception as e:
            last_exception = e
            #print(f"Unexpected error with API key {api_key}: {e}")

    # If all API keys fail
    if last_exception:
        print(f"All API keys failed. Last error: {last_exception}")
    
    return None

def input_with_timeout(prompt, timeout=10):
    result = [None]

    def get_input():
        result[0] = input(prompt).strip()

    input_thread = threading.Thread(target=get_input)
    input_thread.daemon = True
    input_thread.start()
    input_thread.join(timeout)
    
    if input_thread.is_alive():
        print("\nTimeout reached. Continuing...")
        return None
    return result[0]

def start_twitch_app():
    bot.run()
    pass

if __name__ == '__main__':
    if not os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        secrets = load_secrets()
        
        refreshed_token = refresh_twitch_oauth_token(secrets)
        secrets["TWITCH_OAUTH_TOKEN"] = refreshed_token
        print(refreshed_token)

        # Try to get an active live video ID automatically
        video_id = get_live_video_id(secrets['api_key'], secrets['channel_id'])

        if not video_id:
            print("No active live stream found.")
            video_id = input_with_timeout("Please enter a video ID manually: ", timeout=10)

        if not video_id:
            print("No valid video ID provided.")
            

        live_chat_id = get_live_chat_id(video_id, secrets)

        if live_chat_id:
            print(f"Found live chat for video {video_id}. Printing messages...")
            threading.Thread(target=print_live_chat_messages, args=(live_chat_id,), daemon=True).start()
        else:
            print("Live chat not found for this video. Disable Youtube Chat.")

        # Start Twitch bot
        bot = TwitchBot(refreshed_token, secrets["TWITCH_CHANNEL"])
        threading.Thread(target=start_twitch_app, args=(), daemon=True).start()
    # Run the Flask app
    # app = Flask(__name__)
    # app.secret_key = 'supersecretkey'
    app.run()
