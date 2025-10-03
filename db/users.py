from . import db

class User(db.Model):
    __tablename__ = "users"

    email = db.Column(db.String(30), primary_key=True)
    username = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(20), nullable=False)

    def __repr__(self):
        return f"<User {self.username}>"


def create_user(user: User) -> None:
    db.session.add(user)
    db.session.commit()


def verify_password(email: str, password: str) -> bool:
    return User.query.filter_by(email=email, password=password).first() != None

def is_email_already_taken(email: str) -> bool:
    return User.query.filter_by(email=email).first() != None