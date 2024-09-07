from flask import Blueprint, jsonify, request, render_template, redirect, url_for
import json

from forms import ContactSalesForm
from db_connection import get_db_conn
from propai import prompt_gen


views = Blueprint("views", __name__)


@views.route("/")
def index():
    '''
        :return: Landing Page
    '''
    form = ContactSalesForm()
    return render_template("index.html", form=form)


@views.route("/contact-sales", methods=["POST"])
def contact_sales():
    '''
        :body: {ContactSalesForm}
        :return:
    '''

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
                        """, (body["email"],))
                        ex_user = cur.fetchone()
                        if ex_user:
                            return jsonify({"status": 409, "message": "Something went wrong"}), 409

                        cols = [key for key in body]
                        print(", ".join(cols))
                        print(", ".join(["%s"] * len(cols)))

                        cur.execute(f"""
                            INSERT INTO contact_sales ({", ".join(cols)})
                            VALUES ({", ".join(["%s"] * len(cols))});
                        """, ([(body[key],) for key in cols]))
                        conn.commit()
                        return jsonify({"status": 200, "message": "Successfully signed up"}), 200
                    except Exception as e:
                        raise Exception(e)
    except Exception as e:
        print("Contact sales: ", str(e))
        return jsonify({"status": 500, "message": "Something went wrong, please try again"}), 500


@views.route("/dashboard")
def dashboard():
    '''
        :return: dashboard page
    '''
    return render_template("dashboard.html")


@views.route('/get-response', methods=["POST"])
def get_response():
    '''
        :return: 200, response
        :return: 404, something went wrong with the agent
        :return: 429, {'message': str} not sent in the body
    '''
    body = request.get_json()
    if body["message"]:
        try:
            rsp = prompt_gen.SQL_AGENT.invoke({"input": body["message"]})
            result = rsp["output"]
            if result:
                return jsonify({"status": 200, "response": result})
        except Exception as e:
            print(f"Get Response: {str(e)}")
            return jsonify({"status": 404, "message": "Sorry I couldn't answer that, try something else"})
    else:
        print(f"Get Response: Invalid request")
        return jsonify({"status": 429, "message": "Invalid request"})
