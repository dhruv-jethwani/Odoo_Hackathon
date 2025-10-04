from . import db
from datetime import datetime

# Simple Approval model — adapt as needed for your real app
class Approval(db.Model):
    __tablename__ = 'approvals'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    requestor_email = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(100), nullable=True)
    amount = db.Column(db.Float, nullable=True)
    currency = db.Column(db.String(10), nullable=True)
    status = db.Column(db.String(20), nullable=False, default='Pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    approver_email = db.Column(db.String(100), nullable=True)
    approver_comments = db.Column(db.Text, nullable=True)
    receipt_filename = db.Column(db.String(200), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'requestor_email': self.requestor_email,
            'description': self.description,
            'category': self.category,
            'amount': self.amount,
            'currency': self.currency,
            'status': self.status,
            'created_at': None if not self.created_at else self.created_at.isoformat(),
            'updated_at': None if not self.updated_at else self.updated_at.isoformat(),
            'approver_email': self.approver_email,
            'approver_comments': self.approver_comments,
            'receipt_filename': self.receipt_filename,
        }


class ApprovalRule(db.Model):
    __tablename__ = 'approval_rules'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(200), nullable=False)
    min_amount = db.Column(db.Float, nullable=True)
    max_amount = db.Column(db.Float, nullable=True)
    category = db.Column(db.String(100), nullable=True)
    required_approvers = db.Column(db.Integer, nullable=False, default=1)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'min_amount': self.min_amount,
            'max_amount': self.max_amount,
            'category': self.category,
            'required_approvers': self.required_approvers,
        }


# -----------------------
# CRUD functions
# -----------------------

def create_approval(requestor_email: str, description: str = None, category: str = None, amount: float = None, currency: str = None, receipt_filename: str = None) -> Approval:
    a = Approval(requestor_email=requestor_email, description=description, category=category, amount=amount, currency=currency, receipt_filename=receipt_filename)
    db.session.add(a)
    db.session.commit()
    return a


def list_approvals(status: str = None, limit: int = 200):
    q = Approval.query
    if status:
        q = q.filter_by(status=status)
    return q.order_by(Approval.created_at.desc()).limit(limit).all()


def list_approvals_by_requestor(email: str, status: str = None, limit: int = 200):
    q = Approval.query.filter_by(requestor_email=email)
    if status:
        q = q.filter_by(status=status)
    return q.order_by(Approval.created_at.desc()).limit(limit).all()


def list_approvals_by_approver(email: str, status: str = None, limit: int = 200):
    q = Approval.query.filter_by(approver_email=email)
    if status:
        q = q.filter_by(status=status)
    return q.order_by(Approval.created_at.desc()).limit(limit).all()


def get_approval_by_id(aid: int):
    return Approval.query.get(aid)


def set_approval_status(aid: int, approver_email: str, status: str, comments: str = None):
    a = get_approval_by_id(aid)
    if not a:
        return None
    a.status = status
    a.approver_email = approver_email
    a.approver_comments = comments
    db.session.commit()
    return a


# Approval rule helpers
def create_rule(name: str, min_amount: float = None, max_amount: float = None, category: str = None, required_approvers: int = 1):
    r = ApprovalRule(name=name, min_amount=min_amount, max_amount=max_amount, category=category, required_approvers=required_approvers)
    db.session.add(r)
    db.session.commit()
    return r


def list_rules():
    return ApprovalRule.query.order_by(ApprovalRule.id.asc()).all()


def get_rule_by_id(rid: int):
    return ApprovalRule.query.get(rid)
