import functools
from functools import wraps

# Flask Modules
from flask import (
    Blueprint, jsonify, request, render_template, redirect,
    url_for, session, flash
)

# Directory Modules
from db_connection import get_db_conn


views = Blueprint("views", __name__)


# Login Wrapper
def login_required(f):
    @wraps(f)
    def secure_endpoint(*args, **kwargs):
        if "email" not in session:
            flash("You need to be logged in to access this page.")
            return redirect(url_for('views.login'))  # Redirect to the login page
        return f(*args, **kwargs)
    return secure_endpoint


@views.route("/")
def index():
    """
    :return: Landing Page
    """
    return render_template("index.html")


@views.route('/contact-sales')
def contact_sales():
    return render_template("contact-sales.html")


@views.route("/dashboard")
@login_required
def dashboard():
    """
    :return: dashboard page
    """
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            # Get the user ID based on the email from the session
            cur.execute("""
                SELECT id
                FROM users
                WHERE email = %s;
            """, (session["email"], ))
            user_id = cur.fetchone()

            # Grabbing room names
            cur.execute("""
                SELECT room_name
                FROM rooms
                WHERE admin_id = %s;
            """, (user_id[0], ))

            room = cur.fetchone()  # Store the result to avoid calling fetchone() multiple times
            if room is None:
                all_rooms = None
            else:
                print(f"Room: type {type(room)} - {room[0]}")
                all_rooms = [r for r in room]
                print(all_rooms)

    return render_template(
        "dashboard.html",
        email=session["email"],
        all_rooms=all_rooms
    )


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
@login_required
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
