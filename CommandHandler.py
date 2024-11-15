import re
from datetime import datetime, timedelta
import homeassistant_controls
import sound_borad

access_hierarchy = ['regular', 'patron', 'superchat']

def check_access(user_status, command_level):
    user_level = access_hierarchy.index(user_status) if user_status in access_hierarchy else 0
    command_level_index = access_hierarchy.index(command_level) if command_level in access_hierarchy else 0
    return user_level >= command_level_index

def handle_desk_command(match, is_superchat, command_info, display_name):
    print("Desk command received! From: " + display_name)
    if match:
        desk_height = int(match.group(1))
        if 71 <= desk_height <= 120:
            print(f"Adjusting desk height to {desk_height} as requested by {display_name}.")
            #homeassistant_controls.adjust_desk_height(desk_height)
            command_info["last_used"] = datetime.now()
        else:
            print(f"Desk height {desk_height} out of range. Command ignored.")

def handle_bubbles_command(match, is_superchat, command_info, display_name):
    print("Bubbles command activated by " + display_name)
    homeassistant_controls.Bubbles()
    command_info["last_used"] = datetime.now()

def handle_sound_command(match, is_superchat, command_info, display_name):
    if match:
        sound_effect = match.group(1)
        print(sound_effect)
        print(f"Playing sound: {sound_effect} for {display_name}")
        # Assuming a function `play_sound` that plays the sound effect
        sound_borad.play_sound(sound_effect)
        command_info["last_used"] = datetime.now()


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
    },
    "!sound_": {
        "timeout": {"regular": timedelta(minutes=0), "patron": timedelta(minutes=0), "superchat": timedelta(seconds=0)},
        "access_level": "patron",
        "action": handle_sound_command
    }
}

def execute_command(command_key, message_text, is_superchat, display_name, check_name_in_data):
    user_status = get_user_status(display_name, is_superchat, check_name_in_data)
    cmd_info = commands.get(command_key)
    if cmd_info:
        command_level = cmd_info["access_level"]
        if is_superchat or check_access(user_status, command_level):
            # Adjust the regex pattern to match commands like !Sound_boo, !Sound_clap
            match = re.search(rf"{command_key}(\w+)", message_text)
            current_time = datetime.now()
            last_used = cmd_info.get("last_used", datetime.min)
            timeout = cmd_info["timeout"].get(user_status, timedelta(minutes=10))
            if is_superchat or (current_time - last_used >= timeout):
                cmd_info["action"](match, is_superchat, cmd_info, display_name)
                cmd_info["last_used"] = current_time

def get_user_status(display_name, is_superchat, check_name_in_data):
    if is_superchat:
        return "superchat"
    elif check_name_in_data(display_name):
        return "patron"
    else:
        return "regular"
