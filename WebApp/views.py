import json

# Flask Modules
from flask import Blueprint, jsonify, request, render_template, redirect, url_for

# Directory Modules
from forms import ContactSalesForm
from db_connection import get_db_conn


views = Blueprint("views", __name__)


@views.route("/")
def index():
    """
    :return: Landing Page
    """
    form = ContactSalesForm()
    return render_template("index.html", form=form)


@views.route('/contact-sales')
def contact_sales():
    return render_template("contact-sales.html")


@views.route("/dashboard")
def dashboard():
    """
    :return: dashboard page
    """
    return render_template("dashboard.html")


@views.route("/pricing")
def pricing():
    return render_template("pricing.html")


@views.route("/login")
def login():
    return render_template("login.html")


@views.route('/signup')
def signup():
    return render_template("signup.html")
