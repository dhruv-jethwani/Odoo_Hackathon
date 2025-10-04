from . import db
from werkzeug.security import generate_password_hash, check_password_hash
from utils.tokens import generate_random_tokens

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
        user.session_token = generate_random_tokens(32)
        db.session.commit()

def get_user_by_email(email: str) -> User:
    return User.query.filter_by(email=email).first()


def get_users(search: str = None, limit: int = 100):
    """Return a list of users. If `search` is provided, filter by email or username (case-insensitive).

    Args:
        search: optional search string to match against email or username
        limit: max number of results to return

    Returns:
        List[User]
    """
    query = User.query
    if search:
        like = f"%{search}%"
        # Use ilike for case-insensitive search when supported
        try:
            query = query.filter((User.email.ilike(like)) | (User.username.ilike(like)))
        except Exception:
            # Fallback to case-sensitive contains if ilike not supported
            query = query.filter((User.email.contains(search)) | (User.username.contains(search)))
    return query.limit(limit).all()
