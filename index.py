from flask import Flask, send_from_directory, request, session, make_response, abort, redirect, jsonify, g
import sqlite3
from werkzeug.utils import secure_filename
import sqlite3
import os
import json
from modules import s3
from uuid import uuid4
import datetime

app = Flask(__name__, static_folder="/static")
app.config["UPLOAD_FOLDER"] = "./user_images"

DATABASE = os.getcwd() + "/ad-platform.db"

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
            }, {
                "id": 2,
                "name": "Night Time Hollywood",
                "image": "hollywood-night.jpg",
            }, {
                "id": 3,
                "name": "Morning Traffic",
                "image": "traffic-morning.jpg",
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
            if "file" not in request.files:
                return abort(400)
            # In the future, the availability of the amount of time in the cart that is being sent will 
            # need to be verified before the user is allowed to purchase the ads 
            file = request.files.get("file")
            file.filename = str(uuid4()) + ".jpg"
            cart = json.loads(request.form.get("cart"))
            quote_id = request.form.get("quoteId")
            file = request.files.get("file")
            file.filename = str(uuid4()) + ".jpg"
            '''
            if file:
                uploaded = s3.upload_s3(file)
            '''
            asset_query = "insert into assets (path) values ('{}');".format(file.filename)
            db_connection = sqlite3.connect(DATABASE)
            cursor = db_connection.cursor()
            cursor.execute(asset_query)
            db_connection.commit()
            asset_id = cursor.lastrowid
            purchases_query = "insert into purchases (quote_id, service, asset_id, extra_days, extra_minutes_per_day, total_price, days, price_per_day, per_minute_per_day, start_date, end_date) values ('{}', 'paypal', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}')".format(quote_id, asset_id, cart["addedDays"], cart["addedMinutes"], cart["total"], cart["days"], cart["pricePerDay"], cart["perMinutePerDay"], cart["start"], cart["end"])
            cursor.execute(purchases_query)
            db_connection.commit()
            db_connection.close()
            # The object that is persisted needs to have quote id, service (currently paypal), asset id (photo),
            # order id (from paypal), user's email (from paypal), total cost, added days, added mins per day, Paid (true or false)
            return 'Advertising Successfully Reserved', 200
        except Exception as e:
            print(e)
            return "Error on attempt at initial capture", 500
    if request.method == "PUT":
        try:
            quote_id = request.json["quoteId"]
            payer = json.loads(request.json["payer"])
            payment_info = json.loads(request.json["paymentInfo"])
            db_connection = sqlite3.connect(DATABASE)
            cursor = db_connection.cursor()
            update_query = "update purchases set order_id='{}', email='{}', phone='{}', first_name='{}', last_name='{}' where quote_id='{}';".format(payment_info["orderID"], payer["payer_info"]["email"], payer["payer_info"]["phone"], payer["payer_info"]["first_name"], payer["payer_info"]["last_name"], quote_id) 
            cursor.execute(update_query)
            db_connection.commit();
            db_connection.close()
            # Once all requesite info is collected, for an advertisment, an email will also need to be sent out and
            # the user is redirected to a page summarizing what they just ordered
            return jsonify({"location": "payment/paynow.html"})
        except Exception as e:
            print("error: ", e)
            return "Error at capture update", 400


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve(path):
    if path != "" and os.path.exists("static/" + path):
        return send_from_directory("static", path)
    else:
        return send_from_directory('static', 'index.html')

if __name__ == "__main__":
    app.run(use_reloader=True, port=5050)
