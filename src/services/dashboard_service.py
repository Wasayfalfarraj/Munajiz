import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config.db import get_connection  # noqa: E402
from services.forecast_service import get_alert  # noqa: E402


def get_stats():
    conn = get_connection()
    cur = conn.cursor()

    total = cur.execute("SELECT COUNT(*) c FROM transactions").fetchone()['c']
    completed = cur.execute("SELECT COUNT(*) c FROM transactions WHERE status='completed'").fetchone()['c']
    needs_employee = cur.execute(
        "SELECT COUNT(*) c FROM cases WHERE status='open' AND needs_employee=1"
    ).fetchone()['c']
    open_cases = cur.execute("SELECT COUNT(*) c FROM cases WHERE status='open'").fetchone()['c']
    auto_closed = cur.execute(
        "SELECT COUNT(*) c FROM retry_history WHERE result='success'"
    ).fetchone()['c']
    ready_for_retry = cur.execute(
        "SELECT COUNT(*) c FROM transactions WHERE status='blocked'"
    ).fetchone()['c']

    today_volume_row = cur.execute(
        """SELECT volume FROM forecast_data
           WHERE branch='الرياض شمال' AND service_type='renew_residency'
           ORDER BY date DESC LIMIT 1"""
    ).fetchone()
    today_volume = today_volume_row['volume'] if today_volume_row else 0

    # ── أسباب التعثر الأكثر تكراراً (لقائمة "أسباب التعثر اليوم") ─────────
    # نجمع حسب نص السبب المحدد نفسه، مو حسب كود منجز — لأن نفس الكود (MUN-422 مثلاً)
    # يغطي أسباب مختلفة تماماً (جواز، تأمين، رسوم...)
    reason_rows = cur.execute(
        """SELECT reason_ar, COUNT(*) c
           FROM cases GROUP BY reason_ar ORDER BY c DESC LIMIT 5"""
    ).fetchall()
    max_count = reason_rows[0]['c'] if reason_rows else 1
    reasons = [
        {
            'title_ar': r['reason_ar'],
            'count': r['c'],
            'bar_pct': round(r['c'] / max_count * 100),
        }
        for r in reason_rows
    ]

    # ── آخر الأحداث (من سجل إعادة المحاولة الفعلي) ─────────────────────────
    event_rows = cur.execute(
        """SELECT transaction_id, attempted_at, result, note_ar
           FROM retry_history ORDER BY attempted_at DESC LIMIT 5"""
    ).fetchall()
    events = [
        {
            'transaction_id': e['transaction_id'],
            'time': e['attempted_at'],
            'result': e['result'],
            'note_ar': e['note_ar'],
        }
        for e in event_rows
    ]

    # ── الكود الأكثر شيوعاً اليوم ─────────────────────────────────────────
    top_code_row = cur.execute(
        """SELECT c.code, fc.name_ar, COUNT(*) n
           FROM cases c JOIN failure_codes fc ON c.code = fc.code
           WHERE c.status = 'open'
           GROUP BY c.code ORDER BY n DESC LIMIT 1"""
    ).fetchone()

    # ── أعلى 5 أكواد استثناء حالياً (لبطاقات "أكثر الاستثناءات شيوعاً") ──────
    top_codes_rows = cur.execute(
        """SELECT fc.code, fc.name_ar, COUNT(*) n
           FROM cases c JOIN failure_codes fc ON c.code = fc.code
           WHERE c.status = 'open'
           GROUP BY fc.code ORDER BY n DESC LIMIT 5"""
    ).fetchall()
    top_codes = [{'code': r['code'], 'name_ar': r['name_ar'], 'count': r['n']} for r in top_codes_rows]

    conn.close()

    # ── يحتاج انتباه — ملخّص مضغوط لأهم ٤ نقاط، كل شي مبني على بيانات حقيقية ─
    attention = []
    if needs_employee:
        attention.append(f"{needs_employee} طلب يحتاج قرار موظف")
    if top_code_row:
        attention.append(f"{top_code_row['code']} ({top_code_row['name_ar']}) هو الاستثناء الأكثر شيوعاً اليوم")
    if ready_for_retry:
        attention.append(f"{ready_for_retry} طلب جاهز لإعادة المحاولة التلقائية")
    alert = get_alert()
    if alert:
        attention.append(f"يُتوقع ارتفاع الحمل بفرع {alert['branch']} يوم {alert['peak_day_ar']}")

    return {
        'total_requests_today': today_volume,
        'auto_closed_count': auto_closed,
        'needs_employee_count': needs_employee,
        'in_progress_count': ready_for_retry,
        'open_cases_count': open_cases,
        'completion_rate_pct': round(completed / total * 100, 1) if total else 0,
        'reasons_breakdown': reasons,
        'recent_events': events,
        'attention_required': attention[:4],
        'top_exceptions': top_codes,
    }
