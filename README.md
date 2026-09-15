# منجز — Munajiz 🚀

## الفكرة الأساسية

**منجز** نظام ذكي لحل مشاكل التعثر في معاملات الجوازات والإقامة تلقائياً وعرض بيانات توقعية لضمان استمرارية التشغيل.

### المشكلة 🔴
- **معاملات معطلة** بسبب أكواد استثناء متكررة
- **لا توجد رؤية واضحة** لأسباب التعثر
- **لا يمكن التنبؤ** بالأحمال المستقبلية
- **معالجة يدوية** مرهقة وبطيئة

### الحل ✅
- 🤖 **حل آلي** للأكواد التي تسمح بالحل التلقائي
- 📊 **لوحة تحكم واضحة** توضح جميع الأرقام بلمحة سريعة
- 📈 **توقع الحمل** والمحاكاة لرؤية المستقبل
- 🎯 **دليل ترميز شامل** يوضح كل كود واستثناء
- 📋 **Playbook** يرشد الموظفين خطوة بخطوة

---

## الميزات الرئيسية

### 1️⃣ لوحة التحكم (Dashboard)
```
📊 إحصائيات فورية:
   ├─ إجمالي الحالات المعطلة
   ├─ تم حلها تلقائياً ✅
   ├─ تحتاج موظف 👤
   └─ قيد المعالجة ⏳
```

### 2️⃣ دليل الترميز (Exception Guide)
**جدول واضح لكل كود:**
| الكود | الاسم | المعنى | طريقة الحل |
|-----|------|--------|----------|
| 001 | Missing Document | الوثيقة ناقصة | حل آلي / يحتاج موظف |
| ... | ... | ... | ... |

### 3️⃣ معاملاتي (My Transactions)
- تتبع المعاملات الشخصية
- حالة كل معاملة في الوقت الفعلي
- التاريخ الكامل للتحديثات

### 4️⃣ التوقع والمحاكاة (Forecast & Simulation)
- 📈 توقع الحمل المستقبلي
- 🔄 محاكاة السيناريوهات المختلفة
- 💡 توصيات مبنية على البيانات

### 5️⃣ دليل التشغيل (Playbook)
- خطوات واضحة للموظفين
- توجيهات حسب نوع الاستثناء
- أفضل الممارسات

---

## الهيكل الفني

```
Munajiz/
│
├── frontend/                 ← الواجهة الأمامية
│   └── index.html           ← صفحة واحدة متكاملة (HTML+CSS+JS)
│                             (700+ سطر، محسّنة للأداء)
│
├── backend/                  ← الـ API والبيانات
│   ├── src/
│   │   ├── app.py           ← نقطة البداية (Flask)
│   │   ├── routes/          ← جميع الـ API endpoints
│   │   │   ├── dashboard_routes.py
│   │   │   ├── cases_routes.py
│   │   │   ├── codes_routes.py
│   │   │   ├── forecast_routes.py
│   │   │   ├── transactions_routes.py
│   │   │   └── beneficiary_routes.py
│   │   ├── services/        ← منطق العمل
│   │   │   ├── dashboard_service.py
│   │   │   ├── cases_service.py
│   │   │   ├── codes_service.py
│   │   │   ├── forecast_service.py
│   │   │   ├── resolution_service.py
│   │   │   └── ...
│   │   ├── config/
│   │   │   └── db.py        ← إعدادات قاعدة البيانات
│   │   └── seed/
│   │       └── seed.py      ← بيانات أولية تلقائية
│   │
│   ├── data/
│   │   └── munjiz.db        ← SQLite (تُنشأ تلقائياً)
│   │
│   ├── Requirements.txt      ← المكتبات (Flask فقط)
│   └── render.yaml          ← تكوين Render
│
└── README.md                ← هذا الملف

```

---

## التشغيل المحلي (Development)

### المتطلبات
- **Python 3.8+**
- **تصفح ويب حديث** (Chrome, Firefox, Safari...)

### خطوات التشغيل

#### 1️⃣ الباك إند (السيرفر)
```bash
cd backend
pip install -r Requirements.txt
cd src
python app.py
```
✅ السيرفر سيعمل على: **http://127.0.0.1:5000**

#### 2️⃣ الفرونت (الواجهة)
افتحي الملف مباشرة في المتصفح:
```
file:///path/to/Munajiz/frontend/index.html
```

