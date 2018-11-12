from flask import Flask, send_from_directory
import os
app = Flask(__name__, static_folder='/static')

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve(path):
    cwd = os.getcwd()
    print(cwd)
    if path != "" and os.path.exists("static/" + path):
        return send_from_directory("static", path)
    else:
        return send_from_directory('static', 'index.html')

if __name__ == "__main__":
    app.run(use_reloader=True, port=5000)
