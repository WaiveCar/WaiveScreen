from flask import Flask, send_from_directory, request, abort, redirect, url_for
from werkzeug.utils import secure_filename
import os
import json
import boto3, botocore
app = Flask(__name__, static_folder='/static')
app.config["UPLOAD_FOLDER"] = "./user_images"

S3_BUCKET = "daleighan.com"
S3_KEY = os.environ.get("S3_ACCESS_KEY")
S3_SECRET = os.environ.get("S3_SECRET_ACCESS_KEY")
S3_LOCATION = 'http://{}.s3.amazonaws.com/'.format(S3_BUCKET)

s3 = boto3.client(
   "s3",
   aws_access_key_id=S3_KEY,
   aws_secret_access_key=S3_SECRET
)

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
        print("file:", file)
        file.filename = secure_filename(file.name) + ".jpg"

        if file:
            print("filename: ", file.filename)
            #file.save(os.path.join(app.config["UPLOAD_FOLDER"], file.filename + ".jpg"))
            uploaded = upload_s3(file, S3_BUCKET)
            print('uploaded: ', uploaded)
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

def upload_s3(file, bucket_name, acl="public-read"):
    try: 
        s3.upload_fileobj(
            file,
            bucket_name,
            file.filename,
            ExtraArgs={
                "ACL": acl,
            }
        ) 
    except Exception as e:
        print("error: ", e)
        return e
    return "{}{}".format(S3_LOCATION, file.filename)

if __name__ == "__main__":
    app.run(use_reloader=True, port=5050)
