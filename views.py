from flask import Blueprint, jsonify, request, render_template, redirect, url_for
import json
from forms import ContactSalesForm
from db_connection import get_db_conn


views = Blueprint("views", __name__)


'''
    All landing page functions
'''
@views.route("/")
def index():
    form = ContactSalesForm()
    return render_template("index.html", form=form)


@views.route("/contact-sales", methods=["POST"])
def contact_sales():
    try:
        body = request.get_json()
        print(body)
        if body:
            with get_db_conn() as conn:
                with conn.cursor() as cur:
                    try:
                        cur.execute("""
                            SELECT 1
                            FROM contact_sales
                            WHERE email = %s;
                        """, (body["email"], ))
                        ex_user = cur.fetchone()
                        if ex_user:
                            return jsonify({"status": 409, "message": "Something went wrong"}), 409

                        cols = [key for key in body]
                        print(", ".join(cols))
                        print(", ".join(["%s"] * len(cols)))

                        cur.execute(f"""
                            INSERT INTO contact_sales ({", ".join(cols)})
                            VALUES ({", ".join(["%s"] * len(cols))});
                        """, ([(body[key], ) for key in cols]))
                        conn.commit()
                        return jsonify({"status": 200, "message": "Successfully signed up"}), 200
                    except Exception as e:
                        raise Exception(e)
    except Exception as e:
        print("Contact sales: ", str(e))
        return jsonify({"status": 500, "message": "Something went wrong, please try again"}), 500


'''
    Dashboard related
'''
@views.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")
