from flask import Flask

from views import views


app = Flask(__name__)
app.register_blueprint(views)
app.config["SECRET_KEY"] = "secret"


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
