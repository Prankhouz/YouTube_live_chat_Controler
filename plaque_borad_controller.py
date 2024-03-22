import requests
import time

def set_leds(led_indices, color,timehere):
    api_endpoint = f"http://192.168.1.14/json/state"
    payload = {
        "seg": {
            "i": []
        }
    }

    # Construct the payload to set the color of each LED
    for index in led_indices:
        payload["seg"]["i"].extend([index, color])

    # Send the API request to set the colors of the LEDs
    response = requests.post(api_endpoint, json=payload)

    # Check if the request was successful
    if response.status_code == 200:
        print(f"Set color {color} for LEDs {led_indices} successfully!")
    else:
        print(f"Failed to set color for LEDs {led_indices}. Status code: {response.status_code}")
        return False
    
    time.sleep(timehere)
    
    # Construct the payload to turn off the LEDs
    for index in led_indices:
        payload["seg"]["i"].extend([index, "000000"])

    # Send the API request to turn off all LEDs
    response = requests.post(api_endpoint, json=payload)

    # Check if the request was successful
    if response.status_code == 200:
        #print("Turned off all LEDs successfully!")
        return True
    else:
        print(f"Failed to turn off all LEDs. Status code: {response.status_code}")
        return False


#set_leds([86,85,84,99,100,101], "d900ff",5)


