import os
import sys
from collections import defaultdict
from datetime import date as date_cls, timedelta

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config.db import get_connection  # noqa: E402

WEEKDAY_AR = ['الأحد', 'الاثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت']

CAPACITY_NORMAL = 18000
CAPACITY_EXTENDED = 22000


def get_forecast(branch='الرياض شمال', service_type='renew_residency'):
    conn = get_connection()
    cur = conn.cursor()
    rows = cur.execute(
        """SELECT date, volume FROM forecast_data
           WHERE branch = ? AND service_type = ? ORDER BY date ASC""",
        (branch, service_type)
    ).fetchall()
    conn.close()

    if not rows:
        return None

    # ── الطريقة: متوسط كل يوم أسبوع (Weekday Average) ────────────────────
    weekday_totals = defaultdict(list)
    for r in rows:
        d = date_cls.fromisoformat(r['date'])
        weekday_totals[d.weekday()].append(r['volume'])
    weekday_avg = {wd: sum(v) / len(v) for wd, v in weekday_totals.items()}

    # ── معامل الاتجاه: متوسط آخر 14 يوم مقابل الـ 14 يوم اللي قبلها ──────
    volumes = [r['volume'] for r in rows]
    last14 = volumes[-14:]
    prev14 = volumes[-28:-14] if len(volumes) >= 28 else last14
    recent_avg = sum(last14) / len(last14)
    prev_avg = sum(prev14) / len(prev14) if prev14 else recent_avg
    trend_ratio = (recent_avg / prev_avg) if prev_avg else 1.0
    trend_ratio = max(0.8, min(trend_ratio, 1.5))  # حدود معقولة تمنع قفزات غريبة

    last_date = date_cls.fromisoformat(rows[-1]['date'])
    forecast_days = []
    peak = None
    for i in range(1, 7):
        d = last_date + timedelta(days=i)
        wd = d.weekday()  # Mon=0 .. Sun=6
        base = weekday_avg.get(wd, recent_avg)
        predicted = round(base * trend_ratio)

        if predicted >= CAPACITY_EXTENDED:
            risk = 'high'
        elif predicted >= CAPACITY_NORMAL:
            risk = 'med'
        else:
            risk = 'low'

        day_info = {
            'date': d.isoformat(),
            'weekday_ar': WEEKDAY_AR[(wd + 1) % 7],  # تحويل ترتيب Python لترتيب أحد..سبت
            'predicted_volume': predicted,
            'risk': risk,
        }
        forecast_days.append(day_info)
        if peak is None or predicted > peak['predicted_volume']:
            peak = day_info

    overcapacity_pct = round((peak['predicted_volume'] - CAPACITY_NORMAL) / CAPACITY_NORMAL * 100)

    return {
        'branch': branch,
        'service_type': service_type,
        'capacity_normal': CAPACITY_NORMAL,
        'capacity_extended': CAPACITY_EXTENDED,
        'forecast_days': forecast_days,
        'peak_day': peak,
        'overcapacity_pct': overcapacity_pct,
        'method_ar': 'متوسط كل يوم أسبوع من التاريخ + معامل اتجاه من آخر 28 يوماً',
    }


def get_alert():
    """ينبني على نفس التوقع — يرجّع تنبيه فقط إذا فيه يوم يتجاوز الطاقة الموسّعة."""
    forecast = get_forecast()
    if not forecast:
        return None
    peak = forecast['peak_day']
    if peak['risk'] != 'high':
        return None
    return {
        'branch': forecast['branch'],
        'peak_day_ar': peak['weekday_ar'],
        'peak_volume': peak['predicted_volume'],
        'overcapacity_pct': forecast['overcapacity_pct'],
        'message_ar': (
            f"موجة طلبات متوقعة يوم {peak['weekday_ar']} بحجم {peak['predicted_volume']:,} طلب "
            f"— تتجاوز الطاقة المتاحة بنسبة {forecast['overcapacity_pct']}%."
        ),
    }


def get_continuity_status():
    """حالة استمرارية العمل — محسوبة من بيانات حقيقية، مو نص ثابت."""
    conn = get_connection()
    cur = conn.cursor()
    integration_open = cur.execute(
        """SELECT COUNT(*) c FROM cases
           WHERE status='open' AND code IN ('MUN-301','MUN-501')"""
    ).fetchone()['c']
    conn.close()

    alert = get_alert()

    if integration_open >= 10:
        return {'status': 'integration_issue', 'label_ar': 'مشكلة تكامل',
                'detail_ar': f'{integration_open} حالة متأثرة بتعثر تكامل حالياً'}
    if alert:
        return {'status': 'elevated_load', 'label_ar': 'حمل مرتفع',
                'detail_ar': alert['message_ar']}
    return {'status': 'stable', 'label_ar': 'مستقر', 'detail_ar': 'لا توجد مؤشرات ضغط أو تعثر تكامل حالياً'}


def simulate_disruption(kind):
    """محاكاة فقط — لا تتصل بأي نظام حقيقي. الأرقام مبنية على آخر حجم فعلي بالبيانات."""
    conn = get_connection()
    cur = conn.cursor()
    row = cur.execute(
        """SELECT volume FROM forecast_data
           WHERE branch = 'الرياض شمال' AND service_type = 'renew_residency'
           ORDER BY date DESC LIMIT 1"""
    ).fetchone()
    conn.close()
    current_volume = row['volume'] if row else 18000

    if kind == 'payment':
        affected = round(current_volume * 0.16)
        return {
            'kind': kind,
            'message_ar': (
                f"انقطاع بوابة الدفع — تحويل {affected:,} طلب تلقائياً لبوابة احتياطية، "
                f"وإشعار المستفيدين المتأثرين بعدم التأثر على طلبهم."
            ),
            'rto_minutes': 8,
        }, 200
    if kind == 'passport':
        unaffected_pct = 68
        return {
            'kind': kind,
            'message_ar': (
                f"تعطل التحقق من الجواز — إيقاف مؤقت لطلبات تجديد الجواز فقط، "
                f"واستمرار {unaffected_pct}% من الطلبات الأخرى بلا تأثير."
            ),
            'rto_minutes': 22,
        }, 200
    if kind == 'full':
        return {
            'kind': kind,
            'message_ar': (
                f"انقطاع كامل للفرع — تحويل جميع الطلبات ({current_volume:,} طلب) لفروع بديلة، "
                f"وتفعيل Playbook الطوارئ."
            ),
            'rto_minutes': 28,
        }, 200
    return {'error': 'نوع محاكاة غير معروف'}, 400
