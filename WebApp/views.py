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
            cur.execute("SELECT id FROM users WHERE email = %s;", (session['email'], ))
            data = cur.fetchone()
            admin_id = data[0]

            cur.execute("""\
                SELECT room_name FROM rooms WHERE admin_id = %s;
            """, (admin_id, ))
            data = cur.fetchall()
            if data is None:
                all_rooms = None
            else:
                all_rooms = [item[0] for item in data]
    return render_template(
        "dashboard.html", email=session["email"],
        all_rooms=all_rooms
    )


@views.route("/pricing")
def pricing():
    return render_template("pricing.html")



@views.route('/signup')
def signup():
    return render_template("signup.html")



@views.route("/login")
def login():
    return render_template("login.html")


@views.route("/logout")
@login_required
def logout():
    try:
        session.pop("email")
        flash("Successfully Logged Out")
        return redirect(url_for('views.login'))
    except Exception as e:
        print(f"Logout: {type(e).__name__} - {str(e)}")
        return jsonify({"status": 500, "detail": "Something went wrong"}), 500


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
    if session["plan"]:
        session.pop("plan")
    session["plan"] = body["plan"]
    return jsonify({"plan": body["plan"]}), 200


@views.route("/get-room", methods=["POST"])
def get_room():
    body = request.get_json()
    if session["room_id"]:
        session.pop("room_id")
    session["room_id"] = body["room_id"]
    return jsonify({"room_id": body["room_id"]}), 200
