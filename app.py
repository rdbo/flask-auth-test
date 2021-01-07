from flask import Flask, url_for, redirect, render_template, request
from flask_sqlalchemy import SQLAlchemy
import uuid

app = Flask("test")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
valid_sessions = {}

class User(db.Model):
    username = db.Column(db.String(64), primary_key=True, unique=True, nullable=False)
    password = db.Column(db.String(64), unique=False, nullable=False)

    def __init__(self, user : str, passwd : str):
        self.username = user
        self.password = passwd

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/logout", methods=["POST"])
def logout():
    token = request.form["token"]
    if token:
        valid_sessions.pop(token)
        return redirect(url_for("index"))
    return redirect(url_for("error", err_str="invalid_token"))

@app.route("/sessions")
def sessions():
    global valid_sessions
    return render_template("sessions.html", session_list=valid_sessions)

@app.route("/users")
def users():
    return render_template("users.html", user_list=User.query.all())

@app.route("/error/<err_str>")
def error(err_str):
    return render_template("error.html", err=err_str)

@app.route("/user/<tkn>")
def user(tkn):
    global valid_sessions

    for entry in valid_sessions:
        if entry == tkn:
            user_data = User.query.filter_by(username=valid_sessions[entry]).first()
            if user_data:
                return render_template("user.html", user=user_data, token=tkn)
    return redirect(url_for("error", err_str="invalid_token"))

@app.route("/login", methods=["GET", "POST"])
def login():
    global valid_sessions
    if request.method == "POST":
        user = request.form["username"]
        passwd = request.form["password"]
        if user and passwd:
            user_data = User.query.filter_by(username=user).first()
            if not user_data or not user_data.password == passwd:
                return redirect(url_for("error", err_str="invalid_login"))
            token = str(uuid.uuid4()).replace("-", "")
            valid_sessions[token] = user_data.username
            return redirect(url_for("user", tkn=token))
        else:
            return redirect(url_for("error", err_str="invalid_form"))
    else:
        return render_template("login.html")

@app.route("/new", methods=["GET", "POST"])
def new_account():
    if request.method == "POST":
        user = request.form["username"]
        passwd = request.form["password"]
        if user and passwd:
            duplicated = User.query.filter_by(username=user).first()
            if duplicated:
                return redirect(url_for("error", err_str="duplicated_username"))
            
            user_data = User(user, passwd)
            db.session.add(user_data)
            db.session.commit()
            return redirect(url_for("login"))
        else:
            return redirect(url_for("error", err_str="invalid_form"))
            
    else:
        return render_template("new.html")

if __name__ == "__main__":
    db.create_all()
    app.run()