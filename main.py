from flask import Flask
from db import db
from db.users import User
from handlers.auth import auth_bp
from handlers import admin_bp, manager_bp, employee_bp
from flask import render_template
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("SQL_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

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