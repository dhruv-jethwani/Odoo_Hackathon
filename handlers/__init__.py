from flask import Blueprint

auth_bp = Blueprint('auth', __name__)
admin_bp = Blueprint('admin', __name__)
manager_bp = Blueprint('manager', __name__)
employee_bp = Blueprint('employee', __name__)