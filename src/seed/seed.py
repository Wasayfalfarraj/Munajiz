# ═══════════════════════════════════════════════════════════════════════
# Seed script — يبني الجداول من الصفر ويعبّئها ببيانات صناعية (fictional)
# التشغيل: python src/seed/seed.py
# ═══════════════════════════════════════════════════════════════════════
import os
import sys
import random
from datetime import date, timedelta

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config.db import get_connection, DB_PATH  # noqa: E402

conn = get_connection()
cur = conn.cursor()

# ── 1. Schema ─────────────────────────────────────────────────────────
cur.executescript("""
DROP TABLE IF EXISTS transaction_history;
DROP TABLE IF EXISTS forecast_data;
DROP TABLE IF EXISTS retry_history;
DROP TABLE IF EXISTS cases;
DROP TABLE IF EXISTS requirement_checks;
DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS failure_codes;

-- قاموس أكواد منجز + محرك القواعد بنفس الجدول (مصدر حقيقة واحد، بدون تكرار بكود بايثون)
CREATE TABLE failure_codes (
  code TEXT PRIMARY KEY,
  name_ar TEXT NOT NULL,
  meaning_ar TEXT NOT NULL,
  root_cause_ar TEXT NOT NULL,
  resolution_type TEXT NOT NULL,          -- DATA_REVALIDATION | DATA_SYNCHRONIZATION | REQUIREMENT_COMPLETION |
                                           -- DUPLICATE_RESOLUTION | TEMPORARY_SERVICE_RECOVERY | SAFE_RETRY | EMPLOYEE_REVIEW
  automatic_resolution_allowed INTEGER NOT NULL,
  employee_intervention_required INTEGER NOT NULL,
  verification_required INTEGER NOT NULL,
  max_attempts INTEGER,
  recommended_action_ar TEXT NOT NULL
);

CREATE TABLE users (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  employer_name TEXT,
  service_type TEXT NOT NULL
);

CREATE TABLE transactions (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL REFERENCES users(id),
  service_type TEXT NOT NULL,
  status TEXT NOT NULL,           -- completed | blocked | pending_employee
  branch TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE requirement_checks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  transaction_id TEXT NOT NULL REFERENCES transactions(id),
  requirement_type TEXT NOT NULL,
  status TEXT NOT NULL,            -- valid | expired | outstanding | pending
  detail_ar TEXT NOT NULL,
  days_remaining INTEGER
);

CREATE TABLE cases (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  transaction_id TEXT NOT NULL REFERENCES transactions(id),
  code TEXT NOT NULL REFERENCES failure_codes(code),
  bucket TEXT NOT NULL,                -- passport_identity | residency_address | other
  reason_ar TEXT NOT NULL,
  priority TEXT NOT NULL,
  needs_employee INTEGER NOT NULL,
  retry_available INTEGER NOT NULL,
  recommendation_ar TEXT,
  wait_time TEXT,
  status TEXT NOT NULL DEFAULT 'open', -- open | closed | transferred
  root_cause_ar TEXT,                  -- يُملأ وقت التشخيص الفعلي
  corrective_action_ar TEXT,           -- يُملأ وقت تنفيذ الحل
  verification_result_ar TEXT,         -- يُملأ وقت التحقق
  retry_count INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE retry_history (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  transaction_id TEXT NOT NULL REFERENCES transactions(id),
  attempted_at TEXT NOT NULL,
  result TEXT NOT NULL,
  note_ar TEXT
);

CREATE TABLE transaction_history (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  transaction_id TEXT NOT NULL REFERENCES transactions(id),
  event TEXT NOT NULL,
  actor TEXT NOT NULL,             -- system | employee | beneficiary
  description_ar TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE forecast_data (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  date TEXT NOT NULL,
  branch TEXT NOT NULL,
  service_type TEXT NOT NULL,
  volume INTEGER NOT NULL
);
""")

