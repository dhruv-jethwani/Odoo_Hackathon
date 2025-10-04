from . import manager_bp
from flask import request, render_template, redirect, url_for, jsonify, g
from db import users
from db import approvals as approvals
from handlers.auth_utils import require_role
from utils.currency import get_currency_for_country, convert_amount


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
	# Determine current manager's email and user id from the request context (g)
	manager_email = getattr(g, 'current_user_email', None)
	approvals_list = []
	if manager_email:
		# find all employees who have this manager
		mgr_user = users.User.query.filter_by(email=manager_email).first()
		if mgr_user:
			employees = users.User.query.filter_by(manager_id=mgr_user.id).all()
			emails = [e.email for e in employees]
			# include approvals from those employees
			approvals_list = approvals.list_approvals_by_requestors(emails=emails)
	else:
		# fallback: show global pending approvals
		approvals_list = approvals.list_approvals(status='Pending')

	# convert to dicts and add requestor_username for display
	approvals_dicts = []
	for a in approvals_list:
		d = a.to_dict()
		u = users.User.query.filter_by(email=d.get('requestor_email')).first()
		d['requestor_username'] = u.username if u else d.get('requestor_email')
		# convert amount to company currency (determine company currency from manager's admin record if possible)
		company_currency = 'USD'
		# try to infer company currency from manager user's manager (admin) or environment; fallback USD
		# Here we check if there's an Admin record and use its country to derive currency
		try:
			from db import admins as admins_mod
			admin_obj = admins_mod.Admin.query.first()
			if admin_obj and admin_obj.country:
				cc = get_currency_for_country(admin_obj.country)
				if cc:
					company_currency = cc
		except Exception:
			pass
		# convert if approval has currency
		orig_currency = d.get('currency') or ''
		converted = None
		if d.get('amount') is not None and orig_currency:
			try:
				converted = convert_amount(d.get('amount'), orig_currency, company_currency)
			except Exception:
				converted = None
		d['converted_amount'] = converted
		d['company_currency'] = company_currency
		approvals_dicts.append(d)

	return render_template('manager.html', approvals=approvals_dicts, current_user_name=username or 'Manager', current_user_role='Manager')



@manager_bp.route('/manager/approvals/<int:aid>/approve', methods=['POST'])
@require_role('Manager')
def manager_approve(aid: int):
	# prefer the logged-in manager's email from `g` (set in main.before_request)
	approver_email = request.form.get('approver_email') or request.args.get('email') or getattr(g, 'current_user_email', None)
	if not approver_email:
		return "Approver email required", 400
	a = approvals.set_approval_status(aid, approver_email=approver_email, status='Approved', comments=request.form.get('comments'))
	if not a:
		return "Not found", 404
	return redirect(url_for('manager.manager_dashboard', email=approver_email))


@manager_bp.route('/manager/approvals/<int:aid>/reject', methods=['POST'])
@require_role('Manager')
def manager_reject(aid: int):
	approver_email = request.form.get('approver_email') or request.args.get('email') or getattr(g, 'current_user_email', None)
	if not approver_email:
		return "Approver email required", 400
	a = approvals.set_approval_status(aid, approver_email=approver_email, status='Rejected', comments=request.form.get('comments'))
	if not a:
		return "Not found", 404
	return redirect(url_for('manager.manager_dashboard', email=approver_email))


# escalate removed per requirements: managers can only approve or reject
