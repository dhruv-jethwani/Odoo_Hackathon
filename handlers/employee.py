from . import employee_bp
from flask import request, render_template, redirect, url_for, make_response
from db import users
from werkzeug.security import generate_password_hash, check_password_hash

from flask import jsonify
from db import approvals as approvals
from handlers.auth_utils import require_role


@employee_bp.route('/employee/api/approvals', methods=['POST'])
@require_role('Employee')
def employee_api_create_approval():
	data = request.get_json(force=True, silent=True) or {}
	requestor_email = data.get('requestor_email')
	if not requestor_email:
		return jsonify({'ok': False, 'error': 'requestor_email is required'}), 400
	description = data.get('description')
	category = data.get('category')
	amount = data.get('amount')
	currency = data.get('currency')

	a = approvals.create_approval(requestor_email=requestor_email, description=description, category=category, amount=amount, currency=currency)
	return jsonify({'ok': True, 'approval': a.to_dict()}), 201


@employee_bp.route('/employee/api/approvals', methods=['GET'])
@require_role('Employee')
def employee_api_list_approvals():
	return render_template('emp_submit_expense.html', current_user_name='Employee', current_user_role='Employee')


@employee_bp.route('/employee/dashboard')
@require_role('Employee')
def employee_dashboard():
	# show employee view; accept email query param for now
	username = request.args.get('username')
	email = request.args.get('email')
	approvals_list = []
	if email:
		items = approvals.list_approvals_by_requestor(email=email)
		# convert to dicts for template
		approvals_list = [a.to_dict() for a in items]
	return render_template('emp_view_expense.html', approvals=approvals_list, current_user_name=username or 'Employee', current_user_role='Employee')


@employee_bp.route('/employee/submit', methods=['POST'])
@require_role('Employee')
def submit_expense():
	"""Handle form-based expense submission from `emp_submit_expense.html`.

	The form doesn't include an email field, so this handler accepts the
	employee's email via either a query parameter `?email=...` on the form page
	or via a hidden input named `email` in the submitted form. If no email is
	provided the handler returns the submit form with an error message.
	"""
	username = request.args.get('username') or request.form.get('username')
	email = request.args.get('email') or request.form.get('email')
	if not email:
		# render the submit form again with an error (so admin/dev can see the issue)
		return render_template('emp_submit_expense.html', error_msg='Email is required to submit an expense.', current_user_name=username or 'Employee', current_user_role='Employee')

	description = request.form.get('description')
	amount = request.form.get('amount')
	currency = request.form.get('currency') or 'USD'

	# handle optional receipt upload
	receipt = None
	receipt_filename = None
	if 'receipt' in request.files:
		receipt = request.files.get('receipt')
		if receipt and receipt.filename:
			import os
			uploads_dir = os.path.join(os.getcwd(), 'static', 'uploads')
			os.makedirs(uploads_dir, exist_ok=True)
			# sanitize filename lightly
			from werkzeug.utils import secure_filename
			fname = secure_filename(receipt.filename)
			path = os.path.join(uploads_dir, fname)
			receipt.save(path)
			receipt_filename = fname

	# Convert amount where possible
	try:
		amount_val = float(amount) if amount else None
	except Exception:
		amount_val = None

	a = approvals.create_approval(requestor_email=email, description=description, category=None, amount=amount_val, currency=currency, receipt_filename=receipt_filename)

	# After creating the approval redirect to the employee dashboard
	return redirect(url_for('employee.employee_dashboard', email=email, username=username))


