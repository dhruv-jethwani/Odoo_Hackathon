from . import employee_bp
from flask import request, render_template, redirect, url_for, make_response
from db import users
from werkzeug.security import generate_password_hash, check_password_hash

from flask import jsonify
from db import approvals as approvals




@employee_bp.route('/employee/api/approvals', methods=['POST'])
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
def employee_api_list_approvals():
	email = request.args.get('email')
	if not email:
		return jsonify({'ok': False, 'error': 'email query param required'}), 400
	status = request.args.get('status')
	limit = request.args.get('limit', default=200, type=int)
	items = approvals.list_approvals_by_requestor(email=email, status=status, limit=limit)
	return jsonify({'ok': True, 'approvals': [i.to_dict() for i in items]})


