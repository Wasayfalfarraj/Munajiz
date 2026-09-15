import os
import sys
import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config.db import get_connection  # noqa: E402


def compute_digital_twin(txn_status, case):
    """يبني تمثيل مراحل رحلة المعاملة (Digital Twin) من حالتها الفعلية بقاعدة البيانات."""
    stages_def = [
        ('submitted', 'تقديم الطلب'),
        ('verification', 'التحقق من المعلومات'),
        ('eligibility', 'فحص الأهلية'),
        ('processing', 'المعالجة الحكومية'),
        ('employee_decision', 'قرار الموظف'),
        ('completed', 'مكتملة'),
    ]

    if txn_status == 'completed':
        states = ['done', 'done', 'done', 'done', 'done', 'done']
        current = 'completed'
        progress = 100
    elif txn_status == 'pending_employee':
        states = ['done', 'done', 'done', 'done', 'active', 'pending']
        current = 'employee_decision'
        progress = 80
    else:  # blocked
        states = ['done', 'done', 'done', 'blocked', 'pending', 'pending']
        current = 'processing'
        progress = 55

    stages = [
        {'key': k, 'label_ar': label, 'state': s}
        for (k, label), s in zip(stages_def, states)
    ]

    return {
        'stages': stages,
        'current_stage': current,
        'progress_pct': progress,
        'exception_code': case['code'] if case else None,
        'exception_reason': case['reason_ar'] if case else None,
        'next_action': case['recommendation_ar'] if case else None,
        'requires_employee': bool(case['needs_employee']) if case else False,
    }


def get_transaction_detail(tid):
    conn = get_connection()
    cur = conn.cursor()

    txn = cur.execute(
        """SELECT t.*, u.name, u.employer_name FROM transactions t
           JOIN users u ON t.user_id = u.id WHERE t.id = ?""", (tid,)
    ).fetchone()
    if not txn:
        conn.close()
        return None

    checks = cur.execute(
        "SELECT * FROM requirement_checks WHERE transaction_id = ?", (tid,)
    ).fetchall()
    failing = [dict(c) for c in checks if c['status'] != 'valid']

    case = cur.execute(
        """SELECT * FROM cases WHERE transaction_id = ? AND status = 'open'""", (tid,)
    ).fetchone()

    # زملاء بنفس المنشأة عندهم معاملات متعثرة أيضاً — لقائمة "الإصلاح الجماعي"
    # نجيب الإجراء الموصى به من قاموس الأكواد نفسه (code فريد الآن، 6 أكواد بس)
    bulk = []
    if txn['employer_name']:
        rows = cur.execute(
            """SELECT t2.id, u2.name, c2.reason_ar, fc.recommended_action_ar
               FROM transactions t2
               JOIN users u2 ON t2.user_id = u2.id
               LEFT JOIN cases c2 ON c2.transaction_id = t2.id AND c2.status = 'open'
               LEFT JOIN failure_codes fc ON c2.code = fc.code
               WHERE u2.employer_name = ? AND t2.status IN ('blocked', 'pending_employee')
                     AND t2.id != ?
               LIMIT 10""",
            (txn['employer_name'], tid)
        ).fetchall()
        for r in rows:
            bulk.append({
                'name': r['name'],
                'reason': r['reason_ar'],
                'action': r['recommended_action_ar'] or 'مراجعة',
            })

    digital_twin = compute_digital_twin(txn['status'], case)

    conn.close()
    return {
        'id': txn['id'],
        'status': txn['status'],
        'user_name': txn['name'],
        'employer_name': txn['employer_name'],
        'failing_requirements': [
            {'type': f['requirement_type'], 'detail': f['detail_ar']} for f in failing
        ],
        'code': case['code'] if case else None,
        'reason_ar': case['reason_ar'] if case else None,
        'recommendation_ar': case['recommendation_ar'] if case else None,
        'retry_available': bool(case['retry_available']) if case else False,
        'bulk_related': bulk,
        'digital_twin': digital_twin,
    }


def retry_transaction(tid):
    """
    نقطة النهاية القديمة /retry ما زالت تشتغل بنفس الشكل اللي تتوقعه الواجهة الحالية،
    لكن داخليًا صارت تستدعي محرك الحل الحقيقي (resolution_service) بدل إعادة المحاولة الساذجة.
    """
    from services.resolution_service import resolve_transaction

    conn = get_connection()
    cur = conn.cursor()
    txn = cur.execute("SELECT status FROM transactions WHERE id = ?", (tid,)).fetchone()
    conn.close()

    if not txn:
        return {'error': 'المعاملة غير موجودة'}, 404
    if txn['status'] not in ('blocked',):
        return {'error': 'لا توجد إعادة محاولة متاحة لهذه المعاملة'}, 400

    result, status_code = resolve_transaction(tid)
    return {'transaction_id': tid, 'status': result.get('status', txn['status'])}, status_code
