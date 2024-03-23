from flask import render_template

from server import app


@app.route("/")
def home():
    return render_template("home.html", name="World")