أو استخدمي **Live Server** في VS Code:
```
كليك يمين على index.html → Open with Live Server
```

#### 3️⃣ اختبار الاتصال
روحي على: `http://127.0.0.1:5000/api/health`

يجب تشوفي:
```json
{"status": "ok", "service": "munjiz-backend"}
```

---

## النشر (Deployment)

### الخيار 1️⃣: Render (الأسهل والأسرع)

#### الباك إند:
1. انسخي الملفات إلى **مستودع GitHub جديد**
2. في Render:
   - اضغطي **New → Web Service**
   - اختاري المستودع
   - **Build Command**: `pip install -r Requirements.txt`
   - **Start Command**: `cd src && python app.py`
   - اضغطي **Deploy**
3. انسخي الرابط الجديد (مثل: `https://munajiz-api.onrender.com`)

#### الفرونت:
1. في `frontend/index.html` غيري السطر **1191**:
```javascript
// من:
const API_BASE = 'http://127.0.0.1:5000';

// إلى:
const API_BASE = 'https://munajiz-api.onrender.com';
```

2. ارفعي الملف في Render → **Static Site** أو GitHub Pages

### الخيار 2️⃣: GitHub Pages (للفرونت فقط)

1. ارفعي المستودع على GitHub
2. روحي **Settings → Pages**
3. اختاري **Deploy from branch → main**
4. الرابط بيظهر تلقائياً

---

## API Endpoints

### Dashboard
```
GET /api/dashboard/stats
→ إحصائيات شاملة (الحالات، الأكواد الشائعة، إلخ)
```

### Cases (الحالات)
```
GET /api/cases                    → جميع الحالات
GET /api/cases/<id>               → حالة محددة
POST /api/cases                   → إنشاء حالة جديدة
PUT /api/cases/<id>/resolve       → حل حالة
```

### Exception Codes (أكواد الاستثناء)
```
GET /api/codes                    → جميع الأكواد
GET /api/codes/search             → البحث بالكود
```

### Forecast (التوقع)
```
GET /api/forecast                 → بيانات التوقع
GET /api/forecast/alert           → التنبيهات
GET /api/forecast/continuity      → بيانات الاستمرارية
```

### Transactions (المعاملات)
```
GET /api/transactions             → جميع المعاملات
GET /api/transactions/<id>        → معاملة محددة
```

### Beneficiary (المستفيد)
```
GET /api/beneficiary/<id>         → معلومات المستفيد
```

---

## التكنولوجيا المستخدمة

**الفرونت:**
- HTML5 (Semantic)
- CSS3 (Grid, Flexbox, Variables)
- JavaScript Vanilla (بدون مكتبات خارجية)

**الباك إند:**
- Python 3
- Flask (خفيف وسريع)
- SQLite (قاعدة بيانات محلية)

**البيانات:**
- Schema محسّن (Normalized)
- Seed data أولية للتطوير
- CORS مفعّل للتطوير السهل

---

## نقاط القوة

✅ **سهل التطوير** — فرونت وباك إند منفصلان  
✅ **بدون مكتبات خارجية ثقيلة** — أداء سريع  
✅ **قابل للتوسع** — معمارية نظيفة (Services + Routes)  
✅ **نشر سهل** — Render.yaml جاهز  
✅ **بيانات حقيقية** — من السيناريو الفعلي  
✅ **واجهة احترافية** — تجربة مستخدم سلسة  

---

## الملفات المهمة

| الملف | الوصف |
|------|--------|
| `frontend/index.html` | الواجهة الكاملة (الصفحة الوحيدة) |
| `backend/src/app.py` | السيرفر الرئيسي (Flask) |
| `backend/Requirements.txt` | المكتبات المطلوبة |
| `backend/render.yaml` | تكوين النشر على Render |
| `backend/data/munjiz.db` | قاعدة البيانات (SQLite) |

---

## المساهمون

👩‍💻 فريق منجز — Munajiz Team

---

## الملاحظات

- قاعدة البيانات تُنشأ **تلقائياً** عند تشغيل السيرفر أول مرة من `backend/src/seed/seed.py`
- الفرونت يتواصل مع الباك إند عبر **API REST**
- **CORS مفعّل** — لا توجد مشاكل أمان في التطوير المحلي
- الأرقام والبيانات **وهمية/اختبارية** للعرض التوضيحي

---

**جاهز للاستخدام! 🚀**
