"""
محرك حل الاستثناءات — القلب الوظيفي لمنجز.
لا يكتفي بإعادة المحاولة: يشخّص السبب الجذري، يحدد نوع الحل المناسب من
قواعد جدول failure_codes، ينفّذه، يتحقق من النتيجة، ثم يكمل المعاملة أو
يصعّدها لموظف — ويسجّل كل خطوة بجدول transaction_history.
"""
import os
import sys
import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config.db import get_connection  # noqa: E402
from services import integration_service  # noqa: E402


def _log(cur, tid, event, actor, desc):
    cur.execute(
        """INSERT INTO transaction_history (transaction_id, event, actor, description_ar, created_at)
           VALUES (?, ?, ?, ?, ?)""",
        (tid, event, actor, desc, datetime.datetime.now().isoformat(timespec='seconds')),
    )


def _get_open_case(cur, tid):
    return cur.execute(
        "SELECT * FROM cases WHERE transaction_id = ? AND status = 'open'", (tid,)
    ).fetchone()


def _get_rule(cur, code):
    return cur.execute("SELECT * FROM failure_codes WHERE code = ?", (code,)).fetchone()


def diagnose_transaction(tid):
    """تشخيص للقراءة فقط — لا ينفّذ أي إجراء، فقط يوضّح السبب والحل المقترح."""
    conn = get_connection()
    cur = conn.cursor()

    txn = cur.execute("SELECT * FROM transactions WHERE id = ?", (tid,)).fetchone()
    if not txn:
        conn.close()
        return None

    case = _get_open_case(cur, tid)
    if not case:
        conn.close()
        return {
            'transaction_id': tid, 'exception_code': None, 'exception_name': None,
            'root_cause': None, 'evidence': [], 'affected_component': None,
            'corrective_action': None, 'resolution_type': None,
            'automation_allowed': None, 'employee_required': None, 'verification_required': None,
            'recommendation': 'لا يوجد استثناء مفتوح لهذه المعاملة حالياً.',
        }

    rule = _get_rule(cur, case['code'])
    evidence_rows = cur.execute(
        """SELECT requirement_type, status, detail_ar FROM requirement_checks
           WHERE transaction_id = ? AND status != 'valid'""", (tid,)
    ).fetchall()
    evidence = [dict(e) for e in evidence_rows]

    conn.close()
    return {
        'transaction_id': tid,
        'exception_code': case['code'],
        'exception_name': rule['name_ar'],
        'root_cause': rule['root_cause_ar'],
        'evidence': evidence,
        'affected_component': evidence[0]['requirement_type'] if evidence else None,
        'corrective_action': rule['recommended_action_ar'],
        'resolution_type': rule['resolution_type'],
        'automation_allowed': bool(rule['automatic_resolution_allowed']),
        'employee_required': bool(rule['employee_intervention_required']),
        'verification_required': bool(rule['verification_required']),
        'recommendation': rule['recommended_action_ar'],
    }


def _execute_remediation(cur, tid, case, rule):
    """ينفّذ إجراء التصحيح الفعلي حسب resolution_type — ويرجّع (event, وصف عربي)."""
    rtype = rule['resolution_type']

    if rtype == 'REQUIREMENT_COMPLETION':
        cur.execute(
            "UPDATE requirement_checks SET status='valid', days_remaining=NULL "
            "WHERE transaction_id=? AND status!='valid'", (tid,)
        )
        return 'requirement_completed', 'تم استكمال الشرط الناقص من قبل المستفيد وإعادة فحصه'

    if rtype == 'DATA_SYNCHRONIZATION':
        integration_service.synchronize('conflicting_field')
        cur.execute(
            "UPDATE requirement_checks SET status='valid' WHERE transaction_id=? AND status!='valid'", (tid,)
        )
        return 'data_synchronization_completed', 'تمت مزامنة البيانات مع المصدر المعتمد وإعادة التحقق'

    if rtype == 'DATA_REVALIDATION':
        integration_service.validate('transaction_data')
        cur.execute(
            "UPDATE requirement_checks SET status='valid' WHERE transaction_id=? AND status!='valid'", (tid,)
        )
        return 'revalidation_completed', 'أُعيد التحقق من البيانات بعد تحديثها'

    if rtype == 'TEMPORARY_SERVICE_RECOVERY':
        result = integration_service.check_integration_status('linked_service')
        if result == integration_service.SUCCESS:
            cur.execute(
                "UPDATE requirement_checks SET status='valid' WHERE transaction_id=? AND status!='valid'", (tid,)
            )
            return 'service_recovery_completed', 'تعافت الخدمة المرتبطة وأُعيد تنفيذ العملية المتأثرة'
        return 'service_recovery_pending', 'الخدمة المرتبطة ما زالت غير متاحة'

    if rtype == 'SAFE_RETRY':
        return 'reconciliation_completed', 'تمت مطابقة الحالة الفعلية للطلب قبل أي إعادة إرسال — لا تكرار'

    if rtype == 'DUPLICATE_RESOLUTION':
        txn = cur.execute("SELECT user_id, service_type FROM transactions WHERE id=?", (tid,)).fetchone()
        original = integration_service.search_existing_transaction(cur, txn['user_id'], txn['service_type'], tid)
        if original:
            return 'duplicate_linked', f'تم ربط الحالة بالمعاملة الصحيحة الموجودة رقم {original} ومنع التكرار'
        cur.execute(
            "UPDATE requirement_checks SET status='valid' WHERE transaction_id=? AND status!='valid'", (tid,)
        )
        return 'duplicate_not_found', 'لم يُعثر على معاملة سابقة مطابقة — اعتُمدت هذه المعاملة كأصلية'

    return 'corrective_action_completed', 'نُفّذ إجراء تصحيحي عام'


