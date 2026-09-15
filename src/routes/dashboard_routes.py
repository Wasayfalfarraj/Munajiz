import os
import sys

from flask import Blueprint, jsonify

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from services.dashboard_service import get_stats  # noqa: E402

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/api/dashboard/stats', methods=['GET'])
def stats():
    return jsonify(get_stats())
