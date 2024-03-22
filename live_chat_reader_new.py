from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import time
import re
import homeassistant_desk_control
from datetime import datetime, timedelta
import data, plaque_borad_controller

API_KEY = data.API_KEY
VIDEO_ID = data.VIDEO_ID

YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'


def handle_desk_command(match, is_superchat, command_info, display_name):
    if match:
        desk_height = int(match.group(1))
        if 71 <= desk_height <= 110:
            print(f"{desk_height} is between 71 and 110. By user: {display_name}")
            command_info["last_used"] = datetime.now()  # Update the timeout start only if valid
        else:
            print(f"{desk_height} is not between 71 and 110. Command ignored, timeout not started. By user: {display_name}")


def handle_bubbles_command(match, is_superchat, command_info, display_name):
    print("Hello! This message is from: " + display_name)
    # Update the timeout start for commands without validation requirements
    command_info["last_used"] = datetime.now()


commands = {
    "!desk_": {"timeout": timedelta(minutes=5), "last_used": datetime.now() - timedelta(minutes=5), "action": handle_desk_command},
    "!bubbles": {"timeout": timedelta(minutes=5), "last_used": datetime.now() - timedelta(minutes=5), "action": handle_bubbles_command},
}

def get_live_chat_id(video_id):
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=API_KEY)
    request = youtube.videos().list(
        part='liveStreamingDetails',
        id=video_id
    )
    response = request.execute()

    liveChatId = response.get('items', [])[0].get('liveStreamingDetails', {}).get('activeLiveChatId')
    return liveChatId

def check_name_in_data(display_name):
    for person in data.supporter_data:
        if person['name'] == display_name:
            return person
    return None

def execute_command(command, message_text, is_superchat, display_name):
    cmd_info = commands[command]
    match = re.search(rf"{command}(\d+)", message_text)
    if command == "!bubbles" or match:  # Ensure match is checked for commands expecting parameters
        current_time = datetime.now()
        if is_superchat or (current_time - cmd_info["last_used"] >= cmd_info["timeout"]):
            cmd_info["action"](match, is_superchat, cmd_info, display_name)  # Include display_name in action call


def print_live_chat_messages(live_chat_id):
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=API_KEY)
    request = youtube.liveChatMessages().list(
        liveChatId=live_chat_id,
        part='id,snippet,authorDetails'
    )

    while True:
        response = request.execute()
        for item in response['items']:
            message_text = item['snippet']['displayMessage']
            display_name = item['authorDetails']['displayName']
            is_superchat = item['snippet'].get('superChatDetails') is not None
            print(f"{display_name}: {message_text} (Superchat: {is_superchat})")

            person_info = check_name_in_data(display_name)
            if person_info:
                plaque_borad_controller.set_leds(person_info['Leds'], person_info['Leds_colour'], 5)

        for command in message_text.split():
            if command in commands:
                execute_command(command, message_text, is_superchat, display_name)
        time.sleep(15)
        request = youtube.liveChatMessages().list_next(request, response)

if __name__ == '__main__':
    live_chat_id = get_live_chat_id(VIDEO_ID)
    if live_chat_id:
        print(f"Found live chat for video {VIDEO_ID}. Printing messages...")
    else:
        print("Live chat not found for this video.")
        pass