def _verify(cur, tid):
    remaining = cur.execute(
        "SELECT COUNT(*) c FROM requirement_checks WHERE transaction_id=? AND status!='valid'", (tid,)
    ).fetchone()['c']
    return remaining == 0


def resolve_transaction(tid):
    """
    التدفق الكامل: تشخيص → سبب جذري → إجراء تصحيحي → تنفيذ → تحقق → إكمال/تصعيد.
    يُستخدم من endpoint /resolve، ومن /retry القديم للتوافق مع الواجهة الحالية.
    """
    conn = get_connection()
    cur = conn.cursor()
    now = datetime.datetime.now().isoformat(timespec='seconds')

    txn = cur.execute("SELECT * FROM transactions WHERE id = ?", (tid,)).fetchone()
    if not txn:
        conn.close()
        return {'error': 'المعاملة غير موجودة'}, 404

    case = _get_open_case(cur, tid)
    if not case:
        conn.close()
        already_resolved = txn['status'] == 'completed'
        return {
            'transaction_id': tid, 'status': txn['status'], 'resolved': already_resolved,
            'employee_required': False,
            'message': 'المعاملة مكتملة بالفعل' if already_resolved else 'لا يوجد استثناء مفتوح لهذه المعاملة',
        }, 200

    rule = _get_rule(cur, case['code'])
    _log(cur, tid, 'diagnosis_started', 'system', f"بدء تشخيص الاستثناء {case['code']}")
    root_cause = rule['root_cause_ar']
    cur.execute("UPDATE cases SET root_cause_ar = ? WHERE id = ?", (root_cause, case['id']))
    _log(cur, tid, 'root_cause_identified', 'system', root_cause)

    # ── قرار موظف مباشرة (بدون أي محاولة آلية) ────────────────────────────
    if not rule['automatic_resolution_allowed']:
        _log(cur, tid, 'employee_review_required', 'system', 'الحالة تتطلب صلاحية بشرية — لا أتمتة')
        conn.commit()
        conn.close()
        return {
            'transaction_id': tid, 'status': txn['status'], 'resolved': False,
            'employee_required': True, 'root_cause': root_cause,
            'message': 'يحتاج قرار موظف — تم تجهيز الملف',
        }, 200

    # ── تنفيذ الإجراء التصحيحي الفعلي ──────────────────────────────────────
    _log(cur, tid, 'corrective_action_started', 'system', rule['recommended_action_ar'])
    event, action_desc = _execute_remediation(cur, tid, case, rule)
    cur.execute("UPDATE cases SET corrective_action_ar = ? WHERE id = ?", (action_desc, case['id']))
    _log(cur, tid, event, 'system', action_desc)

    # ── التحقق من النتيجة ──────────────────────────────────────────────────
    if rule['verification_required']:
        verified = _verify(cur, tid)
        verification_desc = 'تم التحقق من استيفاء الشرط بنجاح' if verified else 'فشل التحقق — ما زال هناك شرط غير مستوفى'
        cur.execute("UPDATE cases SET verification_result_ar = ? WHERE id = ?", (verification_desc, case['id']))
        _log(cur, tid, 'verification_success' if verified else 'verification_failed', 'system', verification_desc)
    else:
        verified = True

    if verified:
        cur.execute("UPDATE transactions SET status = 'completed' WHERE id = ?", (tid,))
        cur.execute("UPDATE cases SET status = 'closed' WHERE id = ?", (case['id'],))
        _log(cur, tid, 'transaction_resumed', 'system', 'استؤنفت المعاملة بعد التحقق من الحل')
        _log(cur, tid, 'resolved', 'system', 'تم حل الاستثناء')
        cur.execute(
            """INSERT INTO retry_history (transaction_id, attempted_at, result, note_ar)
               VALUES (?, ?, 'success', ?)""", (tid, now, action_desc)
        )
        result = {
            'transaction_id': tid, 'status': 'completed', 'resolved': True, 'employee_required': False,
            'root_cause': root_cause, 'corrective_action': action_desc, 'verification': 'تم التحقق من تطابق البيانات',
        }
    else:
        new_count = (case['retry_count'] or 0) + 1
        cur.execute("UPDATE cases SET retry_count = ? WHERE id = ?", (new_count, case['id']))
        max_attempts = rule['max_attempts']
        if max_attempts is not None and new_count >= max_attempts:
            cur.execute("UPDATE cases SET needs_employee = 1 WHERE id = ?", (case['id'],))
            _log(cur, tid, 'escalated_to_employee', 'system', 'تجاوزت الحالة الحد الأقصى لمحاولات الحل الآلي')
            employee_required = True
        else:
            employee_required = False
            _log(cur, tid, 'retry_scheduled', 'system', 'بانتظار محاولة حل تالية')
        cur.execute(
            """INSERT INTO retry_history (transaction_id, attempted_at, result, note_ar)
               VALUES (?, ?, 'failed', ?)""", (tid, now, verification_desc)
        )
        result = {
            'transaction_id': tid, 'status': txn['status'], 'resolved': False,
            'employee_required': employee_required, 'root_cause': root_cause, 'corrective_action': action_desc,
        }

    conn.commit()
    conn.close()
    return result, 200


def get_history(tid):
    conn = get_connection()
    cur = conn.cursor()
    rows = cur.execute(
        """SELECT event, actor, description_ar, created_at FROM transaction_history
           WHERE transaction_id = ? ORDER BY id ASC""", (tid,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
