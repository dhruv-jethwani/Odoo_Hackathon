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
        user_objs = users.get_users(search=q, limit=limit)
        users_list = []
        for u in user_objs:
            manager_name = None
            if getattr(u, 'manager_id', None):
                mgr = users.User.query.get(u.manager_id)
                manager_name = mgr.username if mgr else None
            users_list.append({'id': u.id, 'username': u.username, 'email': u.email, 'role': u.role, 'manager': manager_name})
        # Render dashboard.html (available) and provide users in context for the template to use
        # Also provide a list of managers for the "Create User" modal
        manager_objs = users.User.query.filter_by(role='Manager').all()
        managers = [{'id': m.id, 'username': m.username, 'email': m.email} for m in manager_objs]
        return render_template('dashboard.html', users=users_list, current_user_name='Admin', managers=managers)
    except Exception as e:
        print(f"Error fetching users: {e}")
        return "An error occurred while fetching users.", 500



@admin_bp.route('/admin/approval-rules', methods=['GET'])
def admin_approval_rules():
    try:
        rules = []
        # If approvals module exists, try to fetch rules
        try:
            from db import approvals
            rules = [r.to_dict() for r in approvals.list_rules()]
        except Exception:
            rules = []
        return render_template('admin_approve.html', rules=rules, current_user_name='Admin')
    except Exception as e:
        print(f"Error fetching approval rules: {e}")
        return "Error", 500


@admin_bp.route('/admin/expenses', methods=['GET'])
def admin_expenses():
    try:
        # fetch all approvals/expenses
        items = []
        try:
            from db import approvals
            items = [a.to_dict() for a in approvals.list_approvals(limit=500)]
        except Exception:
            items = []
        return render_template('admin_expense.html', expenses=items, current_user_name='Admin')
    except Exception as e:
        print(f"Error fetching expenses: {e}")
        return "Error", 500



@admin_bp.route('/admin/approval-rules', methods=['POST'])
def admin_approval_rules_create():
    # Handle form submission from admin_approve.html to create a new rule
    try:
        form = request.form
        name = form.get('description') or form.get('name') or 'Approval Rule'
        min_amount = form.get('min_amount')
        max_amount = form.get('max_amount')
        category = form.get('category')
        required_approvers = form.get('required_approvers') or 1
        # Convert numeric fields where possible
        try:
            min_amount = float(min_amount) if min_amount else None
        except Exception:
            min_amount = None
        try:
            max_amount = float(max_amount) if max_amount else None
        except Exception:
            max_amount = None
        try:
            required_approvers = int(required_approvers)
        except Exception:
            required_approvers = 1

        from db import approvals as approvals_mod
        approvals_mod.create_rule(name=name, min_amount=min_amount, max_amount=max_amount, category=category, required_approvers=required_approvers)
        return redirect(url_for('admin.admin_approval_rules'))
    except Exception as e:
        print(f"Error creating approval rule: {e}")
        return "Error", 500



@admin_bp.route('/admin/expenses/<int:aid>/override', methods=['POST'])
def admin_override_expense(aid: int):
    # Admin override: set approval status directly from admin UI
    try:
        action = request.form.get('action')
        approver_email = request.form.get('approver_email') or 'admin@company'
        comments = request.form.get('comments')
        if action not in ('approve', 'reject'):
            return "Invalid action", 400
        status = 'Approved' if action == 'approve' else 'Rejected'
        from db import approvals as approvals_mod
        a = approvals_mod.set_approval_status(aid, approver_email=approver_email, status=status, comments=comments)
        if not a:
            return "Not found", 404
        return redirect(url_for('admin.admin_expenses'))
    except Exception as e:
        print(f"Error overriding expense: {e}")
        return "Error", 500

@admin_bp.route('/admin/users/<int:uid>/send-password', methods=['POST'])
def admin_send_password(uid: int):
    try:
        # In a real app we'd email or reset; here we'll just log and return to users page
        user = users.User.query.get(uid)
        if not user:
            return "User not found", 404
        # TODO: send password/email reset link. For now, just redirect back.
        return redirect(url_for('admin.admin_users'))
    except Exception as e:
        print(f"Error sending password: {e}")
        return "Error", 500

@admin_bp.route('/admin/users/<int:uid>/delete', methods=['POST'])
def admin_delete_user(uid: int):
    try:
        user = users.User.query.get(uid)
        if not user:
            return "User not found", 404
        from db import db as _db
        _db.session.delete(user)
        _db.session.commit()
        return redirect(url_for('admin.admin_users'))
    except Exception as e:
        print(f"Error deleting user: {e}")
        return "Error", 500



@admin_bp.route('/admin/users/create', methods=['POST'])
def admin_create_user():
    try:
        form = request.form
        username = form.get('username')
        email = form.get('email')
        role = form.get('role', 'Employee')
        manager_id = form.get('manager_id')

        # Basic validation
        if not username or not email:
            return "Missing username or email", 400

        if role not in ('Employee', 'Manager'):
            return "Invalid role", 400

        # Prevent creating Admin via this endpoint
        if role == 'Admin':
            return "Cannot create Admin via this endpoint", 403

        # Prevent duplicate emails
        if users.is_email_already_taken(email):
            return "Email already taken", 409

        # If a manager id was provided, validate it refers to an existing Manager
        mgr_id = None
        if manager_id:
            try:
                candidate_id = int(manager_id)
                mgr = users.User.query.get(candidate_id)
                if mgr and getattr(mgr, 'role', None) == 'Manager':
                    mgr_id = candidate_id
                else:
                    # invalid manager selection; ignore or return error
                    return "Selected manager is invalid", 400
            except Exception:
                return "Invalid manager id", 400

        # Generate a temporary password for the new user and store its hash
        from utils.tokens import generate_random_tokens
        from werkzeug.security import generate_password_hash
        temp_password = "employee"
        password_hash = generate_password_hash(temp_password)

        # Create the user record
        users.create_user_record(email=email, username=username, password_hash=password_hash, role=role, manager_id=mgr_id)

        # Log the temporary password so the admin can relay it (in a real app, email it)
        print(f"Created user {email} with temporary password: {temp_password}")

        return redirect(url_for('admin.admin_users'))
    except Exception as e:
        print(f"Error creating user: {e}")
        return "Error", 500