# ❓ الأسئلة الشائعة
# Frequently Asked Questions (FAQ)

**نظام تحليل أداء لاعبي التزلج**

---

## 📑 الفهرس

1. [أسئلة عامة](#أسئلة-عامة)
2. [التثبيت والإعداد](#التثبيت-والإعداد)
3. [الاستخدام](#الاستخدام)
4. [المشاكل الشائعة](#المشاكل-الشائعة)
5. [الأداء](#الأداء)
6. [الأمان](#الأمان)
7. [التطوير](#التطوير)

---

## 🌟 أسئلة عامة

### س1: ما هو نظام تحليل أداء لاعبي التزلج؟

**ج:** نظام شامل ومتكامل لإدارة وتحليل أداء لاعبي التزلج على الجليد. يوفر:
- إدارة الأعضاء والحضور
- تقارير احترافية PDF
- نظام مستويات وشارات
- إشعارات تلقائية
- مقارنة الأداء
- رسوم بيانية تفاعلية

### س2: هل النظام مجاني؟

**ج:** نعم! النظام مفتوح المصدر تحت رخصة MIT. يمكنك:
- ✅ استخدامه مجاناً
- ✅ تعديله
- ✅ توزيعه
- ✅ استخدامه تجارياً

### س3: ما اللغات المدعومة؟

**ج:** النظام يدعم:
- 🇪🇬 العربية (كامل)
- 🇬🇧 الإنجليزية (كامل)
- يمكن إضافة لغات أخرى بسهولة

### س4: هل يعمل النظام بدون إنترنت؟

**ج:** نعم! بعد التثبيت، يعمل النظام محلياً (offline) بالكامل. الإنترنت مطلوب فقط لـ:
- تحميل المكتبات أول مرة
- إرسال الإشعارات (Email/SMS)
- التحديثات

### س5: كم عدد الأعضاء الذي يدعمه النظام؟

**ج:** النظام يدعم:
- ✅ حتى 1000 عضو بأداء ممتاز
- ✅ حتى 5000 عضو بأداء جيد
- ✅ أكثر من 10000 بأداء مقبول (يحتاج تحسينات)

---

## 🔧 التثبيت والإعداد

### س6: ما هي متطلبات النظام؟

**ج:**

**الحد الأدنى:**
```
المعالج: Intel Core i3
الذاكرة: 4 GB RAM
المساحة: 2 GB
Python: 3.10+
```

**الموصى به:**
```
المعالج: Intel Core i5+
الذاكرة: 8 GB RAM
المساحة: 5 GB
SSD: موصى به
```

### س7: كيف أثبت النظام؟

**ج:**

```bash
# 1. استنسخ المشروع
git clone https://github.com/elmansoory/yasooo.git
cd yasooo

# 2. الفرع المناسب
git checkout claude/skating-analysis-system-019JhsA9HHwcSgQ6oXnujCjf

# 3. ثبت المكتبات
pip install -r requirements.txt

# 4. شغّل النظام
streamlit run modern_app.py
```

### س8: يظهر خطأ عند تثبيت المكتبات. ماذا أفعل؟

**ج:**

**الحل 1: تحديث pip**
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

**الحل 2: بيئة افتراضية**
```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
# أو
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

**الحل 3: تثبيت فردي**
```bash
pip install streamlit pandas numpy plotly
pip install opencv-python mediapipe tensorflow torch
```

### س9: المكتبات كبيرة جداً! هل هناك بديل؟

**ج:** نعم! للاستخدام الأساسي:

```bash
# مكتبات أساسية فقط (أخف بكثير)
pip install -r requirements-minimal.txt
```

هذا يثبت:
- Streamlit
- Pandas
- Plotly
- NumPy

ويستثني المكتبات الثقيلة (TensorFlow, PyTorch, MediaPipe)

### س10: كيف أتحقق من التثبيت؟

**ج:**

```bash
# تشغيل الاختبار الشامل
python test_system.py
```

**النتيجة المتوقعة:**
```
✅ PASSED: 73
❌ FAILED: 0
📈 SCORE: 100%
```

---

## 💡 الاستخدام

### س11: كيف أضيف عضو جديد؟

**ج:**

**الطريقة 1: من الواجهة**
1. صفحة "الأعضاء"
2. "إضافة عضو جديد"
3. املأ البيانات
4. احفظ

**الطريقة 2: استيراد من Excel**
1. جهّز ملف Excel بالتنسيق:
```
| name      | gender | birth_date |
|-----------|--------|------------|
| محمد أحمد | ذكر    | 2010-05-15 |
```
2. استورد الملف

### س12: كيف أسجل الحضور؟

**ج:**

**طريقة سريعة:**
1. صفحة "الحضور"
2. اختر التاريخ
3. اختر الأعضاء (multi-select)
4. "تسجيل"

**استيراد جماعي:**
```
| member_id | date       |
|-----------|------------|
| 1         | 2025-01-15 |
| 2         | 2025-01-15 |
```

### س13: كيف أصدّر تقرير PDF؟

**ج:**

```python
from src.utils.pdf_generator import generate_member_pdf

# تقرير عضو
generate_member_pdf(
    member_data={'name': 'محمد', 'id': 1},
    attendance_data=attendance_df,
    output_path='reports/member_1.pdf'
)
```

أو من الواجهة:
1. ملف العضو
2. "تصدير PDF"
3. احفظ

### س14: كيف أقارن بين لاعبين؟

**ج:**

1. صفحة "المقارنة"
2. اختر اللاعبين (2-5)
3. "مقارنة"
4. شاهد النتائج والرسوم

### س15: كيف أفعّل الإشعارات؟

**ج:**

```python
# في ملف الإعدادات
NOTIFICATIONS_ENABLED = True
EMAIL_ENABLED = True
SMS_ENABLED = False  # يحتاج خدمة خارجية

# تكوين البريد
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USER = 'your_email@gmail.com'
EMAIL_PASSWORD = 'your_password'
```

---

## 🔧 المشاكل الشائعة

### س16: النظام بطيء. كيف أسرّعه؟

**ج:**

**1. فعّل Cache:**
```python
# في الكود
@st.cache_data
def get_members():
    return pd.read_sql(...)
```

**2. قلل البيانات المعروضة:**
```python
# بدلاً من عرض كل السجلات
df.head(100)  # أول 100 فقط
```

**3. استخدم النسخة المحسنة:**
```bash
streamlit run optimized_app.py
```

**4. قاعدة بيانات أسرع:**
- استخدم SSD بدل HDD
- نظف قاعدة البيانات: `VACUUM`

### س17: الرسوم البيانية لا تظهر!

**ج:**

**السبب الشائع:** مشكلة في Plotly

**الحل:**
```bash
# 1. تحديث Plotly
pip install --upgrade plotly

# 2. مسح Cache المتصفح
Ctrl + Shift + Delete

# 3. جرب متصفح آخر
```

### س18: خطأ "Module not found"!

**ج:**

**المشكلة:** مكتبة غير مثبتة

**الحل:**
```bash
# ثبت المكتبة المفقودة
pip install <module_name>

# أو أعد تثبيت الكل
pip install -r requirements.txt
```

### س19: خطأ في قاعدة البيانات!

**ج:**

**خطأ شائع:** قاعدة بيانات مقفلة

**الحل:**
```bash
# 1. أغلق جميع نوافذ التطبيق
# 2. احذف ملف القفل
rm *.db-journal

# 3. أو أنشئ قاعدة جديدة
python setup_database.py
```

### س20: "ModuleNotFoundError: mediapipe"

**ج:**

**السبب:** MediaPipe غير مثبت (مكتبة كبيرة)

**الحل 1: ثبت MediaPipe**
```bash
pip install mediapipe>=0.10.8
```

**الحل 2: استخدم النسخة الأساسية**
- MediaPipe مطلوب فقط لتحليل الفيديو المتقدم
- يمكنك استخدام النظام بدونه للميزات الأساسية

---

## ⚡ الأداء

### س21: كيف أحسن الأداء؟

**ج:**

**1. استخدم Cache:**
```python
from src.utils.cache_manager import cached

@cached(max_age=300)  # 5 دقائق
def expensive_operation():
    ...
```

**2. تحسين البيانات:**
```python
from src.utils.data_optimizer import DataOptimizer

df = DataOptimizer.optimize_dataframe(df)
# يوفر حتى 50% ذاكرة!
```

**3. قراءة كسولة:**
```python
# بدل قراءة كل البيانات
df = DataOptimizer.lazy_load_database(
    'database.db',
    'members',
    limit=100
)
```

**4. Streaming:**
```python
# للملفات الكبيرة
for chunk in pd.read_csv('large.csv', chunksize=1000):
    process(chunk)
```

### س22: كيف أتحقق من الأداء؟

**ج:**

```python
from src.utils.cache_manager import cache_stats, performance_report

# إحصائيات Cache
print(cache_stats())

# تقرير الأداء
print(performance_report())
```

---

## 🔒 الأمان

### س23: هل بياناتي آمنة؟

**ج:** نعم! النظام:
- ✅ يعمل محلياً (offline)
- ✅ لا يرسل بيانات لأي مكان
- ✅ قاعدة بيانات محلية
- ✅ يمكنك تشفير قاعدة البيانات

### س24: كيف أحمي قاعدة البيانات؟

**ج:**

**1. كلمة مرور:**
```python
# في الإعدادات
DB_PASSWORD = "strong_password_here"
```

**2. تشفير:**
```bash
# استخدم SQLCipher
pip install sqlcipher3
```

**3. نسخ احتياطي:**
```bash
# نسخ يومي تلقائي
cp skating_database.db backups/db_$(date +%Y%m%d).db
```

### س25: كيف أمنع الوصول غير المصرح؟

**ج:**

**1. كلمة مرور للتطبيق:**
```python
# في ملف .streamlit/config.toml
[server]
enableCORS = false
headless = true

[browser]
serverAddress = "localhost"
```

**2. Authentication:**
```python
import streamlit_authenticator as stauth

# نظام تسجيل دخول
authenticator = stauth.Authenticate(...)
name, authentication_status, username = authenticator.login()
```

---

## 👨‍💻 التطوير

### س26: كيف أضيف ميزة جديدة؟

**ج:**

```python
# 1. أنشئ ملف جديد
touch src/features/my_feature.py

# 2. اكتب الكود
class MyFeature:
    def __init__(self):
        pass

# 3. استورد في التطبيق
from src.features.my_feature import MyFeature

# 4. استخدم
feature = MyFeature()
```

### س27: كيف أساهم في المشروع؟

**ج:**

```bash
# 1. Fork المشروع
# 2. Clone
git clone https://github.com/YOUR_USERNAME/yasooo.git

# 3. فرع جديد
git checkout -b feature/my-feature

# 4. Commit
git commit -m "Add my feature"

# 5. Push
git push origin feature/my-feature

# 6. Pull Request على GitHub
```

### س28: كيف أختبر الكود؟

**ج:**

```bash
# تشغيل جميع الاختبارات
pytest

# اختبار ملف معين
pytest tests/test_progression.py

# مع تغطية الكود
pytest --cov=src tests/
```

### س29: أين الوثائق التقنية؟

**ج:**

```
docs/
├── API.md              # توثيق API
├── ARCHITECTURE.md     # المعمارية
├── CONTRIBUTING.md     # المساهمة
└── DEVELOPMENT.md      # دليل المطور
```

### س30: كيف أبلغ عن خطأ؟

**ج:**

1. افتح Issue على GitHub:
   https://github.com/elmansoory/yasooo/issues

2. اكتب:
   - وصف المشكلة
   - خطوات إعادة الإنتاج
   - لقطة شاشة (إن أمكن)
   - رسالة الخطأ الكاملة

---

## 🎓 نصائح وحيل

### نصيحة 1: اختصارات لوحة المفاتيح

```
Ctrl + R    : تحديث الصفحة
Ctrl + Shift + R : مسح Cache وتحديث
Ctrl + Click : فتح في تبويب جديد
F11         : وضع ملء الشاشة
```

### نصيحة 2: أوامر مفيدة

```bash
# مراقبة الأداء
streamlit run app.py --logger.level=debug

# تشغيل على منفذ مختلف
streamlit run app.py --server.port=8502

# السماح بالوصول الخارجي
streamlit run app.py --server.address=0.0.0.0
```

### نصيحة 3: تسريع التطوير

```python
# تفعيل Hot Reload
# في .streamlit/config.toml
[server]
runOnSave = true
```

### نصيحة 4: تنظيف قاعدة البيانات

```python
from src.utils.data_optimizer import DataOptimizer

# تنظيف وتحسين
DataOptimizer.vacuum_database('skating_database.db')
```

### نصيحة 5: نسخ احتياطي تلقائي

```bash
# في crontab (Linux/Mac)
0 2 * * * cp ~/yasooo/skating_database.db ~/backups/db_$(date +\%Y\%m\%d).db
```

---

## 📞 الدعم

### حصلت على سؤال لم يُجب عنه؟

- 📧 **Email:** support@skating-system.com
- 💬 **GitHub Issues:** https://github.com/elmansoory/yasooo/issues
- 📚 **الوثائق:** راجع USER_GUIDE.md
- 🎥 **الفيديوهات:** قريباً

---

## 🔄 التحديثات

### كيف أتابع التحديثات؟

```bash
# تحقق من التحديثات
git fetch origin
git status

# تحديث
git pull origin main
pip install -r requirements.txt --upgrade
```

### نسخة النظام الحالية

```python
# في التطبيق
import streamlit as st
st.sidebar.text("النسخة: 2.0.0")
```

---

**🎿 نظام تحليل أداء لاعبي التزلج**  
**النسخة 2.0.0 - الأسئلة الشائعة**  
**آخر تحديث: 2026-04-03**
