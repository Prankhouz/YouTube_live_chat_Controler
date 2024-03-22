from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import time
import re  # Import the regular expressions module
import homeassistant_desk_control
from datetime import datetime, timedelta
import data, plaque_borad_controller

API_KEY = data.API_KEY
VIDEO_ID = data.VIDEO_ID

YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'

# Initialize a list of commands or keywords to look for in chat messages
commands = ["!desk_"]
desk_timeouts = {"!desk_": datetime.now() - timedelta(minutes=5)}  # Initialize with a past time


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
            print(f"{item['authorDetails']['displayName']}: {message_text} (Superchat: {is_superchat})")

            person_info = check_name_in_data(display_name)
            if person_info:
                plaque_borad_controller.set_leds(person_info['Leds'], person_info['Leds_colour'],5)


            for command in commands:
                if command in message_text:
                    current_time = datetime.now()
                    superchat_bypass = is_superchat and command == "!desk_"

                    if (current_time - desk_timeouts[command] >= timedelta(minutes=5)) or superchat_bypass:
                        match = re.search(rf"{command}(\d+)", message_text)
                        if match:
                            print(f"Found the command {command} with number: {match.group(1)} in the message.")
                            if 71 <= int(match.group(1)) <= 110:
                                print(f"{int(match.group(1))} is between 71 and 110.")
                                homeassistant_desk_control.adjust_desk_height(int(match.group(1)))
                                desk_timeouts[command] = current_time
                            else:
                                print(f"{int(match.group(1))} is not between 71 and 110.")

        time.sleep(15)
        request = youtube.liveChatMessages().list_next(request, response)


if __name__ == '__main__':
    live_chat_id = get_live_chat_id(VIDEO_ID)
    if live_chat_id:
        print(f"Found live chat for video {VIDEO_ID}. Printing messages...")
        print_live_chat_messages(live_chat_id)
    else:
        print("Live chat not found for this video.")
