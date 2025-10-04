from . import auth_bp
from flask import request, render_template, redirect, url_for, make_response
from db import users
from werkzeug.security import generate_password_hash, check_password_hash

# 🟢 Register Route
@auth_bp.route("/", methods=["GET"])
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    # Get form data
    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    # Validation
    if not username or not email or not password:
        return render_template("register.html", error_msg="⚠️ All fields are required")

    if users.is_email_already_taken(email):
        return render_template("register.html", error_msg="⚠️ Email already registered")

    # Hash password
    hashed_password = generate_password_hash(password)

    # Create user object
    user_obj = users.User(
        email=email,
        username=username,
        password=hashed_password
    )

    users.create_user(user_obj)

    # Redirect to login after successful register
    return redirect(url_for("auth.login"))


# 🟢 Login Route
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    # Get form data
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    print(email,password)
    if not email or not password:
        return render_template("login.html", error_msg="⚠️ All fields are required")

    # Get user from DB
    user = users.get_user_by_email(email)
    if not user or not check_password_hash(user.password, password):
        return render_template("login.html", error_msg="❌ Invalid credentials")

    # Update session token (only needs email, not password)
    users.update_session_token(email)

    # Redirect to dashboard/home
    res = make_response(redirect(url_for("dashboard")))
    return res

