from . import auth_bp
from flask import request, make_response, render_template, redirect, url_for
from db import users

@auth_bp.route("/", methods=["GET"])
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    username = request.form.get("username")
    password = request.form.get("password")
    email = request.form.get("email")

    is_email_already_taken = users.is_email_already_taken(email)
    print(f"Is email already taken: {is_email_already_taken}")
    if is_email_already_taken:
        return render_template("register.html", error_msg="Username Already Exists")
    user_obj = users.User(
        email=email,
        username=username,
        password=password,
    )
    users.create_user(user_obj)
    res = make_response(redirect(url_for("auth.home")))
    return res

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    email = request.form.get("email")
    password = request.form.get("password")

    user_authenticated = users.verify_password(email, password)
    if not user_authenticated:
        return render_template("login.html", error_msg="Invalid Credentials")

    users.update_session_token(email, password)

    res = make_response(redirect(url_for("auth.home")))
    return res

