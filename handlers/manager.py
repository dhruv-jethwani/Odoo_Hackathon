from . import manager_bp
from flask import request, render_template, redirect, url_for, make_response, jsonify
from db import users
from db import approvals as approvals
from handlers.auth_utils import require_role
from werkzeug.security import generate_password_hash, check_password_hash


@manager_bp.route('/manager/api/approvals', methods=['GET'])
@require_role('Manager')
def manager_api_list_approvals():
	approver_email = request.args.get('approver_email')
	status = request.args.get('status')
	limit = request.args.get('limit', default=200, type=int)
	if approver_email:
		items = approvals.list_approvals_by_approver(email=approver_email, status=status, limit=limit)
	else:
		# if no approver specified, return pending approvals for managers to pick up
		items = approvals.list_approvals(status='Pending', limit=limit)

	# enrich with requestor username
	out = []
	for i in items:
		d = i.to_dict()
		u = users.User.query.filter_by(email=d.get('requestor_email')).first()
		d['requestor_username'] = u.username if u else d.get('requestor_email')
		out.append(d)
	return jsonify({'ok': True, 'approvals': out})


@manager_bp.route('/manager/api/approvals/<int:aid>/decide', methods=['POST'])
@require_role('Manager')
def manager_api_decide_approval(aid: int):
	data = request.get_json(force=True, silent=True) or {}
	action = (data.get('action') or '').lower()
	approver_email = data.get('approver_email')
	comments = data.get('comments')

	if action not in ('approve', 'reject'):
		return jsonify({'ok': False, 'error': 'action must be approve or reject'}), 400
	if not approver_email:
		return jsonify({'ok': False, 'error': 'approver_email is required'}), 400

	status = 'Approved' if action == 'approve' else 'Rejected'
	a = approvals.set_approval_status(aid, approver_email=approver_email, status=status, comments=comments)
	if not a:
		return jsonify({'ok': False, 'error': 'approval not found'}), 404
	return jsonify({'ok': True, 'approval': a.to_dict()})



@manager_bp.route('/manager/dashboard')
@require_role('Manager')
def manager_dashboard():
	# Render dashboard but mark role as Manager; front-end can adapt
	username = request.args.get('username')
	# show pending approvals for this manager (or all pending if no specific manager email provided)
	manager_email = request.args.get('email')
	if manager_email:
		approvals_list = approvals.list_approvals_by_approver(email=manager_email)
	else:
		approvals_list = approvals.list_approvals(status='Pending')

	# convert to dicts and add requestor_username for display
	approvals_dicts = []
	for a in approvals_list:
		d = a.to_dict()
		u = users.User.query.filter_by(email=d.get('requestor_email')).first()
		d['requestor_username'] = u.username if u else d.get('requestor_email')
		approvals_dicts.append(d)

	return render_template('manager.html', approvals=approvals_dicts, current_user_name=username or 'Manager', current_user_role='Manager')



@manager_bp.route('/manager/expenses/<int:aid>/approve', methods=['POST'])
def manager_approve(aid: int):
	approver_email = request.args.get('email') or request.form.get('approver_email')
	if not approver_email:
		return "Approver email required", 400
	a = approvals.set_approval_status(aid, approver_email=approver_email, status='Approved', comments=request.form.get('comments'))
	if not a:
		return "Not found", 404
	return redirect(url_for('manager.manager_dashboard', email=approver_email))


@manager_bp.route('/manager/expenses/<int:aid>/reject', methods=['POST'])
def manager_reject(aid: int):
	approver_email = request.args.get('email') or request.form.get('approver_email')
	if not approver_email:
		return "Approver email required", 400
	a = approvals.set_approval_status(aid, approver_email=approver_email, status='Rejected', comments=request.form.get('comments'))
	if not a:
		return "Not found", 404
	return redirect(url_for('manager.manager_dashboard', email=approver_email))


@manager_bp.route('/manager/expenses/<int:aid>/escalate', methods=['POST'])
def manager_escalate(aid: int):
	approver_email = request.args.get('email') or request.form.get('approver_email')
	if not approver_email:
		return "Approver email required", 400
	# For escalate we mark status as PendingEscalation or similar; here we use 'Escalated'
	a = approvals.set_approval_status(aid, approver_email=approver_email, status='Escalated', comments=request.form.get('comments'))
	if not a:
		return "Not found", 404
	return redirect(url_for('manager.manager_dashboard', email=approver_email))
