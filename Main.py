import sqlite3
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import time
import threading
import Secrets
import CommandHandler
import plaque_borad_controller

def get_database_connection():
    connection = sqlite3.connect('database.db')
    return connection

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
    youtube = build('youtube', 'v3', developerKey=Secrets.API_KEY)
    request = youtube.liveChatMessages().list(liveChatId=live_chat_id, part='id,snippet,authorDetails')
    first_request = True
    while True:
        response = request.execute()
        if not first_request:
            for item in response['items']:
                message_text = item['snippet']['displayMessage']
                display_name = item['authorDetails']['displayName']
                is_superchat = item['snippet'].get('superChatDetails') is not None
                if is_superchat:
                    CommandHandler.handle_bubbles_command(None, is_superchat, CommandHandler.commands["!bubbles"], display_name)
                person_info = check_name_in_data(display_name)
                if person_info:
                    threading.Thread(target=plaque_borad_controller.set_leds, args=(person_info[2], person_info[1], 10)).start()
                for command in CommandHandler.commands.keys():
                    if command in message_text:
                        CommandHandler.execute_command(command, message_text, is_superchat, display_name, check_name_in_data)
                        break
        time.sleep(15)
        first_request = False
        request = youtube.liveChatMessages().list_next(request, response)

def get_live_chat_id(video_id):
    youtube = build('youtube', 'v3', developerKey=Secrets.API_KEY)
    request = youtube.videos().list(part='liveStreamingDetails', id=video_id)
    response = request.execute()
    liveChatId = response.get('items', [])[0].get('liveStreamingDetails', {}).get('activeLiveChatId')
    return liveChatId

if __name__ == '__main__':
    live_chat_id = get_live_chat_id(Secrets.VIDEO_ID)
    if live_chat_id:
        print(f"Found live chat for video {Secrets.VIDEO_ID}. Printing messages...")
        print_live_chat_messages(live_chat_id)
    else:
        print("Live chat not found for this video.")
