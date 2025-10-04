from . import auth_bp
from flask import request, render_template, redirect, url_for, make_response
from db import users
from db import admins as admins
from werkzeug.security import generate_password_hash, check_password_hash
from flask import redirect

# 🟢 Register Route
@auth_bp.route("/", methods=["GET"])
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html", hide_navbar=True)

    # Get form data
    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    # Validation
    if not username or not email or not password:
        return render_template("register.html", error_msg="⚠️ All fields are required", hide_navbar=True)

    if users.is_email_already_taken(email):
        return render_template("register.html", error_msg="⚠️ Email already registered", hide_navbar=True)

    # Hash password
    hashed_password = generate_password_hash(password)

    # Create an Admin account on registration
    admins.create_admin(name=username, email=email, password=password)

    # Redirect to login after successful register
    return redirect(url_for("auth.login"))


# 🟢 Login Route
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html", hide_navbar=True)

    # Get form data
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    print(email,password)
    if not email or not password:
        return render_template("login.html", error_msg="⚠️ All fields are required", hide_navbar=True)

    # First, check if this is an admin
    admin = admins.get_admin_by_email(email)
    if admin and admin.check_password(password):
        # update admin session token
        token = admins.update_admin_session_token(email)
        # Redirect admins to the admin users view which provides the users/managers context
        res = make_response(redirect(url_for('admin.admin_users', username=admin.name)))
        # set a cookie with the session token (simple, not HttpOnly for dev)
        res.set_cookie('session_token', token, httponly=True)
        return res

    # Not an admin — check users table
    user = users.get_user_by_email(email)
    if not user or not check_password_hash(user.password, password):
        return render_template("login.html", error_msg="❌ Invalid credentials", hide_navbar=True)

    # Update user session token
    token = users.update_session_token(email)

    # Redirect depending on role
    role = getattr(user, 'role', 'Employee')
    if role == 'Manager':
        res = make_response(redirect(url_for('manager.manager_dashboard', username=user.username, email=user.email)))
        res.set_cookie('session_token', token, httponly=True)
        return res
    else:
        # Employee
        res = make_response(redirect(url_for('employee.employee_dashboard', email=email, username=user.username)))
        res.set_cookie('session_token', token, httponly=True)
        return res





@auth_bp.route('/logout')
def logout():
    # Clear any session token for the current user if provided via query param (simple implementation)
    # Clear server-side token for the logged-in user (if cookie present)
    token = request.cookies.get('session_token')
    if token:
        # try to find a user with this token
        u = users.User.query.filter_by(session_token=token).first()
        if u:
            u.session_token = None
            from db import db as _db
            _db.session.commit()
        # also try admins
        from db import admins as admins_mod
        a = admins_mod.Admin.query.filter_by(session_token=token).first()
        if a:
            a.session_token = None
            from db import db as _db
            _db.session.commit()

    res = make_response(redirect(url_for('auth.login')))
    res.delete_cookie('session_token')
    return res

