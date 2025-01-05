from flask import Flask, request, render_template, redirect, url_for, jsonify
import json
import os
from plaque_board_controller import set_leds
import commandhandler

app = Flask(__name__)

DATA_FILE = "data.json"
SECRETS_FILE = 'secrets.json'
COMMANDS_FILE = 'commands.json'

def load_commands():
    with open(COMMANDS_FILE, 'r') as file:
        return json.load(file)

# Save commands to JSON file
def save_commands(commands):
    with open(COMMANDS_FILE, 'w') as file:
        json.dump(commands, file, indent=4)

# Function to load data from JSON
def load_secrets():
    if not os.path.exists(SECRETS_FILE):
        return []  # Return empty list if file does not exist
    with open(SECRETS_FILE, "r") as file:
        return json.load(file)

# Save secrets to JSON file
def save_secrets(secrets):
    with open(SECRETS_FILE, 'w') as file:
        json.dump(secrets, file, indent=4)

# Function to load data from JSON
def load_data():
    if not os.path.exists(DATA_FILE):
        return []  # Return empty list if file does not exist
    with open(DATA_FILE, "r") as file:
        return json.load(file)

# Function to save data to JSON
def save_data(data):
    with open(DATA_FILE, "w") as file:
        json.dump(data, file, indent=4)

# Function to update data in JSON
def update_data(yt_name, leds_colour, leds):
    data = load_data()
    
    # Check if the entry already exists (based on YT_Name)
    for entry in data:
        if entry["YT_Name"] == yt_name:
            entry["Leds_colour"] = leds_colour
            entry["Leds"] = leds
            break
    else:
        # If no match is found, add a new entry
        data.append({
            "YT_Name": yt_name,
            "Leds_colour": leds_colour,
            "Leds": leds
        })
    
    save_data(data)

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/secrets', methods=['GET', 'POST'])
def manage_secrets():
    secrets = load_secrets()
    if request.method == 'POST':
        secrets['api_key'] = request.form['api_key']
        secrets['api_key_backup'] = request.form['api_key_backup']
        secrets['video_id'] = request.form['video_id']
        secrets['access_token'] = request.form['access_token']
        secrets['ha_url'] = request.form['ha_url']
        secrets['plaque_board_BOARD_IP'] = request.form['plaque_board_BOARD_IP']
        save_secrets(secrets)
        return redirect(url_for('manage_secrets'))

    return render_template('manage_secrets.html', secrets=secrets)

@app.route('/commands', methods=['GET', 'POST'])
def manage_commands():
    commands = load_commands()
    if request.method == 'POST':
        for command_name in commands.keys():
            commands[command_name]['enabled'] = f'enabled_{command_name}' in request.form
            commands[command_name]['timeout'] = int(request.form.get(f'timeout_{command_name}', commands[command_name]['timeout']))
            commands[command_name]['access_level'] = request.form.get(f'access_level_{command_name}', commands[command_name]['access_level'])
        save_commands(commands)
        return redirect(url_for('manage_commands'))

    return render_template('manage_commands.html', commands=commands, access_levels=get_access_levels())

# Function to get access levels
def get_access_levels():
    return {
        "regular": 1,
        "patreon": 2,
        "superchat": 3,
    }

@app.route('/test_commands', methods=['POST'])
def test_commands():
    command_input = request.form['command_input']
    commands = load_commands()
    if command_input in commands:
        commandhandler.execute_command(command_input, "Test User")
    else:
        print(f"Command '{command_input}' not recognized.")
    return redirect(url_for('manage_commands'))

@app.route('/update_command', methods=['POST'])
def update_command():
    command_name = request.form.get('command_name')
    enabled = request.form.get('enabled') == 'true'
    timeout = request.form.get('timeout')
    access_level = request.form.get('access_level')

    # Load the commands from the JSON file
    commands = load_commands()

    # Update the command with new values
    if command_name in commands:
        commands[command_name]['enabled'] = enabled
        commands[command_name]['timeout'] = int(timeout)
        commands[command_name]['access_level'] = access_level
        save_commands(commands)

        return jsonify({'message': f'Command {command_name} updated successfully.'}), 200
    else:
        return jsonify({'error': f'Command {command_name} not found.'}), 404

@app.route("/editor", methods=["GET", "POST"])
def editor():
    if request.method == "POST":
        yt_name = request.form["YT_Name"]
        leds_colour = request.form["Leds_colour"]
        leds = request.form["Leds"]
        update_data(yt_name, leds_colour, leds)
        return redirect(url_for("editor"))
    
    # Load data for display
    data = load_data()
    return render_template("editor.html", data=data)

@app.route("/edit", methods=["POST"])
def edit():
    original_yt_name = request.form["original_YT_Name"]
    yt_name = request.form["YT_Name"]
    leds_colour = request.form["Leds_colour"]
    leds = request.form["Leds"]

    # Load and update data
    data = load_data()
    for entry in data:
        if entry["YT_Name"] == original_yt_name:
            entry["YT_Name"] = yt_name
            entry["Leds_colour"] = leds_colour
            entry["Leds"] = leds
            break
    save_data(data)

    return redirect(url_for("editor"))

@app.route("/delete", methods=["POST"])
def delete():
    yt_name = request.json.get("YT_Name")

    # Load data and filter out the entry with the given YT_Name
    data = load_data()
    data = [entry for entry in data if entry["YT_Name"] != yt_name]

    # Save the updated data back to the JSON file
    save_data(data)

    return jsonify({"status": "success"})

@app.route("/trigger_leds", methods=["POST"])
def trigger_leds():
    yt_name = request.json.get("YT_Name")
    timehere = request.json.get("time", 5)  # Default duration of 5 seconds

    # Load data to find the matching row
    data = load_data()
    for entry in data:
        if entry["YT_Name"] == yt_name:
            leds_colour = entry["Leds_colour"]
            leds = entry["Leds"]
            success = set_leds(leds, leds_colour, timehere)
            return jsonify({"status": "success" if success else "failure"})

    return jsonify({"status": "error", "message": "YT_Name not found"}), 404

def run():
    secrets = load_secrets()
    app.run(host="0.0.0.0", port=8091, debug=False)

if __name__ == "__main__":
    secrets = load_secrets()
    app.run(host="0.0.0.0", port=8091, debug=False)