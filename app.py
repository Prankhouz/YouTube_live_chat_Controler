from flask import Flask, request, render_template_string, redirect, url_for
import sqlite3

app = Flask(__name__)

# Function to get the current data from the database
def get_data():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM supporter_data")
    data = cursor.fetchall()
    conn.close()
    return data

# Function to insert or update data in the database
def update_data(yt_name, leds_colour, leds):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO supporter_data (YT_Name, Leds_colour, Leds) VALUES (?, ?, ?)",
                   (yt_name, leds_colour, leds))
    conn.commit()
    conn.close()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        yt_name = request.form['YT_Name']
        leds_colour = request.form['Leds_colour']  # This will now be a hex color value
        leds = request.form['Leds']  # This can be another property or value related to LEDs
        update_data(yt_name, leds_colour, leds)
        return redirect(url_for('index'))
    data = get_data()
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Supporter Data Editor</title>
    </head>
    <body>
        <form method="post">
            <input type="text" name="YT_Name" placeholder="YT Name" required>
            <input type="color" name="Leds_colour" placeholder="Leds Colour" required>
            <input type="text" name="Leds" placeholder="Leds" required>
            <button type="submit">Submit</button>
        </form>
        <hr>
        <table>
            <tr>
                <th>YT Name</th>
                <th>Leds Colour</th>
                <th>Leds</th>
            </tr>
            {% for row in data %}
            <tr>
                <td>{{ row[0] }}</td>
                <td style="background-color: {{ row[1] }}">{{ row[1] }}</td>
                <td>{{ row[2] }}</td>
            </tr>
            {% endfor %}
        </table>
    </body>
    </html>
    """
    return render_template_string(html, data=data)

if __name__ == '__main__':
    app.run(debug=True)
