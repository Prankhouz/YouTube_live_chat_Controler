import requests
import time

def adjust_desk_height(desired_height):
    # Configuration
    ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiI3NzA0ZWI2ODVkNWQ0OGJkYjg4OTk0ZTZlNmFhMDYzMyIsImlhdCI6MTcxMDI0Mjc3MSwiZXhwIjoyMDI1NjAyNzcxfQ.qMxeg-H6qJJC-h96uuVu1GAyncqM6_I2uHuXrW3pTxI"
    HA_URL = "http://192.168.1.170:8123"
    STOP_ENTITY_ID = "cover.desk_desk"
    SET_HEIGHT_ENTITY_ID = "number.desk_desk_height"

    # Header for authentication
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "content-type": "application/json",
    }

    # First stop cover sequence
    stop_data = {"entity_id": STOP_ENTITY_ID}
    stop_response = requests.post(f"{HA_URL}/api/services/cover/stop_cover", json=stop_data, headers=headers)

    if stop_response.status_code == 200:
        print("Success! The cover has been stopped.")
        time.sleep(1)  # Wait for a moment before setting the height
    else:
        print(f"Error stopping the cover: {stop_response.text}")

    # First set height sequence
    set_height_data = {
        "entity_id": SET_HEIGHT_ENTITY_ID,
        "value": desired_height
    }
    set_height_response = requests.post(f"{HA_URL}/api/services/number/set_value", json=set_height_data, headers=headers)

    if set_height_response.status_code == 200:
        print("Success! The height has been adjusted.")
    else:
        print(f"Error setting the height: {set_height_response.text}")

    # Second stop cover sequence (repeat)
    stop_response = requests.post(f"{HA_URL}/api/services/cover/stop_cover", json=stop_data, headers=headers)

    if stop_response.status_code == 200:
        print("Success! The cover has been stopped again.")
        time.sleep(1)  # Wait for a moment before the next action
    else:
        print(f"Error stopping the cover: {stop_response.text}")

    # Second set height sequence (repeat)
    set_height_response = requests.post(f"{HA_URL}/api/services/number/set_value", json=set_height_data, headers=headers)

    if set_height_response.status_code == 200:
        print("Success! The height has been adjusted again.")
    else:
        print(f"Error setting the height: {set_height_response.text}")


#adjust_desk_height(110.0)