from . import db
from werkzeug.security import generate_password_hash, check_password_hash
import secrets

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # better than using email as PK
    email = db.Column(db.String(100), unique=True, nullable=False)
    username = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(200), nullable=False)  # store hashed password
    session_token = db.Column(db.String(64), nullable=True)

    def __repr__(self):
        return f"<User {self.username}>"

# -----------------------
# CRUD functions
# -----------------------

def create_user(user: User) -> None:
    db.session.add(user)
    db.session.commit()

def verify_password(email: str, password: str) -> bool:
    user = User.query.filter_by(email=email).first()
    if not user:
        return False
    return check_password_hash(user.password, password)

def is_email_already_taken(email: str) -> bool:
    return User.query.filter_by(email=email).first() is not None

def update_session_token(email: str) -> None:
    user = User.query.filter_by(email=email).first()
    if user:
        user.session_token = secrets.token_hex(16)  # generate random session token
        db.session.commit()

def get_user_by_email(email: str) -> User:
    return User.query.filter_by(email=email).first()
