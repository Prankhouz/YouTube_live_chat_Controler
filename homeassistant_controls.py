import requests
import time
import json
import os

# Load secrets from the JSON file
SECRETS_FILE = 'secrets.json'

def load_secrets():
    if not os.path.exists(SECRETS_FILE):
        raise FileNotFoundError(f"Secrets file '{SECRETS_FILE}' not found.")
    with open(SECRETS_FILE, 'r') as file:
        return json.load(file)

# Load secrets
secrets = load_secrets()

# Home Assistant details
ACCESS_TOKEN = secrets['access_token']
HA_URL = secrets['ha_url']
HEADERS = {
    'Authorization': f'Bearer {ACCESS_TOKEN}',
    'Content-Type': 'application/json',
}

def call_ha_service(service, data):
    url = f"{HA_URL}/api/services/{service}"
    response = requests.post(url, headers=HEADERS, json=data)
    if response.status_code == 200:
        print(f"Service '{service}' called successfully.")
    else:
        print(f"Error calling service '{service}': {response.text}")

def Bubbles():
    entity_id = 'switch.bubble_machine_bubble_machine_10s'
    print("Turning on the bubble machine...")
    call_ha_service('switch/turn_on', {"entity_id": entity_id})

def Birthday():
    entity_id = 'switch.celebrate_machine_celebrate_machine'
    print("Turning on the celebrate machine...")
    call_ha_service('switch/turn_on', {"entity_id": entity_id})

def adjust_desk_height(desired_height):
    STOP_ENTITY_ID = "cover.desk_desk"
    SET_HEIGHT_ENTITY_ID = "number.desk_desk_height"

    def control_desk(stop_entity_id, set_height_entity_id, height):
        print("Stopping the desk...")
        call_ha_service('cover/stop_cover', {"entity_id": stop_entity_id})
        time.sleep(1)  # Wait for a moment before setting the height

        print("Setting the desk height...")
        call_ha_service('number/set_value', {"entity_id": set_height_entity_id, "value": height})

    # Call the control_desk function twice with a 1-second sleep between the calls
    control_desk(STOP_ENTITY_ID, SET_HEIGHT_ENTITY_ID, desired_height)
    time.sleep(1)
    control_desk(STOP_ENTITY_ID, SET_HEIGHT_ENTITY_ID, desired_height)