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
        admins.update_admin_session_token(email)
        # Redirect admins to the admin users view which provides the users/managers context
        return redirect(url_for('admin.admin_users'))

    # Not an admin — check users table
    user = users.get_user_by_email(email)
    if not user or not check_password_hash(user.password, password):
        return render_template("login.html", error_msg="❌ Invalid credentials", hide_navbar=True)

    # Update user session token
    users.update_session_token(email)

    # Redirect depending on role
    role = getattr(user, 'role', 'Employee')
    if role == 'Manager':
        return redirect(url_for('manager.manager_dashboard'))
    else:
        # Employee
        return redirect(url_for('employee.employee_dashboard', email=email))





@auth_bp.route('/logout')
def logout():
    # Clear any session token for the current user if provided via query param (simple implementation)
    email = request.args.get('email')
    if email:
        user = users.get_user_by_email(email)
        if user:
            user.session_token = None
            from db import db as _db
            _db.session.commit()
    return redirect(url_for('auth.login'))

