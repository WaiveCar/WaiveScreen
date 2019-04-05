from flask import Flask, send_from_directory, request, session, make_response, abort, redirect, jsonify, g
import sqlite3
import os
import json
from modules import s3
from uuid import uuid4
import datetime
from flask_mail import Mail, Message

app = Flask(__name__, static_folder="/static")
app.config["UPLOAD_FOLDER"] = "./user_images"
# Currently, emails cannot be sent out sender info added to the config. Once the config items below are added, 
# Emails should be able to be sent out. The info that is currently there just filler info, so it is all commented out
'''
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'yourId@gmail.com'
app.config['MAIL_PASSWORD'] = '*****'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
'''
# For emails to actually be sent out, the line below needs to be sent to False.
app.config["TESTING"] = True
mail = Mail(app)

# This variable stores the path of the sqlite database
DATABASE = os.getcwd() + "/ad-platform.db"
# This dictionary is currently used for storing session information. It should later be switched to
# some kind of better caching system, but this works for now
active_sessions = dict()



# This route is used when carts are purchased. The post request is to make the intial purchase row
# in the table while the put request is for updating the row with the information sent back by paypal
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
            active_sessions[quote_id] = [cart]
            file = request.files.get("file")
            #The filename for the file to upload will be a uuid
            file.filename = str(uuid4()) + ".jpg"
            # To make the file actually upload to the s3 bucket, the lines below need to be commented back in
            # They are currently commented out so as not to waste space in it
            if file:
                uploaded = s3.upload_s3(file)
            # Here an entry is made in the assets table for the uploaded image. Additional info about
            # the asset will probably need to be added in the future
            asset_query = "insert into assets (path) values ('{}');".format(file.filename)
            db_connection = sqlite3.connect(DATABASE)
            cursor = db_connection.cursor()
            cursor.execute(asset_query)
            db_connection.commit()
            asset_id = cursor.lastrowid
            # This query is for creating the new row in the purchases table. There is probably additional
            # relevant information to add to purchases at a later time
            purchases_query = "insert into purchases (quote_id, service, asset_id, extra_days, extra_minutes_per_day, total_price, days, price_per_day, per_minute_per_day, start_date, end_date) values ('{}', 'paypal', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}')".format(quote_id, asset_id, cart["addedDays"], cart["addedMinutes"], cart["total"], cart["days"], cart["pricePerDay"], cart["perMinutePerDay"], cart["start"], cart["end"])
            cursor.execute(purchases_query)
            db_connection.commit()
            db_connection.close()
            # The object that is persisted needs to have quote id, service (currently paypal), asset id (photo),
            # order id (from paypal), user's email (from paypal), total cost, added days, added mins per day, Paid (true or false).
            # the items that are not already added in this request are added in the put request that is made after the paypal
            # payment is completed
            return 'Advertising Successfully Reserved', 200
        except Exception as e:
            print(e)
            return "Error on attempt at initial capture", 400
    if request.method == "PUT":
        try:
            # This request updates the purchase entry with the information that the client has received after
            # the paypal purchase is completed
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
            # the user is redirected to a page summarizing what they just ordered. The cart that they ordered is stored
            # in the chache so that it can be pulled up by the confirmation page
            cart = active_sessions[quote_id][0]
            active_sessions[quote_id][0]["email"] = payer["payer_info"]["email"]
            msg = Message("Hello", 
                sender="alex@waive.car",
                recipients=[payer["payer_info"]["email"]]
            )
            msg.subject = "Thank you for your WaiveAds purchase!"
            msg.html = f"""
                <div>
                    <style>
                        body, * {{
                          font-family: 'Roboto', 'Helvetica', 'sans-serif';
                        }}
                        .header {{
                          width: 100%;
                        }}
                        .header img {{
                          width: 100%;
                          height: auto;
                        }}
                        .main {{
                          padding: 20px;
                        }}
                    </style>
                    <div class="header">
                        <img src="https://s3.amazonaws.com/waivecar-assets/email-logo.png">
                    </div>
                    <div class="main">
                        <h3>Hello {payer['payer_info']['first_name']} {payer['payer_info']['last_name']}</h3>
                        <p>
                            Thank you for your recent purchase of screentime with Waive! Your advertising will run from {cart['start']} to 
                            {cart['end']} and a total of {cart['days'] + cart['addedDays']} days for {cart['addedMinutes'] + 
                            round(cart['secondsPerDay'] / 60, 2)} minutes a day. The total price for this advertising is 
                            ${round(cart['total'] / 100, 2)}. Don't hesitate to contact us with any further questions!
                        </p>
                        <p>
                            Best regards,<br>
                            Waive
                        </p>
                    </div>
                </div>"""
            # The sending of this e-mail will likely need to be modified once the correct e-mail configuration information is added
            with mail.record_messages() as outbox:
                mail.send(msg)
            # If the storage of the information returned by paypal is successful, the user is sent to the confirmation page
            return jsonify({"location": "confirm.html"})
        except Exception as e:
            return "Error at capture update: {}".format(e), 400

# This route is a catch-all for serving static resources. If the resource does not exist, the user
# is sent the index page
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve(path):
    if path != "" and os.path.exists("static/" + path):
        return send_from_directory("static", path)
    else:
        return send_from_directory('static', 'index.html')

if __name__ == "__main__":
    app.run(host= '0.0.0.0', use_reloader=True, port=5050)
