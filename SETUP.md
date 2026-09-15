# دليل التثبيت والتشغيل السريع ⚡

## التشغيل المحلي (60 ثانية)

### الخطوة 1️⃣: الباك إند

```bash
# انتقلي للمجلد
cd backend

# ثبتي المكتبات
pip install -r Requirements.txt

# شغّلي السيرفر
cd src
python app.py
```

**النتيجة:** السيرفر يشتغل على `http://127.0.0.1:5000/` ✅

### الخطوة 2️⃣: الفرونت

**الطريقة الأولى (الأسهل):**
1. افتحي Visual Studio Code
2. ركبي **Live Server** extension
3. كليك يمين على `frontend/index.html` 
4. اختاري **"Open with Live Server"** ✅

**الطريقة الثانية:**
```bash
cd frontend
python -m http.server 8000
```
ثم روحي: `http://127.0.0.1:8000` ✅

**الطريقة الثالثة:**
افتحي الملف مباشرة في المتصفح:
```
/path/to/Munajiz/frontend/index.html
```

### الخطوة 3️⃣: اختبر الاتصال

روحي على: **`http://127.0.0.1:5000/api/health`**

يجب تشوفي:
```json
{
  "status": "ok",
  "service": "munjiz-backend"
}
```

إذا ما ظهر، تأكدي إن السيرفر (الخطوة 1) يشتغل! 🔧

---

## النشر على Render 🚀

### الباك إند (Web Service)

1. **اعملي Push للملفات على GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

2. **روحي Render.com**
   - اضغطي **New → Web Service**
   - اختاري المستودع
   - اختاري الإعدادات:
     - **Build Command**: `pip install -r Requirements.txt`
     - **Start Command**: `cd src && python app.py`
   - اضغطي **Deploy** ✅

3. **انسخي الرابط الجديد**
   - مثلاً: `https://munajiz-api.onrender.com`

### الفرونت (إختياري - استخدمي GitHub Pages)

1. **غيري `API_BASE` في `frontend/index.html`** (السطر 1191):
```javascript
// من:
const API_BASE = 'http://127.0.0.1:5000';

// إلى:
const API_BASE = 'https://munajiz-api.onrender.com';
```

2. **روحي GitHub → Settings → Pages**
   - اختاري **Deploy from branch → main**
   - الرابط بيظهر تلقائياً ✅

---

## استكشاف الأخطاء

### ❌ "خطأ: لا يمكن الاتصال بالسيرفر"
✅ **الحل:** تأكدي إن الخطوة 1 (تشغيل الباك إند) مكتملة وشغّال

### ❌ "ModuleNotFoundError: Flask"
✅ **الحل:** شغّلي `pip install Flask==3.1.3`

### ❌ "Port 5000 already in use"
✅ **الحل:** غيّري الـ port في `backend/src/app.py` سطر 54:
```python
port = int(os.environ.get('PORT', 5001))  # غيّري من 5000 إلى 5001
```

### ❌ "Database error"
✅ **الحل:** قاعدة البيانات تُنشأ تلقائياً أول مرة. انتظري أو احذفي `backend/data/munjiz.db` وشغّلي السيرفر مرة أخرى

---

## الملفات المهمة للمحكمين

📂 **عرّف المحكمين على:**
- `README.md` — الفكرة الكاملة والميزات
- `frontend/index.html` — الواجهة (700+ سطر, محسّنة)
- `backend/src/app.py` — السيرفر الرئيسي والتكوين
- `backend/Requirements.txt` — المكتبات (Flask فقط!)

---

## نصائح سريعة ✨

- **قاعدة البيانات**: تُنشأ تلقائياً من `backend/src/seed/seed.py`
- **بدون API Key**: كل الـ endpoints مفتوحة (CORS مفعّل)
- **بدون مكتبات ثقيلة**: بس Flask! ⚡
- **الأرقام وهمية**: بيانات توضيحية للهاكاثون

---

**كل شيء جاهز! احنا روديين 🎯**
