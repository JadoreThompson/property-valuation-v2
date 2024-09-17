# Flask Modules
from flask import Blueprint, jsonify, request, render_template, redirect, url_for, session

# Directory Modules
from forms import ContactSalesForm


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


@views.route("/checkout")
def checkout():
    return render_template(
        'checkout.html',
        email=session["email"],
        plan=session["plan"]
    )


"""API Endpoints"""
@views.route('/get-email', methods=["POST"])
def get_email():
    body = request.get_json()
    session["email"] = body["email"]
    return jsonify({"email": body["email"]}), 200


@views.route('/get-plan', methods=["POST"])
def get_pricing_plan():
    body = request.get_json()
    session["plan"] = body["plan"]
    return jsonify({"plan": body["plan"]}), 200
