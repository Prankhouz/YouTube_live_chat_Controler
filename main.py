import json
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import time
import threading
import secrets
import commandhandler
import plaque_board_controller
from tts_module import gotts


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


def print_live_chat_messages(live_chat_id):
    youtube = build("youtube", "v3", developerKey=secrets.API_KEY)
    request = youtube.liveChatMessages().list(
        liveChatId=live_chat_id, part="id,snippet,authorDetails"
    )
    first_request = True
    while True:
        try:
            response = request.execute()
            if not first_request:
                for item in response["items"]:
                    message_text = item["snippet"]["displayMessage"]
                    display_name = item["authorDetails"]["displayName"]
                    is_superchat = item["snippet"].get("superChatDetails") is not None
                    print("User " + display_name + " just said: " + message_text)
                    ttstext = (display_name + " said: " + message_text)
                    gotts(ttstext)  # Queue the TTS

                    if is_superchat:
                        commandhandler.handle_bubbles_command(
                            None,
                            is_superchat,
                            commandhandler.commands["!bubbles"],
                            display_name,
                        )
                    person_info = check_name_in_data(display_name)
                    if person_info:
                        threading.Thread(
                            target=plaque_board_controller.set_leds,
                            args=(person_info["Leds"], person_info["Leds_colour"], 10),
                        ).start()
                    for command in commandhandler.commands.keys():
                        if command in message_text.lower():
                            commandhandler.execute_command(
                                command,
                                message_text,
                                is_superchat,
                                display_name,
                                check_name_in_data,
                            )
                            break
            time.sleep(5)
            first_request = False
            request = youtube.liveChatMessages().list_next(request, response)
        except HttpError as e:
            print(f"Error fetching live chat: {e}")
            time.sleep(10)  # Retry after a short delay


def get_live_chat_id(video_id):
    """
    Fetch the live chat ID for the given video using YouTube API.
    Falls back to API_KEY_Backup if the primary key fails.

    :param video_id: The ID of the YouTube video.
    :return: The live chat ID if found, or None otherwise.
    """
    api_keys = [secrets.API_KEY, secrets.API_KEY_Backup]
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


if __name__ == "__main__":
    try:
        live_chat_id = get_live_chat_id(secrets.VIDEO_ID)
        if live_chat_id:
            print(f"Found live chat for video {secrets.VIDEO_ID}. Printing messages...")
            print_live_chat_messages(live_chat_id)
        else:
            print("Live chat not found for this video.")
    except KeyboardInterrupt:
        print("Program interrupted by user.")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        print("Exiting program.")
