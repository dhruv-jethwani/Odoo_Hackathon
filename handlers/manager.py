from . import manager_bp
from flask import request, render_template, redirect, url_for, make_response, jsonify
from db import users
from db import approvals as approvals
from werkzeug.security import generate_password_hash, check_password_hash




@manager_bp.route('/manager/api/approvals', methods=['GET'])
def manager_api_list_approvals():
	approver_email = request.args.get('approver_email')
	status = request.args.get('status')
	limit = request.args.get('limit', default=200, type=int)
	if approver_email:
		items = approvals.list_approvals_by_approver(email=approver_email, status=status, limit=limit)
	else:
		# if no approver specified, return pending approvals for managers to pick up
		items = approvals.list_approvals(status='Pending', limit=limit)
	return jsonify({'ok': True, 'approvals': [i.to_dict() for i in items]})


@manager_bp.route('/manager/api/approvals/<int:aid>/decide', methods=['POST'])
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
