from flask import Flask, send_from_directory, request, session, make_response, abort, redirect, jsonify
from werkzeug.utils import secure_filename
import os
import json
from modules import s3
from config.db import *
from uuid import uuid4
import datetime

app = Flask(__name__, static_folder="/static")
app.config["UPLOAD_FOLDER"] = "./user_images"

active_sessions = dict()

@app.route("/splash_resources")
def respond():
    old_session_id = request.headers.get("Session-Id")
    session_uuid = old_session_id if old_session_id in active_sessions else str(uuid4()) 
    if not session_uuid in active_sessions:
        active_sessions[session_uuid] = []
    response = make_response(jsonify({
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
    }))
    response.headers.set("Session-Id", session_uuid)
    return response

@app.route("/deal")
def get_deal():
    zone = request.args.get("zone")
    price = request.args.get("price")
    start = request.args.get("start")
    if start:
        start_obj = datetime.datetime.utcfromtimestamp(int(request.args.get("start")))
    else:
        start_obj = datetime.datetime.now() 
    end = request.args.get("end")
    if end:
        end_obj = datetime.datetime.utcfromtimestamp(int(request.args.get("end")))
    quoteId = request.args.get("quoteId")
    return jsonify({
        "id": quoteId,
        "zone": "the zone",
        "start": start,
        "end": end,
        "price": price,
        "minutesPerDay": "some amount"
    })

@app.route("/purchase", methods=["POST"])
def handle_cart():
    if request.method == "POST":
        if "file" not in request.files:
            return abort(404)
        file = request.files.get("file")
        file.filename = str(uuid4()) + ".jpg"
        print(request)
        if file:
            uploaded = s3.upload_s3(file)
            return jsonify({"location": "payment/paynow.html"})
        else:
            return "error"

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve(path):
    if path != "" and os.path.exists("static/" + path):
        return send_from_directory("static", path)
    else:
        return send_from_directory('static', 'index.html')

if __name__ == "__main__":
    app.run(use_reloader=True, port=5050)
