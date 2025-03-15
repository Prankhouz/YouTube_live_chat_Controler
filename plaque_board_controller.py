import requests
import time
import json
import os

SECRETS_FILE = 'secrets.json'

# Function to load data from JSON
def load_secrets():
    if not os.path.exists(SECRETS_FILE):
        return []  # Return empty list if file does not exist
    with open(SECRETS_FILE, "r") as file:
        return json.load(file)
        
def set_leds(led_indices, color, timehere):
    secrets = load_secrets()
    led_indices_new = list(map(int, led_indices.split(",")))
    api_endpoint = f"http://{secrets['board_ip']}/json/state"
    
    # If color is a string (e.g. "#FF0000"), remove the '#' and assign directly.
    # Otherwise, assume it is a tuple of integers.
    if isinstance(color, str):
        hex_color = color.lstrip('#').lower()
        if len(hex_color) != 6:
            raise ValueError("Invalid color string length, expected 6 hexadecimal digits")
    else:
        hex_color = '{:02x}{:02x}{:02x}'.format(*color)
    
    payload = {"seg": {"id": 0, "i": []}}

    # Construct the payload to set the color of each LED.
    for index in led_indices_new:
        payload["seg"]["i"].extend([index, hex_color])
    
    try:
        response = requests.post(api_endpoint, json=payload)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Failed to set color for LEDs {led_indices_new}. Error: {e}")
        return False
    else:
        pass

    time.sleep(timehere)

    payload = {"seg": {"id": 0, "frz": False}}
    try:
        response = requests.post(api_endpoint, json=payload)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return False
    else:
        return True

def set_leds_for_user(display_name, duration=3):
    """Trigger LEDs for a user based on their display name"""
    try:
        # Load plaques from file
        if os.path.exists('plaques.json'):
            with open('plaques.json', 'r') as f:
                plaques = json.load(f)
        else:
            return False

        # Find matching plaque
        matching_plaque = None
        for plaque in plaques:
            if plaque.get('YT_Name', '').lower() == display_name.lower():
                matching_plaque = plaque
                break

        if matching_plaque:
            # Get color and convert from hex if necessary
            color = matching_plaque.get('Leds_colour', '#FFFFFF')
            if isinstance(color, str):
                color = color  # Pass string directly to set_leds
            else:
                # If somehow not a string, ensure it's a tuple of ints
                color = tuple(color)
            
            # Get LED indices
            leds = matching_plaque.get('Leds', '')
            print(f"Triggering LEDs for {display_name} - Color: {color}, Leds: {leds}")
            
            # Trigger the LEDs
            return set_leds(leds, color, duration)
    except Exception as e:
        print(f"Error triggering LEDs for {display_name}: {e}")
        return False
