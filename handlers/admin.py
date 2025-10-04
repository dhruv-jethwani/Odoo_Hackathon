from . import admin_bp
from flask import request, render_template, redirect, url_for, make_response
from db import users
from db import admins as admins
from werkzeug.security import generate_password_hash, check_password_hash
from handlers import auth_bp


@admin_bp.route('/admin/overview')
def admin_overview():
    """Simple admin overview: list registered admins (name and email).

    The previous implementation referenced models that don't exist in this repo
    (ExpenseReport, User with department). Replace with a small, working view
    that uses the `Admin` model defined in `db/admins.py`.
    """
    try:
        admin_objs = admins.Admin.query.order_by(admins.Admin.id.asc()).all()
        return render_template('admin_overview.html', admins=admin_objs)
    except Exception as e:
        print(f"Error fetching admins: {e}")
        return "An error occurred while fetching admin overview.", 500


@admin_bp.route('/admin/users', methods=['GET'])
def admin_users():
    """Admin view: list users and support searching by email/username using ?q=term"""
    try:
        q = request.args.get('q', default=None, type=str)
        # limit parameter optional
        limit = request.args.get('limit', default=100, type=int)
        users_list = users.get_users(search=q, limit=limit)
        return render_template('admin_users.html', users=users_list, query=q)
    except Exception as e:
        print(f"Error fetching users: {e}")
        return "An error occurred while fetching users.", 500