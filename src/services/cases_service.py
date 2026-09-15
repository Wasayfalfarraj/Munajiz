import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config.db import get_connection  # noqa: E402

# تسمية عربية لكل تصنيف — خدمات وزارية، بدون أي مصطلحات أمنية/قضائية
BUCKET_LABELS = {
    'passport_identity': 'الجوازات والهوية',
    'residency_address': 'الإقامة والعنوان الوطني',
    'other': 'خدمات أخرى',
}

# ترتيب الأولوية من الأعلى للأقل (نفس منطق "غير مرتّب حسب من وصل أولاً")
PRIORITY_ORDER = "CASE c.priority WHEN 'high' THEN 0 WHEN 'med' THEN 1 ELSE 2 END"


def get_cases(bucket='all'):
    conn = get_connection()
    cur = conn.cursor()

    # طابور الموظف يعرض فقط الحالات اللي فعلاً تحتاج قرار موظف —
    # الحالات القابلة لإعادة المحاولة التلقائية ما توصل هنا أصلاً
    query = f"""
        SELECT c.transaction_id, c.code, c.reason_ar, c.bucket, c.priority,
               c.recommendation_ar, c.wait_time,
               u.name, u.employer_name
        FROM cases c
        JOIN transactions t ON c.transaction_id = t.id
        JOIN users u ON t.user_id = u.id
        WHERE c.status = 'open' AND c.needs_employee = 1
    """
    params = []
    if bucket != 'all':
        query += " AND c.bucket = ?"
        params.append(bucket)
    query += f" ORDER BY {PRIORITY_ORDER}, c.id"

    rows = cur.execute(query, params).fetchall()

    result = []
    for r in rows:
        extra = cur.execute(
            """SELECT requirement_type, detail_ar FROM requirement_checks
               WHERE transaction_id = ? AND status = 'valid' LIMIT 2""",
            (r['transaction_id'],),
        ).fetchall()

        facts = [
            {'k': 'السبب', 'v': r['reason_ar'], 'cls': 'red'},
            {'k': 'مدة الانتظار', 'v': r['wait_time'], 'cls': ''},
        ]
        for e in extra:
            facts.append({'k': e['requirement_type'], 'v': e['detail_ar'], 'cls': 'green'})

        result.append({
            'id': r['transaction_id'],
            'name': r['name'],
            'sub': 'إقامة أعمال' if r['employer_name'] else 'إقامة فردية',
            'type': r['bucket'],
            'typeLabel': BUCKET_LABELS.get(r['bucket'], 'خدمات أخرى'),
            'priority': r['priority'],
            'code': r['code'],
            'facts': facts,
            'rec': r['recommendation_ar'],
            'wait': r['wait_time'],
        })

    conn.close()
    return result


def close_case(transaction_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE cases SET status = 'closed' WHERE transaction_id = ?", (transaction_id,))
    conn.commit()
    changed = cur.rowcount
    conn.close()
    return changed > 0


def transfer_case(transaction_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE cases SET status = 'transferred' WHERE transaction_id = ?", (transaction_id,))
    conn.commit()
    changed = cur.rowcount
    conn.close()
    return changed > 0


def get_case_detail(transaction_id):
    """يجمّع كل ما يحتاجه الموظف باتخاذ القرار من شاشة واحدة."""
    from services.resolution_service import diagnose_transaction, get_history

    conn = get_connection()
    cur = conn.cursor()

    txn = cur.execute(
        """SELECT t.*, u.name, u.employer_name FROM transactions t
           JOIN users u ON t.user_id = u.id WHERE t.id = ?""", (transaction_id,)
    ).fetchone()
    if not txn:
        conn.close()
        return None

    case = cur.execute(
        "SELECT * FROM cases WHERE transaction_id = ? AND status = 'open'", (transaction_id,)
    ).fetchone()
    conn.close()

    diagnosis = diagnose_transaction(transaction_id) or {}
    history = get_history(transaction_id)

    return {
        'transaction_id': transaction_id,
        'service_label': txn['service_type'],
        'user_name': txn['name'],
        'employer_name': txn['employer_name'],
        'status': txn['status'],
        'exception_code': case['code'] if case else diagnosis.get('exception_code'),
        'reason_ar': case['reason_ar'] if case else None,
        'root_cause': case['root_cause_ar'] if case and case['root_cause_ar'] else diagnosis.get('root_cause'),
        'corrective_action': case['corrective_action_ar'] if case else None,
        'verification_result': case['verification_result_ar'] if case else None,
        'why_not_automatic': diagnosis.get('recommendation') if case and not case['retry_available'] else None,
        'recommendation': case['recommendation_ar'] if case else diagnosis.get('recommendation'),
        'priority': case['priority'] if case else None,
        'previous_attempts': case['retry_count'] if case else 0,
        'evidence': diagnosis.get('evidence', []),
        'history': history,
    }


def apply_employee_decision(transaction_id, decision):
    """اعتماد | رفض | إعادة للمراجعة — قرار حقيقي يعدّل قاعدة البيانات فعلياً."""
    import datetime
    conn = get_connection()
    cur = conn.cursor()

    case = cur.execute(
        "SELECT * FROM cases WHERE transaction_id = ? AND status = 'open'", (transaction_id,)
    ).fetchone()
    if not case:
        conn.close()
        return {'error': 'لا توجد حالة مفتوحة لهذه المعاملة'}, 404

    now = datetime.datetime.now().isoformat(timespec='seconds')

    if decision == 'approve':
        cur.execute("UPDATE transactions SET status = 'completed' WHERE id = ?", (transaction_id,))
        cur.execute("UPDATE cases SET status = 'closed' WHERE id = ?", (case['id'],))
        cur.execute(
            """INSERT INTO transaction_history (transaction_id, event, actor, description_ar, created_at)
               VALUES (?, 'employee_approved', 'employee', 'اعتمد الموظف الحالة', ?)""",
            (transaction_id, now)
        )
        cur.execute(
            """INSERT INTO transaction_history (transaction_id, event, actor, description_ar, created_at)
               VALUES (?, 'resolved', 'employee', 'تم حل الاستثناء بقرار موظف', ?)""",
            (transaction_id, now)
        )
        new_status = 'completed'

    elif decision == 'reject':
        cur.execute("UPDATE transactions SET status = 'rejected' WHERE id = ?", (transaction_id,))
        cur.execute("UPDATE cases SET status = 'closed' WHERE id = ?", (case['id'],))
        cur.execute(
            """INSERT INTO transaction_history (transaction_id, event, actor, description_ar, created_at)
               VALUES (?, 'employee_rejected', 'employee', 'رفض الموظف الطلب', ?)""",
            (transaction_id, now)
        )
        new_status = 'rejected'

    elif decision == 'review':
        cur.execute(
            """INSERT INTO transaction_history (transaction_id, event, actor, description_ar, created_at)
               VALUES (?, 'sent_back_for_review', 'employee', 'أُعيدت الحالة للمراجعة', ?)""",
            (transaction_id, now)
        )
        new_status = 'pending_employee'

    else:
        conn.close()
        return {'error': 'قرار غير معروف'}, 400

    conn.commit()
    conn.close()
    return {'transaction_id': transaction_id, 'status': new_status, 'decision': decision}, 200
