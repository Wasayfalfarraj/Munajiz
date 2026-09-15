"""
محاكي تكامل حكومي مبسّط (Mock) — لأغراض عرض الهاكاثون فقط.
لا يتصل بأي نظام حكومي حقيقي (لا أبشر ولا مقيم ولا قوى). كل دالة هنا تُرجع
نتيجة محاكاة ثابتة تخدم توضيح تدفّق "التشخيص → الحل → التحقق".
"""

SUCCESS = 'SUCCESS'
FAILED = 'FAILED'
TIMEOUT = 'TIMEOUT'
TEMPORARY_FAILURE = 'TEMPORARY_FAILURE'
VALIDATION_FAILED = 'VALIDATION_FAILED'
DATA_MISMATCH = 'DATA_MISMATCH'
ALREADY_PROCESSED = 'ALREADY_PROCESSED'


def validate(field_name):
    """محاكاة إعادة التحقق من بيانات المعاملة."""
    return SUCCESS


def synchronize(field_name):
    """محاكاة مزامنة قيمة حقل مع المصدر المعتمد."""
    return SUCCESS


def check_integration_status(service_name):
    """محاكاة استعلام حالة خدمة حكومية مرتبطة (متاحة/غير متاحة)."""
    return SUCCESS


def retry_operation(service_name):
    """محاكاة إعادة تنفيذ عملية متأثرة بعد استعادة الخدمة."""
    return SUCCESS


def search_existing_transaction(cur, user_id, service_type, exclude_tid):
    """يبحث فعلياً بقاعدة البيانات عن معاملة سابقة مكتملة لنفس المستفيد ونفس الخدمة."""
    row = cur.execute(
        """SELECT id FROM transactions
           WHERE user_id = ? AND service_type = ? AND id != ? AND status = 'completed'
           LIMIT 1""",
        (user_id, service_type, exclude_tid),
    ).fetchone()
    return row['id'] if row else None