# ── 2. قاموس أكواد منجز + قواعد الحل — 8 أكواد (المصدر الوحيد للحقيقة) ────
FAILURE_CODES = [
    dict(code='MUN-101', name_ar='تعذر التحقق', meaning_ar='تعذر التحقق من صحة المعاملة',
         root_cause_ar='بيانات التحقق غير محدّثة أو غير مكتملة',
         resolution_type='DATA_REVALIDATION', automatic_resolution_allowed=1,
         employee_intervention_required=0, verification_required=1, max_attempts=2,
         recommended_action_ar='إعادة التحقق من البيانات ومزامنتها مع المصدر المعتمد'),
    dict(code='MUN-102', name_ar='بيانات غير متطابقة', meaning_ar='البيانات تختلف بين الأنظمة المرتبطة',
         root_cause_ar='اختلاف في قيمة نفس الحقل بين نظامين مرتبطين',
         resolution_type='DATA_SYNCHRONIZATION', automatic_resolution_allowed=1,
         employee_intervention_required=0, verification_required=1, max_attempts=1,
         recommended_action_ar='مزامنة البيانات مع المصدر المعتمد وإعادة التحقق'),
    dict(code='MUN-201', name_ar='شرط غير مستوفى', meaning_ar='شرط مطلوب لإكمال الخدمة غير مكتمل',
         root_cause_ar='أحد المتطلبات الأساسية للخدمة لم يُستوفَ بعد',
         resolution_type='REQUIREMENT_COMPLETION', automatic_resolution_allowed=1,
         employee_intervention_required=0, verification_required=1, max_attempts=None,
         recommended_action_ar='استكمال الشرط الناقص من قبل المستفيد'),
    dict(code='MUN-301', name_ar='تعثر التكامل', meaning_ar='خدمة مرتبطة لم تستجب أو تعثر التكامل معها',
         root_cause_ar='تعثر مؤقت في التكامل مع نظام حكومي مرتبط',
         resolution_type='TEMPORARY_SERVICE_RECOVERY', automatic_resolution_allowed=1,
         employee_intervention_required=0, verification_required=1, max_attempts=3,
         recommended_action_ar='إعادة تنفيذ العملية المتأثرة عبر مسار الاسترجاع المعتمد'),
    dict(code='MUN-302', name_ar='انتهاء مهلة الاتصال', meaning_ar='انتهت مهلة الاتصال أثناء المعالجة وحالة الطلب غير مؤكدة',
         root_cause_ar='حالة الطلب لدى النظام المرتبط غير معروفة بسبب انقطاع الاتصال',
         resolution_type='SAFE_RETRY', automatic_resolution_allowed=1,
         employee_intervention_required=0, verification_required=1, max_attempts=2,
         recommended_action_ar='التحقق من الحالة الفعلية للطلب قبل أي إعادة إرسال'),
    dict(code='MUN-401', name_ar='طلب مكرر', meaning_ar='توجد معاملة سابقة لنفس العملية',
         root_cause_ar='المستفيد قدّم أكثر من طلب لنفس الخدمة',
         resolution_type='DUPLICATE_RESOLUTION', automatic_resolution_allowed=1,
         employee_intervention_required=0, verification_required=1, max_attempts=1,
         recommended_action_ar='ربط الحالة بالمعاملة الصحيحة الموجودة ومنع التكرار'),
    dict(code='MUN-501', name_ar='عطل مؤقت', meaning_ar='عطل مؤقت في خدمة مرتبطة',
         root_cause_ar='الخدمة المرتبطة غير متاحة حالياً بشكل مؤقت',
         resolution_type='TEMPORARY_SERVICE_RECOVERY', automatic_resolution_allowed=1,
         employee_intervention_required=0, verification_required=1, max_attempts=3,
         recommended_action_ar='الانتظار ضمن مسار مراقبة الاسترجاع وإعادة المحاولة عند التعافي'),
    dict(code='MUN-600', name_ar='يحتاج قرار موظف', meaning_ar='لا يمكن حل الحالة بقاعدة آلية معتمدة',
         root_cause_ar='الحالة حساسة أو تتطلب صلاحية بشرية رسمية',
         resolution_type='EMPLOYEE_REVIEW', automatic_resolution_allowed=0,
         employee_intervention_required=1, verification_required=0, max_attempts=0,
         recommended_action_ar='مراجعة الموظف واتخاذ القرار النهائي'),
]
CODES = {fc['code']: fc for fc in FAILURE_CODES}

