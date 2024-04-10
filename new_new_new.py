from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import time
import re
import homeassistant_controls
from datetime import datetime, timedelta
import Secrets, plaque_borad_controller
import threading
import sqlite3

def get_database_connection():
    connection = sqlite3.connect('database.db')
    return connection

API_KEY = Secrets.API_KEY
VIDEO_ID = Secrets.VIDEO_ID

YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'

def handle_desk_command(match, is_superchat, command_info, display_name):
    print("desk! This message is from: " + display_name)
    if match:
        desk_height = int(match.group(1))
        if 71 <= desk_height <= 120:
            print(f"{desk_height} is between 71 and 110. By user: {display_name}")
            homeassistant_controls.adjust_desk_height(int(match.group(1)))
            command_info["last_used"] = datetime.now()  # Update the timeout start only if valid
        else:
            print(f"{desk_height} is not between 71 and 110. Command ignored, timeout not started. By user: {display_name}")

def handle_bubbles_command(match, is_superchat, command_info, display_name):
    print("Bubbles! This message is from: " + display_name)
    homeassistant_controls.Bubbles()
    command_info["last_used"] = datetime.now()  # Update the timeout start

access_hierarchy = ['regular', 'patron', 'superchat']

def check_access(user_status, command_level):
    # Get indices in the hierarchy, default to lowest access if not found
    user_level = access_hierarchy.index(user_status) if user_status in access_hierarchy else 0
    command_level_index = access_hierarchy.index(command_level) if command_level in access_hierarchy else 0

    return user_level >= command_level_index

def get_user_status(display_name, is_superchat):
    if is_superchat:
        return "superchat"
    elif check_name_in_data(display_name):
        return "patron"
    else:
        return "regular"

commands = {
    "!desk_": {
        "timeout": {"regular": timedelta(minutes=10), "patron": timedelta(minutes=3), "superchat": timedelta(seconds=0)},
        "access_level": "regular",
        "action": handle_desk_command
    },

    "!bubbles": {
        "timeout": {"regular": timedelta(minutes=10), "patron": timedelta(minutes=3), "superchat": timedelta(seconds=0)},
        "access_level": "patron",
        "action": handle_bubbles_command
    }
}

def execute_command(command_key, message_text, is_superchat, display_name):
    user_status = get_user_status(display_name, is_superchat)
    cmd_info = commands.get(command_key)

    if cmd_info:
        command_level = cmd_info["access_level"]
        if is_superchat or check_access(user_status, command_level):
            match = re.search(rf"{command_key}(\d+)", message_text)
            current_time = datetime.now()
            last_used = cmd_info.get("last_used", datetime.min)
            timeout = cmd_info["timeout"].get(user_status, timedelta(minutes=10))

            # Check timeout condition
            if is_superchat or (current_time - last_used >= timeout):
                # Call the action function associated with the command
                cmd_info["action"](match, is_superchat, cmd_info, display_name)
                cmd_info["last_used"] = current_time  # Update the last used time



def check_name_in_data(display_name):
    if not display_name:
        return None

    connection = get_database_connection()
    cursor = connection.cursor()
    
    cursor.execute("SELECT * FROM supporter_data WHERE YT_Name = ?", (display_name,))
    person = cursor.fetchone()
    
    cursor.close()
    connection.close()

    return person

def print_live_chat_messages(live_chat_id):
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=API_KEY)
    request = youtube.liveChatMessages().list(
        liveChatId=live_chat_id,
        part='id,snippet,authorDetails'
    )

    first_request = True  # Flag to check if it's the first request
    while True:
        response = request.execute()
        if not first_request:  # Skip processing for the first request
            for item in response['items']:
                message_text = item['snippet']['displayMessage']
                display_name = item['authorDetails']['displayName']
                is_superchat = item['snippet'].get('superChatDetails') is not None

                print(f"{display_name}: {message_text} (Superchat: {is_superchat})")
                
                if is_superchat:
                    handle_bubbles_command(None, is_superchat, commands["!bubbles"], display_name)


                person_info = check_name_in_data(display_name)
                if person_info:
                    print(person_info)
                    threading.Thread(
                        target=plaque_borad_controller.set_leds,
                        args=(person_info[2], person_info[1], 10)
                    ).start()

                for command in commands.keys():
                    if command in message_text:
                        execute_command(command, message_text, is_superchat, display_name)
                        break  # Assuming one command per message

        time.sleep(15)
        first_request = False
        request = youtube.liveChatMessages().list_next(request, response)

def get_live_chat_id(video_id):
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=API_KEY)
    request = youtube.videos().list(
        part='liveStreamingDetails',
        id=video_id
    )
    response = request.execute()

    liveChatId = response.get('items', [])[0].get('liveStreamingDetails', {}).get('activeLiveChatId')
    return liveChatId

if __name__ == '__main__':
    live_chat_id = get_live_chat_id(VIDEO_ID)
    if live_chat_id:
        print(f"Found live chat for video {VIDEO_ID}. Printing messages...")
        print_live_chat_messages(live_chat_id)
    else:
        print("Live chat not found for this video.")