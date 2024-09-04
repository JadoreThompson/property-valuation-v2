from flask import Blueprint, jsonify, request, render_template, redirect, url_for


views = Blueprint("views", __name__)


@views.route("/")
def index():
    return render_template("index.html")


@views.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")