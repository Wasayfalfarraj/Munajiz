# معمارية المشروع 🏗️

## المخطط العام

```
┌─────────────────────────────────────────────────────────────┐
│                     المستخدم (User)                         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────┐
│              الواجهة الأمامية (Frontend)                     │
│              frontend/index.html                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ • لوحة التحكم (Dashboard)                            │  │
│  │ • دليل الترميز (Exception Guide)                   │  │
│  │ • معاملاتي (My Transactions)                       │  │
│  │ • التوقع والمحاكاة (Forecast)                      │  │
│  │ • Playbook                                         │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │
              HTTP REST API (JSON)
                         │
                         ↓
┌─────────────────────────────────────────────────────────────┐
│           الخادم الخلفي (Backend - Flask)                   │
│              backend/src/app.py                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Routes (الـ endpoints)                               │  │
│  │  • dashboard_routes.py                              │  │
│  │  • cases_routes.py                                  │  │
│  │  • codes_routes.py                                  │  │
│  │  • forecast_routes.py                               │  │
│  │  • transactions_routes.py                           │  │
│  │  • beneficiary_routes.py                            │  │
│  └──────────────────────────────────────────────────────┘  │
│                         ↓                                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Services (منطق العمل)                               │  │
│  │  • dashboard_service.py                             │  │
│  │  • cases_service.py                                 │  │
│  │  • codes_service.py                                 │  │
│  │  • forecast_service.py                              │  │
│  │  • resolution_service.py                            │  │
│  │  • integration_service.py                           │  │
│  │  • beneficiary_service.py                           │  │
│  │  • transactions_service.py                          │  │
│  └──────────────────────────────────────────────────────┘  │
│                         ↓                                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Database Layer (قاعدة البيانات)                     │  │
│  │  • config/db.py (الاتصال والإعدادات)              │  │
│  │  • SQLite (data/munjiz.db)                          │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## طبقات المشروع (Layers)

### 1️⃣ Frontend Layer (الواجهة)
**الملف:** `frontend/index.html`

**المسؤوليات:**
- عرض البيانات للمستخدم
- التقاط مدخلات المستخدم
- استدعاء API الخادم
- معالجة الأخطاء والتنسيق

**التقنيات:**
- HTML5 (Semantic markup)
- CSS3 (Grid, Flexbox)
- JavaScript Vanilla (لا توجد مكتبات خارجية ثقيلة)

---

### 2️⃣ API Layer (طبقة الـ API)
**المجلد:** `backend/src/routes/`

**المسؤوليات:**
- تلقي الطلبات HTTP
- التحقق من صحة البيانات
- استدعاء Services
- إرجاع JSON

**الملفات:**
```
routes/
├── dashboard_routes.py     → GET /api/dashboard/stats
├── cases_routes.py         → GET/POST /api/cases
├── codes_routes.py         → GET /api/codes
├── forecast_routes.py      → GET /api/forecast/*
├── transactions_routes.py  → GET /api/transactions
└── beneficiary_routes.py   → GET /api/beneficiary/<id>
```

---

### 3️⃣ Business Logic Layer (منطق العمل)
**المجلد:** `backend/src/services/`

**المسؤوليات:**
- معالجة البيانات
- حسابات معقدة
- توقعات والتنبؤات
- قرارات التحويل التلقائي

**الملفات:**
```
services/
├── dashboard_service.py    → إحصائيات مجمعة
├── cases_service.py        → إدارة الحالات
├── codes_service.py        → إدارة الأكواد
├── forecast_service.py     → التوقعات والمحاكاة
├── resolution_service.py   → قرار الحل التلقائي
├── beneficiary_service.py  → معلومات المستفيد
├── transactions_service.py → معاملات المستفيد
└── integration_service.py  → التكاملات الخارجية
```

---

### 4️⃣ Data Access Layer (الوصول للبيانات)
**الملف:** `backend/src/config/db.py`

**المسؤوليات:**
- إدارة اتصال قاعدة البيانات
- تنفيذ الاستعلامات SQL
- التعامل مع الأخطاء

**الكود الأساسي:**
```python
# الاتصال بـ SQLite
connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()

# تنفيذ الاستعلام
cursor.execute("SELECT * FROM cases")
results = cursor.fetchall()
```

---

### 5️⃣ Database Layer (قاعدة البيانات)
**الملف:** `backend/data/munjiz.db`

**الجداول الأساسية:**
```sql
-- الحالات المعطلة
CREATE TABLE cases (
    id INTEGER PRIMARY KEY,
    case_number TEXT UNIQUE,
    exception_code TEXT,
    status TEXT,
    created_at TIMESTAMP,
    resolved_at TIMESTAMP,
    auto_resolved BOOLEAN
);

-- أكواد الاستثناء
CREATE TABLE exception_codes (
    code TEXT PRIMARY KEY,
    name_ar TEXT,
    name_en TEXT,
    meaning_ar TEXT,
    automatic_resolution_allowed BOOLEAN,
    priority TEXT
);

-- المعاملات
CREATE TABLE transactions (
    id TEXT PRIMARY KEY,
    beneficiary_id TEXT,
    type TEXT,
    status TEXT,
    created_at TIMESTAMP
);

-- المستفيدون
CREATE TABLE beneficiaries (
    id TEXT PRIMARY KEY,
    name_ar TEXT,
    nationality TEXT,
    passport_number TEXT
);

-- التنبؤات
CREATE TABLE forecasts (
    date TEXT,
    predicted_load INTEGER,
    confidence FLOAT
);
```

---

## تدفق البيانات (Data Flow)

### مثال: عرض لوحة التحكم

```
1. المستخدم يفتح الموقع
   └─ يحمّل frontend/index.html

2. الـ JavaScript يطلب البيانات
   └─ fetch('http://backend.com/api/dashboard/stats')

3. الطلب يصل للـ Backend
   └─ GET /api/dashboard/stats

4. Route يمسك الطلب
   └─ dashboard_routes.py → dashboard_service.py

5. Service يحسب الإحصائيات
   ├─ عدد الحالات من جدول cases
   ├─ كم تم حلها تلقائياً
   ├─ كم تحتاج موظف
   └─ أكثر الأكواد شيوعاً

6. Database يُرجع البيانات
   └─ من جداول cases و exception_codes

7. Service تحضير النتيجة
   └─ JSON formatted

8. Route يرد على الطلب
   └─ {"total_cases": 1250, ...}

9. الـ Frontend يستقبل البيانات
   └─ يعرضها في الصفحة
```

---

## معايير التصميم

### 🏗️ Separation of Concerns
كل طبقة لها مسؤولية واحدة فقط:
- Frontend: العرض
- Routes: استقبال الطلبات
- Services: معالجة البيانات
- Database: تخزين البيانات

### 📦 Modularity
كل ملف مسؤول عن جزء واحد:
- `dashboard_routes.py` + `dashboard_service.py` = Dashboard كامل
- `cases_routes.py` + `cases_service.py` = Cases كامل

### 🔄 Reusability
الـ Services تُستخدم من طلبات مختلفة:
```python
# dashboard_routes يستخدم dashboard_service
get_dashboard_stats()

# وأيضاً قد تستخدمها routes أخرى
# = نفس الكود، استخدام متعدد
```

### 🧪 Testability
كل جزء يمكن اختباره بشكل مستقل:
```python
# اختبار Service بدون Route
stats = dashboard_service.get_stats()
assert stats['total_cases'] > 0

# اختبار Route بدون قاعدة البيانات الحقيقية
# (mock objects)
```

---

## مثال: إضافة ميزة جديدة

لنقل نبي نضيف API endpoint جديد: "عرض الحالات المعطلة في آخر ساعة"

### الخطوات:

1. **Routing** (backend/src/routes/cases_routes.py)
```python
@cases_bp.route('/api/cases/recent/hourly', methods=['GET'])
def get_recent_cases():
    return jsonify(cases_service.get_cases_from_last_hour())
```

2. **Service** (backend/src/services/cases_service.py)
```python
def get_cases_from_last_hour():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM cases 
        WHERE created_at > datetime('now', '-1 hour')
    """)
    return cursor.fetchall()
```

3. **Frontend** (frontend/index.html)
```javascript
fetch(`${API_BASE}/api/cases/recent/hourly`)
    .then(res => res.json())
    .then(data => {
        // عرض البيانات
        document.getElementById('recent-cases').innerHTML = 
            data.map(c => `<div>${c.case_number}</div>`).join('');
    });
```

---

## الإحصائيات

| المقياس | الرقم |
|--------|------|
| سطور الفرونت | 1700+ |
| ملفات Backend | 15+ |
| Endpoints | 6 رئيسية |
| جداول البيانات | 6+ |
| المكتبات الخارجية | 1 فقط (Flask) |
| وقت التحميل | < 1 ثانية |

---

**معمارية نظيفة وقابلة للتطوير! 🚀**