for fc in FAILURE_CODES:
    cur.execute("""INSERT INTO failure_codes
                   (code, name_ar, meaning_ar, root_cause_ar, resolution_type,
                    automatic_resolution_allowed, employee_intervention_required,
                    verification_required, max_attempts, recommended_action_ar)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (fc['code'], fc['name_ar'], fc['meaning_ar'], fc['root_cause_ar'], fc['resolution_type'],
                 fc['automatic_resolution_allowed'], fc['employee_intervention_required'],
                 fc['verification_required'], fc['max_attempts'], fc['recommended_action_ar']))

# ── 3. مصادر أسماء وهمية (fictional only) ───────────────────────────────
FIRST_NAMES = ['أحمد', 'محمد', 'سعيد', 'فيصل', 'خالد', 'عبدالله', 'ماريا', 'سانتياغو',
               'فاطمة', 'علي', 'رامي', 'وليد', 'كارلوس', 'نورة', 'هند', 'يوسف', 'ريان', 'دانيال']
LAST_NAMES = ['المطيري', 'الغامدي', 'البلوشي', 'القحطاني', 'الشريف', 'دياز', 'روميرو',
              'مصطفى', 'جابر', 'حمد', 'العتيبي', 'مندوزا']
EMPLOYERS = ['شركة الخليج للتوريدات', 'مؤسسة النخبة للمقاولات', 'شركة الواحة التجارية',
             'مصنع الرياض للصناعات', 'شركة الأفق للخدمات']
BRANCH = 'الرياض شمال'

_txn_counter = 480000
_user_counter = 10000


def next_txn_id():
    global _txn_counter
    _txn_counter += 7
    return f"IQ-2026-{_txn_counter}"


def next_user_id():
    global _user_counter
    _user_counter += 1
    return f"DEMO-{_user_counter}"


def rand_name():
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"


def make_user_and_txn(status, service_type=None, user_id=None):
    uid = user_id or next_user_id()
    employer = random.choice(EMPLOYERS) if random.random() > 0.3 else None
    if service_type is None:
        service_type = 'renew_residency_business' if employer else 'renew_residency_individual'
    if user_id is None:
        cur.execute("INSERT INTO users (id, name, employer_name, service_type) VALUES (?, ?, ?, ?)",
                    (uid, rand_name(), employer, service_type))
    tid = next_txn_id()
    days_ago = random.randint(0, 10)
    created = (date.today() - timedelta(days=days_ago)).isoformat()
    cur.execute("""INSERT INTO transactions (id, user_id, service_type, status, branch, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (tid, uid, service_type, status, BRANCH, created))
    return uid, tid


def insert_req(tid, rtype, status, detail, days_remaining=None):
    cur.execute("""INSERT INTO requirement_checks
                   (transaction_id, requirement_type, status, detail_ar, days_remaining)
                   VALUES (?, ?, ?, ?, ?)""", (tid, rtype, status, detail, days_remaining))


def insert_case(tid, code, bucket, reason_ar, priority, needs_employee, retry_available, rec, wait):
    cur.execute("""INSERT INTO cases
                   (transaction_id, code, bucket, reason_ar, priority,
                    needs_employee, retry_available, recommendation_ar, wait_time, status)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'open')""",
                (tid, code, bucket, reason_ar, priority, int(needs_employee), int(retry_available), rec, wait))


def log_history(tid, event, actor, desc):
    cur.execute("""INSERT INTO transaction_history (transaction_id, event, actor, description_ar, created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (tid, event, actor, desc, date.today().isoformat()))


# ── 4. معاملات ناجحة — 460 معاملة ────────────────────────────────────────
for _ in range(460):
    _, tid = make_user_and_txn('completed')
    insert_req(tid, 'passport', 'valid', 'ساري - أكثر من 6 أشهر', 200)
    insert_req(tid, 'insurance', 'valid', 'مكتمل')
    insert_req(tid, 'violations', 'valid', 'لا توجد مخالفات')
    insert_req(tid, 'work_permit', 'valid', 'ساري')
    log_history(tid, 'resolved', 'system', 'اكتملت المعاملة مباشرة دون استثناء')

# ── 5. MUN-201 شرط غير مستوفى — جواز (45) + تأمين (35) + رسوم (20) ───────
for _ in range(45):
    _, tid = make_user_and_txn('blocked')
    days = random.randint(5, 30)
    insert_req(tid, 'passport', 'expired', f'ينتهي خلال {days} يوماً', days)
    insert_req(tid, 'insurance', 'valid', 'مكتمل')
    insert_req(tid, 'violations', 'valid', 'لا توجد مخالفات')
    insert_req(tid, 'work_permit', 'valid', 'ساري')
    insert_case(tid, 'MUN-201', 'passport_identity', f'جواز السفر ينتهي خلال {days} يوماً',
                'high' if days < 15 else 'med', False, True, CODES['MUN-201']['recommended_action_ar'], f'{days} يوم')
    log_history(tid, 'exception_detected', 'system', 'اكتُشف شرط غير مستوفى: صلاحية الجواز')

for _ in range(35):
    _, tid = make_user_and_txn('blocked')
    insert_req(tid, 'passport', 'valid', 'ساري - أكثر من سنة', 400)
    insert_req(tid, 'insurance', 'expired', 'التأمين الصحي منتهي الصلاحية')
    insert_req(tid, 'violations', 'valid', 'لا توجد مخالفات')
    insert_req(tid, 'work_permit', 'valid', 'ساري')
    insert_case(tid, 'MUN-201', 'residency_address', 'التأمين الصحي منتهي الصلاحية',
                'med', False, True, CODES['MUN-201']['recommended_action_ar'], '2 يوم')
    log_history(tid, 'exception_detected', 'system', 'اكتُشف شرط غير مستوفى: التأمين الصحي')

for _ in range(20):
    _, tid = make_user_and_txn('blocked')
    insert_req(tid, 'passport', 'valid', 'ساري', 300)
    insert_req(tid, 'insurance', 'valid', 'مكتمل')
    insert_req(tid, 'violations', 'outstanding', 'رسوم غير مسددة')
    insert_req(tid, 'work_permit', 'valid', 'ساري')
    insert_case(tid, 'MUN-201', 'other', 'رسوم غير مسددة',
                'low', False, True, CODES['MUN-201']['recommended_action_ar'], '1 يوم')
    log_history(tid, 'exception_detected', 'system', 'اكتُشف شرط غير مستوفى: الرسوم')

# ── 6. MUN-102 بيانات غير متطابقة — تعارض معلومات (20) + هوية (10) ───────
for _ in range(20):
    _, tid = make_user_and_txn('blocked')
    insert_req(tid, 'passport', 'valid', 'ساري', 300)
    insert_req(tid, 'insurance', 'valid', 'مكتمل')
    insert_req(tid, 'violations', 'outstanding', 'بيانات متعارضة بين الأنظمة')
    insert_req(tid, 'work_permit', 'valid', 'ساري')
    insert_case(tid, 'MUN-102', 'residency_address', 'تعارض في معلومات الطلب بين الأنظمة المرتبطة',
                'high', False, True, CODES['MUN-102']['recommended_action_ar'], '10 دقائق')
    log_history(tid, 'exception_detected', 'system', 'اكتُشف تعارض بيانات بين نظامين مرتبطين')

for i in range(10):
    _, tid = make_user_and_txn('blocked', service_type='renew_identity')
    insert_req(tid, 'identity', 'outstanding', 'تعارض في بيانات الهوية')
    insert_case(tid, 'MUN-102', 'passport_identity', 'تعارض في بيانات الهوية المقدَّمة بين الأنظمة',
                'high', False, True, CODES['MUN-102']['recommended_action_ar'], '10 دقائق')
    log_history(tid, 'exception_detected', 'system', 'اكتُشف تعارض ببيانات الهوية')

# ── 7. MUN-301 تعثر التكامل — 20 حالة ─────────────────────────────────────
for _ in range(20):
    _, tid = make_user_and_txn('blocked')
    insert_req(tid, 'passport', 'valid', 'ساري', 300)
    insert_req(tid, 'insurance', 'valid', 'مكتمل')
    insert_req(tid, 'violations', 'valid', 'لا توجد مخالفات')
    insert_req(tid, 'work_permit', 'pending', 'بانتظار رد جهة حكومية مرتبطة (قوى)')
    insert_case(tid, 'MUN-301', 'other', 'تعثر التكامل مع خدمة قوى',
                'med', False, True, CODES['MUN-301']['recommended_action_ar'], '15 دقيقة')
    log_history(tid, 'exception_detected', 'system', 'تعثر التكامل مع نظام قوى')

# ── 8. MUN-501 عطل مؤقت — 15 حالة ─────────────────────────────────────────
for _ in range(15):
    _, tid = make_user_and_txn('blocked')
    insert_req(tid, 'passport', 'valid', 'ساري', 300)
    insert_req(tid, 'insurance', 'pending', 'بانتظار استعادة خدمة التحقق من التأمين')
    insert_req(tid, 'violations', 'valid', 'لا توجد مخالفات')
    insert_req(tid, 'work_permit', 'valid', 'ساري')
    insert_case(tid, 'MUN-501', 'other', 'عطل مؤقت في خدمة التحقق من التأمين',
                'med', False, True, CODES['MUN-501']['recommended_action_ar'], '20 دقيقة')
    log_history(tid, 'exception_detected', 'system', 'عطل مؤقت في خدمة مرتبطة')

# ── 9. MUN-302 انتهاء مهلة الاتصال — 15 حالة (الشروط فعلياً سليمة) ────────
for _ in range(15):
    _, tid = make_user_and_txn('blocked')
    insert_req(tid, 'passport', 'valid', 'ساري', 300)
    insert_req(tid, 'insurance', 'valid', 'مكتمل')
    insert_req(tid, 'violations', 'valid', 'لا توجد مخالفات')
    insert_req(tid, 'work_permit', 'valid', 'ساري')
    insert_case(tid, 'MUN-302', 'other', 'انتهت مهلة الاتصال أثناء المعالجة — حالة الطلب غير مؤكدة',
                'med', False, True, CODES['MUN-302']['recommended_action_ar'], '5 دقائق')
    log_history(tid, 'exception_detected', 'system', 'انتهاء مهلة الاتصال أثناء المعالجة')

# ── 10. MUN-401 طلب مكرر — 15 حالة (نفس المستفيد له معاملتان لنفس الخدمة) ─
for _ in range(15):
    uid, original_tid = make_user_and_txn('completed')
    insert_req(original_tid, 'passport', 'valid', 'ساري', 300)
    insert_req(original_tid, 'insurance', 'valid', 'مكتمل')
    insert_req(original_tid, 'violations', 'valid', 'لا توجد مخالفات')
    insert_req(original_tid, 'work_permit', 'valid', 'ساري')

    _, dup_tid = make_user_and_txn('blocked', user_id=uid)
    insert_req(dup_tid, 'passport', 'valid', 'ساري', 300)
    insert_req(dup_tid, 'insurance', 'valid', 'مكتمل')
    insert_req(dup_tid, 'violations', 'valid', 'لا توجد مخالفات')
    insert_req(dup_tid, 'work_permit', 'valid', 'ساري')
    insert_case(dup_tid, 'MUN-401', 'other', f'توجد معاملة سابقة مكتملة لنفس الخدمة (رقم {original_tid})',
                'low', False, True, CODES['MUN-401']['recommended_action_ar'], '5 دقائق')
    log_history(dup_tid, 'exception_detected', 'system', f'اكتُشف طلب مكرر — المعاملة الأصلية {original_tid}')

# ── 11. MUN-600 قرار موظف — 35 حالة متنوعة الأولوية والتصنيف ─────────────
BUCKET_CHOICES = ['passport_identity', 'residency_address', 'other']
for _ in range(35):
    _, tid = make_user_and_txn('pending_employee')
    bucket = random.choice(BUCKET_CHOICES)
    priority = random.choice(['high', 'med', 'low'])
    insert_req(tid, 'other', 'pending', 'الحالة لا تندرج تحت قاعدة آلية معتمدة')
    wait = f"{random.randint(1, 11)} أيام"
    insert_case(tid, 'MUN-600', bucket, 'الحالة تحتاج قرار موظف — حساسة أو تتطلب صلاحية رسمية',
                priority, True, False, CODES['MUN-600']['recommended_action_ar'], wait)
    log_history(tid, 'exception_detected', 'system', 'الحالة تحتاج قرار موظف مباشرة')

# ── 12. تجديد جواز مستقل (نوع خدمة) — 20 معاملة ───────────────────────────
for i in range(20):
    if i < 15:
        _, tid = make_user_and_txn('completed', service_type='renew_passport')
        insert_req(tid, 'passport', 'valid', 'تم إصدار الجواز الجديد بنجاح')
    else:
        _, tid = make_user_and_txn('blocked', service_type='renew_passport')
        insert_req(tid, 'fees', 'outstanding', 'رسوم إصدار غير مسددة')
        insert_case(tid, 'MUN-201', 'passport_identity', 'رسوم إصدار الجواز غير مسددة', 'low',
                    False, True, CODES['MUN-201']['recommended_action_ar'], '1 يوم')
        log_history(tid, 'exception_detected', 'system', 'رسوم إصدار الجواز غير مسددة')

# ── 13. تجديد الهوية (نوع خدمة) — 20 معاملة مكتملة (تكملة للتنوع) ─────────
for _ in range(20):
    _, tid = make_user_and_txn('completed', service_type='renew_identity')
    insert_req(tid, 'identity', 'valid', 'تم التحقق من الهوية بنجاح')

# ── 13ب. مستفيد تجريبي ثابت (DEMO-90001) — لصفحة "معاملاتي" ───────────────
# نفس المعرّف يطلع كل مرة نشغّل السيد، عشان الواجهة تقدر تعتمد عليه كسيناريو ثابت
DEMO_USER_ID = 'DEMO-90001'
cur.execute("INSERT INTO users (id, name, employer_name, service_type) VALUES (?, ?, ?, ?)",
            (DEMO_USER_ID, 'خالد الأحمدي', None, 'renew_residency_individual'))

# معاملة 1: مكتملة أصلاً بدون أي استثناء
_, demo_t1 = make_user_and_txn('completed', service_type='renew_residency_individual', user_id=DEMO_USER_ID)
insert_req(demo_t1, 'passport', 'valid', 'ساري - أكثر من سنة', 400)
insert_req(demo_t1, 'insurance', 'valid', 'مكتمل')
insert_req(demo_t1, 'violations', 'valid', 'لا توجد مخالفات')
insert_req(demo_t1, 'work_permit', 'valid', 'ساري')
log_history(demo_t1, 'resolved', 'system', 'اكتملت المعاملة مباشرة دون استثناء')

# معاملة 2: MUN-201 — متعثرة حالياً (جواز)، جاهزة لتجربة "عرض التشخيص" وإعادة المحاولة
_, demo_t2 = make_user_and_txn('blocked', service_type='renew_residency_individual', user_id=DEMO_USER_ID)
insert_req(demo_t2, 'passport', 'expired', 'ينتهي خلال 18 يوماً', 18)
insert_req(demo_t2, 'insurance', 'valid', 'مكتمل')
insert_req(demo_t2, 'violations', 'valid', 'لا توجد مخالفات')
insert_req(demo_t2, 'work_permit', 'valid', 'ساري')
insert_case(demo_t2, 'MUN-201', 'passport_identity', 'جواز السفر ينتهي خلال 18 يوماً',
            'med', False, True, CODES['MUN-201']['recommended_action_ar'], '18 يوم')
log_history(demo_t2, 'exception_detected', 'system', 'اكتُشف شرط غير مستوفى: صلاحية الجواز')

# معاملة 3: MUN-301 — متعثرة (تعثر تكامل)، لعرض إجراء استرجاع مختلف بالتشخيص
_, demo_t3 = make_user_and_txn('blocked', service_type='renew_residency_business', user_id=DEMO_USER_ID)
insert_req(demo_t3, 'passport', 'valid', 'ساري', 300)
insert_req(demo_t3, 'insurance', 'valid', 'مكتمل')
insert_req(demo_t3, 'violations', 'valid', 'لا توجد مخالفات')
insert_req(demo_t3, 'work_permit', 'pending', 'بانتظار رد جهة حكومية مرتبطة (قوى)')
insert_case(demo_t3, 'MUN-301', 'other', 'تعثر التكامل مع خدمة قوى',
            'med', False, True, CODES['MUN-301']['recommended_action_ar'], '15 دقيقة')
log_history(demo_t3, 'exception_detected', 'system', 'تعثر التكامل مع نظام قوى')

# معاملة 4: MUN-600 — تحتاج قرار موظف
_, demo_t4 = make_user_and_txn('pending_employee', service_type='renew_residency_individual', user_id=DEMO_USER_ID)
insert_req(demo_t4, 'other', 'pending', 'الحالة لا تندرج تحت قاعدة آلية معتمدة')
insert_case(demo_t4, 'MUN-600', 'other', 'الحالة تحتاج قرار موظف — حساسة أو تتطلب صلاحية رسمية',
            'high', True, False, CODES['MUN-600']['recommended_action_ar'], '3 أيام')
log_history(demo_t4, 'exception_detected', 'system', 'الحالة تحتاج قرار موظف مباشرة')

# ── 14. بيانات تاريخية للتوقع — 90 يوماً ─────────────────────────────────
WEEKDAY_BASE = [22000, 20500, 19000, 21500, 18500, 14000, 12000]  # Sun..Sat
TODAY = date(2026, 9, 14)

for d in range(90, 0, -1):
    day = TODAY - timedelta(days=d)
    sun_index = (day.weekday() + 1) % 7
    weeks_ago = d // 7
    trend_boost = max(0, (13 - weeks_ago)) * 200
    noise = random.randint(-600, 600)
    volume = WEEKDAY_BASE[sun_index] + trend_boost + noise
    if d <= 3:
        volume += 1500
    cur.execute("""INSERT INTO forecast_data (date, branch, service_type, volume)
                   VALUES (?, ?, ?, ?)""",
                (day.isoformat(), BRANCH, 'renew_residency', max(volume, 4000)))

conn.commit()

# ── 15. طباعة ملخص للتأكد ────────────────────────────────────────────────
def count(table):
    return cur.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


print("✅ تم بناء قاعدة البيانات وتعبئتها بنجاح:")
for t in ['failure_codes', 'users', 'transactions', 'requirement_checks', 'cases', 'transaction_history', 'forecast_data']:
    print(f"  {t}: {count(t)}")
print("توزيع الأكواد:")
for row in cur.execute("SELECT code, COUNT(*) c FROM cases GROUP BY code ORDER BY code"):
    print(" ", row['code'], '→', row['c'])
print(f"👤 المستفيد التجريبي {DEMO_USER_ID}:")
for row in cur.execute("SELECT id, status FROM transactions WHERE user_id = ? ORDER BY id", (DEMO_USER_ID,)):
    print(" ", row['id'], '→', row['status'])
print(f"📁 مكان الملف: {DB_PATH}")

conn.close()
