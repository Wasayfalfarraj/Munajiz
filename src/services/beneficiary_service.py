"""
خدمة "معاملاتي" — قائمة معاملات المستفيد التجريبي الثابت (DEMO-90001).
المشروع لا يحتوي نظام تسجيل دخول حقيقي، فنعتمد مستفيد تجريبي واحد ثابت
تُنشئ له seed.py نفس المعاملات في كل مرة، عشان تجربة العرض تكون متكررة وموثوقة.
"""
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config.db import get_connection  # noqa: E402

DEMO_USER_ID = 'DEMO-90001'

STATUS_LABELS_AR = {
    'completed': 'تم حل التعثر',
    'blocked': 'متعثرة',
    'pending_employee': 'تحتاج مراجعة موظف',
}

SERVICE_LABELS_AR = {
    'renew_residency_individual': 'تجديد إقامة',
    'renew_residency_business': 'تجديد إقامة عمالية',
    'renew_identity': 'تجديد هوية',
    'renew_passport': 'تجديد جواز',
}


def get_my_transactions():
    conn = get_connection()
    cur = conn.cursor()
    rows = cur.execute(
        """SELECT t.id, t.service_type, t.status, c.code, c.reason_ar
           FROM transactions t
           LEFT JOIN cases c ON c.transaction_id = t.id AND c.status = 'open'
           WHERE t.user_id = ?
           ORDER BY t.created_at DESC, t.id""",
        (DEMO_USER_ID,),
    ).fetchall()
    conn.close()

    result = []
    for r in rows:
        result.append({
            'id': r['id'],
            'service_label': SERVICE_LABELS_AR.get(r['service_type'], r['service_type']),
            'status': r['status'],
            'status_label': STATUS_LABELS_AR.get(r['status'], r['status']),
            'exception_code': r['code'],
            'cause': r['reason_ar'],
        })
    return result
