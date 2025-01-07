import json
from flask import Flask, request, render_template, redirect, url_for, jsonify
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import time
import logging
import threading
import commandhandler
import plaque_board_controller
from tts_module import gotts
import app

SECRETS_FILE = 'secrets.json'
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

def load_secrets():
    with open(SECRETS_FILE, 'r') as file:
        return json.load(file)

secrets = load_secrets()

def load_json_data():
    with open("data.json", "r") as file:
        return json.load(file)


def check_name_in_data(display_name):
    if not display_name:
        return None
    data = load_json_data()
    for person in data:
        if person["YT_Name"] == display_name:
            return person
    return None


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
                    print("User " + display_name + " just said: " + message_text)
                    
                    if is_superchat:
                        # Handle bubbles command for superchat
                        commandhandler.execute_command("!bubbles", display_name, is_superchat=True)

                    # Check if user is in database
                    person_info = check_name_in_data(display_name)
                    if person_info:
                        # Start thread to run plaque_board_controller.set_leds
                        threading.Thread(target=plaque_board_controller.set_leds, args=(person_info[2], person_info[1], 10)).start()

                    # Handle commands
                    commands = app.load_commands()
                    for base_command in commands.keys():
                        if base_command in message_text.lower():
                            commandhandler.execute_command(message_text.lower(), display_name, is_superchat)
                            notacommand = False
                            break
                            
                    if notacommand:
                        ttstext = (display_name + " said: " + message_text)
                        gotts(ttstext)  # Queue the TTS
            time.sleep(5)
            first_request = False
            request = youtube.liveChatMessages().list_next(request, response)
            if not request:
                print("No more live chat messages available.")
                break
        except HttpError as e:
            print(f"Error retrieving live chat messages: {e}")
            break


def get_live_chat_id(video_id):
    """
    Fetch the live chat ID for the given video using YouTube API.
    Falls back to API_KEY_Backup if the primary key fails.

    :param video_id: The ID of the YouTube video.
    :return: The live chat ID if found, or None otherwise.
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
                print(f"Successfully retrieved live chat ID using API key: {api_key}")
                return live_chat_id
        except HttpError as e:
            last_exception = e
            print(f"API key {api_key} failed with error: {e}")
        except Exception as e:
            last_exception = e
            print(f"Unexpected error with API key {api_key}: {e}")

    # If all API keys fail
    if last_exception:
        print(f"All API keys failed. Last error: {last_exception}")
    return None

import os


if __name__ == '__main__':
    if not os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        secrets = load_secrets()
        live_chat_id = get_live_chat_id(secrets['video_id'])
        try:
            if live_chat_id:
                print(f"Found live chat for video {secrets['video_id']}. Printing messages...")
                # Run print_live_chat_messages in a separate thread
                threading.Thread(target=print_live_chat_messages, args=(live_chat_id,), daemon=True).start()
            else:
                print("Live chat not found for this video.")
        except KeyboardInterrupt:
            print("Program interrupted by user.")
        except Exception as e:
            print(f"Unexpected error: {e}")
        finally:
            print("Exiting program.")

    # Run the Flask app
    #app = Flask(__name__)
    #app.secret_key = 'supersecretkey'
    app.run()
