from flask import Flask
from db import db
from db.users import User
from handlers.auth import auth_bp
# Import modules that declare routes so their route decorators run
from handlers.admin import admin_bp
from handlers.manager import manager_bp
from handlers.employee import employee_bp
from flask import render_template
from flask import request, g
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("SQL_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)


@app.before_request
def load_current_user():
    """Set g.current_user_name and g.current_user_role based on session_token cookie.

    This looks for a `session_token` cookie, then tries to resolve it to an Admin
    first and then to a User. If found, it stores values on `g` for later use.
    """
    g.current_user_name = None
    g.current_user_role = None
    token = request.cookies.get('session_token')
    if not token:
        return
    from db import admins as admins_mod
    from db import users as users_mod
    admin = admins_mod.Admin.query.filter_by(session_token=token).first()
    if admin:
        g.current_user_name = admin.name
        g.current_user_role = 'Admin'
        g.current_user_email = admin.email
        return
    user = users_mod.User.query.filter_by(session_token=token).first()
    if user:
        g.current_user_name = user.username
        g.current_user_role = user.role or 'Employee'
        g.current_user_email = user.email


@app.context_processor
def inject_user_context():
    return {
        'current_user_name': getattr(g, 'current_user_name', None),
        'current_user_role': getattr(g, 'current_user_role', None),
        'current_user_email': getattr(g, 'current_user_email', None),
    }

app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(manager_bp)
app.register_blueprint(employee_bp)


@app.route('/dashboard')
def dashboard():
    # Render the existing dashboard.html template
    return render_template('dashboard.html')

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)