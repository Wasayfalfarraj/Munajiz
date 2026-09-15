# توثيق API 📚

جميع الـ endpoints متاحة على: **`http://127.0.0.1:5000`** أو رابط Render

---

## Dashboard | لوحة التحكم

### GET `/api/dashboard/stats`
**الغرض:** الحصول على إحصائيات شاملة

**مثال:**
```bash
curl http://127.0.0.1:5000/api/dashboard/stats
```

**النتيجة:**
```json
{
  "total_cases": 1250,
  "auto_resolved": 850,
  "pending_officer": 350,
  "in_progress": 50,
  "top_exceptions": [
    {"code": "001", "name_ar": "وثيقة ناقصة", "count": 120},
    {"code": "002", "name_ar": "عدم التطابق", "count": 95}
  ]
}
```

---

## Cases | الحالات

### GET `/api/cases`
**الغرض:** جميع الحالات

**المعاملات:**
- `status` (optional): `open`, `resolved`, `pending`
- `limit` (optional): عدد النتائج
- `offset` (optional): البداية

**مثال:**
```bash
curl "http://127.0.0.1:5000/api/cases?status=open&limit=10"
```

---

### GET `/api/cases/<id>`
**الغرض:** حالة محددة

**مثال:**
```bash
curl http://127.0.0.1:5000/api/cases/123
```

**النتيجة:**
```json
{
  "id": 123,
  "case_number": "CS-2025-00123",
  "status": "open",
  "exception_code": "001",
  "created_at": "2025-01-15T10:30:00",
  "description": "وثيقة جواز سفر ناقصة",
  "assigned_to": "موظف الجوازات"
}
```

---

### POST `/api/cases`
**الغرض:** إنشاء حالة جديدة

**البيانات المطلوبة:**
```json
{
  "exception_code": "001",
  "beneficiary_id": "1234567890",
  "description": "تفاصيل المشكلة"
}
```

---

### PUT `/api/cases/<id>/resolve`
**الغرض:** حل حالة

**البيانات:**
```json
{
  "resolution_type": "auto",
  "notes": "تم حل المشكلة"
}
```

---

## Codes | أكواد الاستثناء

### GET `/api/codes`
**الغرض:** جميع أكواد الاستثناء

**النتيجة:**
```json
[
  {
    "code": "001",
    "name_ar": "وثيقة ناقصة",
    "name_en": "Missing Document",
    "meaning_ar": "الوثيقة المطلوبة ناقصة أو غير واضحة",
    "automatic_resolution_allowed": true,
    "priority": "high"
  },
  ...
]
```

---

### GET `/api/codes/search?q=<query>`
**الغرض:** البحث عن كود

**مثال:**
```bash
curl "http://127.0.0.1:5000/api/codes/search?q=document"
```

---

## Forecast | التوقع

### GET `/api/forecast`
**الغرض:** توقع الحمل المستقبلي

**النتيجة:**
```json
{
  "forecast_data": [
    {
      "date": "2025-01-20",
      "predicted_load": 8500,
      "recommended_staff": 45
    },
    ...
  ]
}
```

---

### GET `/api/forecast/alert`
**الغرض:** التنبيهات المهمة

**النتيجة:**
```json
{
  "alerts": [
    {
      "type": "high_load",
      "severity": "critical",
      "message": "حمل مرتفع متوقع يوم الأحد",
      "date": "2025-01-21"
    }
  ]
}
```

---

### GET `/api/forecast/continuity`
**الغرض:** بيانات استمرارية التشغيل

**النتيجة:**
```json
{
  "current_capacity": 95,
  "projected_capacity_48h": 87,
  "risk_level": "medium",
  "recommendations": [...]
}
```

---

## Transactions | المعاملات

### GET `/api/transactions`
**المعاملات:**
- `beneficiary_id` (optional)
- `status` (optional)
- `date_from` (optional)

**مثال:**
```bash
curl "http://127.0.0.1:5000/api/transactions?beneficiary_id=1234567890"
```

**النتيجة:**
```json
{
  "transactions": [
    {
      "id": "T001",
      "beneficiary_id": "1234567890",
      "type": "visa_renewal",
      "status": "in_progress",
      "created_at": "2025-01-15",
      "exception_code": null
    }
  ]
}
```

---

### GET `/api/transactions/<id>`
**الغرض:** معاملة محددة

---

## Beneficiary | المستفيد

### GET `/api/beneficiary/<id>`
**الغرض:** معلومات المستفيد

**النتيجة:**
```json
{
  "id": "1234567890",
  "name_ar": "أحمد محمد",
  "nationality": "SAU",
  "passport_number": "G12345678",
  "active_transactions": 2,
  "total_resolved": 15
}
```

---

## Health Check

### GET `/api/health`
**الغرض:** التحقق من حالة السيرفر

**النتيجة:**
```json
{
  "status": "ok",
  "service": "munjiz-backend"
}
```

---

## رموز الحالة HTTP

| الرمز | المعنى |
|------|--------|
| `200` | نجاح ✅ |
| `201` | تم الإنشاء ✅ |
| `400` | طلب غير صحيح ❌ |
| `404` | غير موجود ❌ |
| `500` | خطأ السيرفر ❌ |

---

## معلومات إضافية

**جميع الـ responses:**
- تُرجع JSON
- CORS مفعّل (يقبل من أي origin)
- بدون authentication في الوقت الحالي

**تطوير مستقبلي:**
- إضافة JWT Authentication
- Rate Limiting
- Pagination محسّنة
- Caching

---

**للمزيد من التفاصيل:** راجعي ملفات `backend/src/routes/`
