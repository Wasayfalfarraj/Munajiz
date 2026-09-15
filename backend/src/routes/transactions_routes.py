import os
import sys

from flask import Blueprint, jsonify

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from services.transactions_service import get_transaction_detail, retry_transaction  # noqa: E402
from services.resolution_service import diagnose_transaction, resolve_transaction, get_history  # noqa: E402

transactions_bp = Blueprint('transactions', __name__)


@transactions_bp.route('/api/transactions/<transaction_id>', methods=['GET'])
def transaction_detail(transaction_id):
    detail = get_transaction_detail(transaction_id)
    if not detail:
        return jsonify({'error': 'المعاملة غير موجودة'}), 404
    return jsonify(detail)


@transactions_bp.route('/api/transactions/<transaction_id>/retry', methods=['POST'])
def retry(transaction_id):
    body, status_code = retry_transaction(transaction_id)
    return jsonify(body), status_code


@transactions_bp.route('/api/transactions/<transaction_id>/diagnosis', methods=['GET'])
def diagnosis(transaction_id):
    result = diagnose_transaction(transaction_id)
    if result is None:
        return jsonify({'error': 'المعاملة غير موجودة'}), 404
    return jsonify(result)


@transactions_bp.route('/api/transactions/<transaction_id>/diagnose', methods=['POST'])
def diagnose(transaction_id):
    # نفس منطق القراءة — POST هنا فقط لمطابقة الشكل المطلوب (فعل يُطلب تنفيذه)
    result = diagnose_transaction(transaction_id)
    if result is None:
        return jsonify({'error': 'المعاملة غير موجودة'}), 404
    return jsonify(result)


@transactions_bp.route('/api/transactions/<transaction_id>/resolve', methods=['POST'])
def resolve(transaction_id):
    body, status_code = resolve_transaction(transaction_id)
    return jsonify(body), status_code


@transactions_bp.route('/api/transactions/<transaction_id>/history', methods=['GET'])
def history(transaction_id):
    return jsonify(get_history(transaction_id))
