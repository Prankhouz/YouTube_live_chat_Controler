import requests
import time
import secrets

# Home Assistant details
ACCESS_TOKEN = secrets.ACCESS_TOKEN
HA_URL = secrets.HA_URL
HEADERS = {
    'Authorization': f'Bearer {ACCESS_TOKEN}',
    'Content-Type': 'application/json',
}

def control_switch(entity_id, state):
    service = 'turn_on' if state else 'turn_off'
    url = f"{HA_URL}/api/services/switch/{service}"
    data = {"entity_id": entity_id}
    return requests.post(url, headers=HEADERS, json=data).status_code

def Bubbles():
    entity_id = 'switch.bubble_machine_bubble_machine_10s'
    print("Turning on the switch...")
    if control_switch(entity_id, True) == 200:
        print("Switch turned on successfully.")


def adjust_desk_height(desired_height):
    STOP_ENTITY_ID = "cover.desk_desk"
    SET_HEIGHT_ENTITY_ID = "number.desk_desk_height"

    def control_desk(stop_entity_id, set_height_entity_id, height):
        stop_data = {"entity_id": stop_entity_id}
        stop_response = requests.post(f"{HA_URL}/api/services/cover/stop_cover", json=stop_data, headers=HEADERS)

        if stop_response.status_code != 200:
            print(f"Error stopping the cover: {stop_response.text}")
            return

        print("Success! The cover has been stopped.")
        time.sleep(1)  # Wait for a moment before setting the height

        set_height_data = {"entity_id": set_height_entity_id, "value": height}
        set_height_response = requests.post(f"{HA_URL}/api/services/number/set_value", json=set_height_data, headers=HEADERS)

        if set_height_response.status_code != 200:
            print(f"Error setting the height: {set_height_response.text}")
            return

        print("Success! The height has been adjusted.")

    # Call the control_desk function twice with a 1-second sleep between the calls
    control_desk(STOP_ENTITY_ID, SET_HEIGHT_ENTITY_ID, desired_height)
    time.sleep(1)
    control_desk(STOP_ENTITY_ID, SET_HEIGHT_ENTITY_ID, desired_height)
