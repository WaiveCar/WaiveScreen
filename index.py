from flask import Flask, send_from_directory, request, abort, redirect, url_for
from werkzeug.utils import secure_filename
import os
import json
from modules import s3
app = Flask(__name__, static_folder='/static')
app.config["UPLOAD_FOLDER"] = "./user_images"


@app.route("/splash_resources")
def respond():
    return json.dumps({
        "popularLocations": [
            {
                "name": "Daytime Santa Monica",
                "image": "sm-day.jpg",
                "multiplier": 1.5
            }, {
                "name": "Night Time Hollywood",
                "image": "hollywood-night.jpg",
                "multiplier": 2
            }, {
                "name": "Morning Traffic",
                "image": "traffic-morning.jpg",
                "multiplier": 2.5
            }
        ],
        "cheapLocations": [
            {
                "name": "Morning Hollywood",
                "multiplier": 0.75
            }, {
                "name": "Night Time Santa Monica",
                "multiplier": 0.75
            }, {
                "name": "Day Time Mid-City",
                "multiplier": 0.5
            }
        ]
    })

@app.route("/purchase", methods=["POST"])
def handle_cart():
    if request.method == "POST":
        if "file" not in request.files:
            return abort(404)
        file = request.files.get("file")
        file.filename = secure_filename(file.name) + ".jpg"

        if file:
            uploaded = s3.upload_s3(file)
            print("file path: ", uploaded)
            return json.dumps({"location": "payment/paynow.html"})
        else:
            return "error"

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve(path):
    print('path: ', path)
    if path != "" and os.path.exists("static/" + path):
        return send_from_directory("static", path)
    else:
        return send_from_directory('static', 'index.html')

if __name__ == "__main__":
    app.run(use_reloader=True, port=5050)
