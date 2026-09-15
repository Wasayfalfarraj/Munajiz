import os
import sys

from flask import Blueprint, jsonify

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from services.codes_service import get_codes  # noqa: E402

codes_bp = Blueprint('codes', __name__)


@codes_bp.route('/api/codes', methods=['GET'])
def codes():
    return jsonify(get_codes())
