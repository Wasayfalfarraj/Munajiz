import os
import sys

from flask import Blueprint, jsonify, request

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from services.forecast_service import get_forecast, get_alert, simulate_disruption, get_continuity_status  # noqa: E402

forecast_bp = Blueprint('forecast', __name__)


@forecast_bp.route('/api/forecast', methods=['GET'])
def forecast():
    data = get_forecast()
    if not data:
        return jsonify({'error': 'لا توجد بيانات تاريخية بعد — شغّلي seed.py'}), 404
    return jsonify(data)


@forecast_bp.route('/api/forecast/alert', methods=['GET'])
def alert():
    return jsonify(get_alert())  # يرجّع null إذا ما فيه تجاوز للطاقة


@forecast_bp.route('/api/forecast/continuity', methods=['GET'])
def continuity():
    return jsonify(get_continuity_status())


@forecast_bp.route('/api/forecast/simulate', methods=['POST'])
def simulate():
    body = request.get_json(silent=True) or {}
    kind = body.get('type', 'payment')
    result, status_code = simulate_disruption(kind)
    return jsonify(result), status_code
