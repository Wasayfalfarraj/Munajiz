import os
import sys
import subprocess

from flask import Flask, jsonify, send_from_directory

sys.path.append(os.path.dirname(__file__))
from routes.cases_routes import cases_bp  # noqa: E402
from routes.transactions_routes import transactions_bp  # noqa: E402
from routes.forecast_routes import forecast_bp  # noqa: E402
from routes.dashboard_routes import dashboard_bp  # noqa: E402
from routes.codes_routes import codes_bp  # noqa: E402
from routes.beneficiary_routes import beneficiary_bp  # noqa: E402

# مجلد الواجهة — حطي نسخة من index.html هنا (munjiz-backend/frontend/index.html)
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), '..', 'frontend')

# نبني قاعدة البيانات من الصفر في كل مرة يشتغل فيها السيرفر — هذا يضمن
# دايمًا نفس البيانات الطازجة (بما فيها الحل الآلي المسبق)، حتى لو بقي
# ملف قاعدة بيانات قديم من نشر سابق على القرص
seed_path = os.path.join(os.path.dirname(__file__), 'seed', 'seed.py')
subprocess.run([sys.executable, seed_path], check=True)

app = Flask(__name__)
app.register_blueprint(cases_bp)
app.register_blueprint(transactions_bp)
app.register_blueprint(forecast_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(codes_bp)
app.register_blueprint(beneficiary_bp)


# CORS يدوي — يفيد أثناء التطوير المحلي، لا يضر حتى لو صار كل شي من نفس السيرفر
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response


@app.route('/')
def serve_frontend():
    return send_from_directory(FRONTEND_DIR, 'index.html')


@app.route('/api/health')
def health():
    return jsonify({'status': 'ok', 'service': 'munjiz-backend'})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
