from flask import Flask, send_from_directory
import os
import json
app = Flask(__name__, static_folder='/static')

@app.route("/splash_resources")
def respond():
    return json.dumps({
        "popularLocations": [
            {
                "name": "Daytime Santa Monica",
                "image": "sm-day.jpg"
            }, {
                "name": "Night Time Hollywood",
                "image": "hollywood-night.jpg"
            }, {
                "name": "Morning Traffic",
                "image": "traffic-morning.jpg"
            }
        ],
        "cheapLocations": ["Morning Hollywood", "Night Time Santa Monica", "Day Time Mid-City"]
    })

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve(path):
    if path != "" and os.path.exists("static/" + path):
        return send_from_directory("static", path)
    else:
        return send_from_directory('static', 'index.html')

if __name__ == "__main__":
    app.run(use_reloader=True, port=3000)
