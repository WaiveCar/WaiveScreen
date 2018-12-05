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
                "id": 1,
                "name": "Daytime Santa Monica",
                "image": "sm-day.jpg",
                "multiplier": 1.5
            }, {
                "id": 2,
                "name": "Night Time Hollywood",
                "image": "hollywood-night.jpg",
                "multiplier": 2
            }, {
                "id": 3,
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
def get_deals():
    zone = request.args.get("zone")
    price = request.args.get("price")
    start = request.args.get("start")
    is_splash = request.args.get("splash")
    quote_id = request.args.get("quoteId")
    if start:
        start_obj = datetime.datetime.utcfromtimestamp(int(request.args.get("start")))
    else:
        start_obj = datetime.datetime.now() 
    end = request.args.get("end")
    if end:
        end_obj = datetime.datetime.utcfromtimestamp(int(request.args.get("end")))
    quoteId = request.args.get("quoteId")
    if not is_splash:
        return jsonify({
            "id": quoteId,
            "zone": "the zone",
            "start": start,
            "end": end,
            "price": price,
            "minutesPerDay": "some amount"
        })
    else:
        # For now, the dummy data below is going to be sent to the client
        price_per_second = 200 / 60 # $1 per 30 seconds 
        total_seconds = int(price) / price_per_second 
        start = datetime.datetime.now()
        deal = {
            "quotes": [
                {
                    "days": 1,       
                    "start": start,
                    "end": start + datetime.timedelta(days=1),
                    "basePrice": price,
                    "total": price,
                    "pricePerDay": price,
                    "secondsPerDay": total_seconds,
                    "perMinutePerDay": price_per_second * 60, 
                    "addedDays": 0,
                    "addedMinutes": 0,
                    "color": "light",
                },
                {
                    "days": 7,
                    "start": start,
                    "end": start + datetime.timedelta(days=7),
                    "basePrice": price,
                    "total": price,
                    "pricePerDay": int(price) / 7,
                    "secondsPerDay": total_seconds / 7,
                    "perMinutePerDay": price_per_second * 60, 
                    "addedDays": 0,
                    "addedMinutes": 0,
                    "color": "warning"
                },
                {
                    "days": 30,
                    "start": start,
                    "end": start + datetime.timedelta(days=30),
                    "basePrice": price,
                    "total": price,
                    "pricePerDay": int(price) / 30,
                    "secondsPerDay": total_seconds / 30,
                    "perMinutePerDay": price_per_second * 60, 
                    "addedDays": 0,
                    "addedMinutes": 0,
                    "color": "secondary" 
                }
            ]
        }
        active_sessions[quote_id] = deal
        return jsonify(deal)

@app.route("/capture", methods=["POST", "PUT"])
def handle_cart():
    if request.method == "POST":
        try:
            print('data: ', request.data)
            return 'success', 200
        except:
            return "error capturing cart", 400
    if request.method == "PUT":
        try:
            if "file" not in request.files:
                return abort(404)
            payer = request.form.get("payer")
            print("payer: ", payer)
            cart = request.form.get("cart")
            print("cart", cart)
            file = request.files.get("file")
            print("file: ", file)
            file.filename = str(uuid4()) + ".jpg"
            if file:
                uploaded = s3.upload_s3(file)
            # This will also need to keep make database entries for the user's purchase as well as for
            # the new image file that has been uploaded. It will be updated with a payment id after 
            # the payment has succeeded
            return jsonify({"location": "payment/paynow.html"})
        except:
            return "error capturing cart", 400


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve(path):
    if path != "" and os.path.exists("static/" + path):
        return send_from_directory("static", path)
    else:
        return send_from_directory('static', 'index.html')

if __name__ == "__main__":
    app.run(use_reloader=True, port=5050)
