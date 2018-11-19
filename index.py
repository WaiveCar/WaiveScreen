from flask import Flask, send_from_directory, request, abort
from werkzeug.utils import secure_filename
import os
import json
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
        print(request.form.get("cart"))
    if "file" not in request.files:
        return abort(404)
    file = request.files.get("file")
    filename = secure_filename(file.name)
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename + ".jpg"))
    return request.form.get("cart")

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve(path):
    if path != "" and os.path.exists("static/" + path):
        return send_from_directory("static", path)
    else:
        return send_from_directory('static', 'index.html')

if __name__ == "__main__":
    app.run(use_reloader=True, port=5050)
