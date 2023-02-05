import os
import re

from cs50 import SQL
from flask import Flask, session, redirect, render_template,request
from flask_session import Session
from helpers import login_required
from flask_mail import Mail, Message

# Configure application
app = Flask(__name__)

# Requires that "Less secure app access" be on
# https://support.google.com/accounts/answer/6010255
app.config["MAIL_DEFAULT_SENDER"] = "noreply.bot@gmail.com"
app.config["MAIL_PASSWORD"] = "kyiufgpzbtzbpebh"
app.config["MAIL_PORT"] = 465
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_USE_SSL"] = True
app.config["MAIL_USERNAME"] = "mail.bot.web@gmail.com"
mail = Mail(app)

# Blood-Groups
BGROUP = [
    'A+','A-','B+','B-','AB+','AB-','O+','O-'
]
# Zone
ZONE = [
    "Mirpur","Mohammadpur","Dhanmondi"
]

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///users.db")

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/", methods=['POST', 'GET'])
def donate():
    """ THIS IS THE DONATE PAGE """

    # Forgot any user id
    session.clear()

    if request.method == "POST":

        # Form responses
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        phone = request.form.get("phone")
        bgroup = request.form.get("bgroup")
        zone = request.form.get("zone")

        # Usernames, usermail and usersphone arrays
        usernames = db.execute("SELECT name FROM users")
        userphones = db.execute("SELECT phone FROM users")
        useremails = db.execute("SELECT email FROM users")
        unames = []
        uphones = []
        uemails = []
        for i in range(len(usernames)):
            unames.append(usernames[i]['name'].replace(" ", "").upper())
            uphones.append(userphones[i]['phone'])
            uemails.append(useremails[i]['email'])

        # Duplicate user check
        if name.replace(" ", "").upper() in unames and phone in uphones:
            return render_template("donate.html", BGROUP=BGROUP, ZONE=ZONE, error="Error: Existing user !")

        if email in uemails:
            return render_template("donate.html", BGROUP=BGROUP, ZONE=ZONE, error="Error: Existing e-mail !")

        # Inspect element attack proof
        if not zone in ZONE or not bgroup in BGROUP:
            return render_template("donate.html", BGROUP=BGROUP, ZONE=ZONE, error="Error: Invalid entry !")



        db.execute("INSERT INTO users (name, email, password, phone, bgroup, zone)VALUES(?, ?, ?, ?, ?, ?)", name, email, password, phone, bgroup, zone)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE name = ?", name)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        return render_template("donate.html", BGROUP=BGROUP, ZONE=ZONE, success="Click menu to explore")

    return render_template("donate.html", BGROUP=BGROUP, ZONE=ZONE)


@app.route("/login", methods=['POST', 'GET'])
def login():
    """ THIS IS THE LOGIN PAGE """

    # Forgot any user id
    session.clear()

    if request.method == "POST":

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE name = ? AND password = ? AND bgroup = ?", request.form.get("name"), request.form.get("password"), request.form.get("bgroup"))
        if len(rows) != 1:
            return render_template("login.html", BGROUP=BGROUP, ZONE=ZONE, error="Error: Invalid user !")



        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        return redirect("/userinfo")

    return render_template("login.html", BGROUP=BGROUP, ZONE=ZONE)


@app.route("/confirm_edit_delete_account", methods=['GET','POST'])
@login_required
def confirm_edit_delete_account():
    """ THIS IS THE CONFIRM EDIT DELETE ACCOUNT PAGE """
    if request.method == "POST":
        # Form responses
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        phone = request.form.get("phone")
        bgroup = request.form.get("bgroup")
        zone = request.form.get("zone")

        # Inspect element attack proof
        if not zone in ZONE or not bgroup in BGROUP:
            return render_template("confirm_edit.html", BGROUP=BGROUP, ZONE=ZONE, error="Error: Invalid entry !")

        db.execute("UPDATE users SET name = ?, email = ?, password = ?, phone = ?, bgroup = ?, zone = ?  WHERE id = ?", name,email,password,phone,bgroup,zone,session["user_id"])

        return redirect("/userinfo")
    return render_template("confirm_edit.html", BGROUP=BGROUP, ZONE=ZONE)

@app.route("/delete", methods=['GET','POST'])
@login_required
def delete_account():
    if request.method == "POST":
        # Form responses
        check = request.form.get("check")
        if check == '1':
            db.execute("DELETE FROM users WHERE id = ?", session["user_id"])
            return redirect("/")

    return render_template("delete.html")

@app.route("/search", methods=['POST', 'GET'])
def search():
    """ THIS IS THE SEARCH PAGE """
    if request.method == "POST":
        bgroup = request.form.get("bgroup")
        zone = request.form.get("zone")

        # Inspect element attack proof
        if not zone in ZONE or not bgroup in BGROUP:
            return render_template("search.html", BGROUP=BGROUP, ZONE=ZONE, error="Error: Invalid entry !")

        result = db.execute("SELECT name, phone FROM users WHERE bgroup = ? AND zone = ? ORDER BY name ASC", bgroup, zone)

        return render_template("result.html", result=result, BGROUP=BGROUP, ZONE=ZONE)


    return render_template("search.html", BGROUP=BGROUP, ZONE=ZONE)

@app.route("/forget", methods=['POST', 'GET'])
def forget():
    """ THIS IS THE FORGET PASSWORD PAGE """
    if request.method == "POST":
        # Form responses
        email = request.form.get("email")

        # Usermail array
        useremails = db.execute("SELECT email FROM users")
        uemails = []
        for i in range(len(useremails)):
            uemails.append(useremails[i]['email'])

        if email not in uemails:
            return render_template("forget.html", error="Error: User not found !")

        rows = db.execute("SELECT password FROM users WHERE email = ?", email)
        password = rows[0]['password']

        # Send email
        message = Message("Blood-Spot forget password", sender = "noreply.bot@gmail.com", recipients=[email])
        message.body = f"Your password is {password}"
        mail.send(message)
        return redirect("/login")

    return render_template("forget.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/userinfo")
@login_required
def userinfo():
    """ THIS IS THE USER INFORMATION PAGE """
    info = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])

    return render_template("userinfo.html", info=info)
