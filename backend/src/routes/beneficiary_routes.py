import os
import sys

from flask import Blueprint, jsonify

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from services.beneficiary_service import get_my_transactions  # noqa: E402

beneficiary_bp = Blueprint('beneficiary', __name__)


@beneficiary_bp.route('/api/beneficiary/transactions', methods=['GET'])
def my_transactions():
    return jsonify(get_my_transactions())
