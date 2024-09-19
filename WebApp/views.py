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
        if "email" not in session and "user_id" not in session:
            flash("You need to be logged in to access this page.")
            return redirect(url_for('views.login'))
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
            # Loading the rooms connected to acc
            cur.execute("""\
                SELECT room_name, id FROM rooms WHERE admin_id = %s;
            """, (session["user_id"], ))
            data = cur.fetchall()
            if data is None:
                all_rooms = None
            else:
                all_rooms = data

            cur.execute("""\
                SELECT email\
                FROM users\
                WHERE id = %s;
            """, (session["user_id"], ))
            email = cur.fetchone()[0]

    return render_template(
        "dashboard.html", email=email,
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
@views.route("/save-session-object", methods=["POST"])
def save_session_object():
    try:
        body = request.get_json()
        for k, v in body.items():
            session[k] = v
        return jsonify({"status": 200, "message": "Success"}), 200
    except Exception as e:
        print(f"Save Session Object: {type(e).__name__} - {str(e)}")
        return jsonify({"status": 500, "message": str(e)}), 500
