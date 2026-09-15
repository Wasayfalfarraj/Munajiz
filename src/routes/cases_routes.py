import os
import sys

from flask import Blueprint, jsonify, request

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from services.cases_service import (  # noqa: E402
    get_cases, close_case, transfer_case, get_case_detail, apply_employee_decision,
)

cases_bp = Blueprint('cases', __name__)


@cases_bp.route('/api/cases', methods=['GET'])
def list_cases():
    case_type = request.args.get('type', 'all')
    return jsonify(get_cases(case_type))


@cases_bp.route('/api/cases/<transaction_id>/close', methods=['POST'])
def resolve(transaction_id):
    ok = close_case(transaction_id)
    if not ok:
        return jsonify({'error': 'الحالة غير موجودة'}), 404
    return jsonify({'transaction_id': transaction_id, 'status': 'closed'})


@cases_bp.route('/api/cases/<transaction_id>/transfer', methods=['POST'])
def transfer(transaction_id):
    ok = transfer_case(transaction_id)
    if not ok:
        return jsonify({'error': 'الحالة غير موجودة'}), 404
    return jsonify({'transaction_id': transaction_id, 'status': 'transferred'})


@cases_bp.route('/api/cases/<transaction_id>/detail', methods=['GET'])
def detail(transaction_id):
    result = get_case_detail(transaction_id)
    if result is None:
        return jsonify({'error': 'المعاملة غير موجودة'}), 404
    return jsonify(result)


@cases_bp.route('/api/cases/<transaction_id>/decision', methods=['POST'])
def decision(transaction_id):
    body = request.get_json(silent=True) or {}
    d = body.get('decision')
    if d not in ('approve', 'reject', 'review'):
        return jsonify({'error': 'قرار غير صالح — استخدمي approve أو reject أو review'}), 400
    result, status_code = apply_employee_decision(transaction_id, d)
    return jsonify(result), status_code
