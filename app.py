from flask import Flask, request, render_template, redirect, url_for, jsonify
import json
import os
from plaque_board_controller import set_leds

app = Flask(__name__)

DATA_FILE = "data.json"
SECRETS_FILE = 'secrets.json'

# Function to load data from JSON
def load_secrets():
    if not os.path.exists(SECRETS_FILE):
        return []  # Return empty list if file does not exist
    with open(SECRETS_FILE, "r") as file:
        return json.load(file)

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

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        yt_name = request.form["YT_Name"]
        leds_colour = request.form["Leds_colour"]
        leds = request.form["Leds"]
        update_data(yt_name, leds_colour, leds)
        return redirect(url_for("index"))
    
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

    return redirect(url_for("index"))

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

if __name__ == "__main__":
    secrets = load_secrets()
    app.run(host="0.0.0.0", port=8090, debug=True)
