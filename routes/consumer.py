from flask import Blueprint, render_template
from flask_login import login_required

consumer = Blueprint("consumer", __name__)

@consumer.route("/dashboard")
@login_required
def dashboard():
    return render_template("usage.html")