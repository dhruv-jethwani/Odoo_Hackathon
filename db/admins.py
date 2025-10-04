from . import db
from werkzeug.security import generate_password_hash, check_password_hash
import secrets

class Admin(db.Model):
    __tablename__ = "admins"   # ✅ renamed from users → admins

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)   # ✅ added name
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)  # store hashed password
    country = db.Column(db.String(50), nullable=True)     # ✅ added country
    session_token = db.Column(db.String(64), nullable=True)

    def __repr__(self):
        return f"<Admin {self.name}>"

    # -----------------------
    # Utility methods
    # -----------------------
    def set_password(self, password: str):
        """Hash and set password"""
        self.password = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verify password"""
        return check_password_hash(self.password, password)

    def generate_session_token(self):
        """Generate a new session token"""
        self.session_token = secrets.token_hex(16)
        return self.session_token


# -----------------------
# DB helper functions for Admin
# -----------------------

def create_admin(name: str, email: str, password: str, country: str = None) -> Admin:
    admin = Admin(name=name, email=email, country=country)
    admin.set_password(password)
    db.session.add(admin)
    db.session.commit()
    return admin


def get_admin_by_email(email: str) -> Admin:
    return Admin.query.filter_by(email=email).first()


def authenticate_admin(email: str, password: str) -> Admin:
    admin = get_admin_by_email(email)
    if not admin:
        return None
    if admin.check_password(password):
        return admin
    return None


def update_admin_session_token(email: str) -> str:
    admin = get_admin_by_email(email)
    if not admin:
        return None
    token = admin.generate_session_token()
    db.session.commit()
    return token
