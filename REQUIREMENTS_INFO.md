# 📦 دليل المكتبات - Requirements Guide

## الملفات المتاحة

### 1️⃣ `requirements-minimal.txt` ⭐ (موصى به للبداية)

**الاستخدام**: للتشغيل السريع والتجربة الأولى

**المحتويات**:
- ✅ Streamlit (الواجهة)
- ✅ Pandas (معالجة البيانات)
- ✅ Plotly (الرسوم البيانية)
- ✅ SQLAlchemy (قاعدة البيانات)
- ✅ openpyxl (قراءة Excel)
- ✅ مكتبات أساسية أخرى

**الحجم**: ~100-200 MB

**وقت التثبيت**: 1-3 دقائق

**الأمر**:
```bash
pip install -r requirements-minimal.txt
```

**متى تستخدمه؟**
- ✅ عند التشغيل لأول مرة
- ✅ عند التجربة السريعة
- ✅ عند عدم الحاجة لميزات AI/ML
- ✅ على أجهزة ضعيفة

---

### 2️⃣ `requirements.txt` (للميزات المتقدمة)

**الاستخدام**: لتفعيل جميع الميزات بما فيها AI/ML

**المحتويات الإضافية**:
- 🤖 TensorFlow (Deep Learning)
- 🧠 PyTorch (Neural Networks)
- 👁️ MediaPipe (AI للجسم)
- 📹 OpenCV (معالجة الفيديو)
- 🎥 FFmpeg (تحويل الفيديو)
- 🔬 مكتبات علمية متقدمة

**الحجم**: ~5-8 GB

**وقت التثبيت**: 10-30 دقيقة (حسب سرعة الإنترنت)

**الأمر**:
```bash
pip install -r requirements.txt
```

**متى تستخدمه؟**
- 🔬 عند استخدام ميزات تحليل الحركة بالـ AI
- 📹 عند معالجة الفيديوهات
- 🏋️ عند تدريب نماذج Machine Learning
- 💪 على أجهزة قوية فقط

---

## 🎯 التوصيات

### للمبتدئين 👶

```bash
# الأمر الوحيد الذي تحتاجه:
pip install -r requirements-minimal.txt
```

ثم شغّل:
```bash
START.bat
```

---

### للمحترفين 🧑‍💻

```bash
# أولاً: ثبّت الأساسيات
pip install -r requirements-minimal.txt

# اختبر التطبيق
python -m streamlit run app.py

# إذا كنت راضٍ، ثبّت المتقدمة
pip install -r requirements.txt
```

---

## ❓ أسئلة شائعة

### س: هل يجب تثبيت الاثنين؟

**ج**: لا! فقط واحد:
- `requirements-minimal.txt` للتشغيل العادي ⭐
- `requirements.txt` للميزات المتقدمة (اختياري)

---

### س: ماذا لو ثبّت minimal ثم أردت المتقدم؟

**ج**: لا مشكلة! فقط شغّل:
```bash
pip install -r requirements.txt
```

سيثبت الباقي فقط (لن يعيد تثبيت الموجود)

---

### س: كيف أعرف أي مكتبات مثبتة؟

**ج**: شغّل:
```bash
pip list
```

---

### س: لدي مساحة محدودة، ماذا أفعل؟

**ج**: استخدم minimal فقط:
```bash
pip install -r requirements-minimal.txt
```

كافٍ جداً لكل الميزات الأساسية!

---

### س: البرنامج لا يشتغل بعد تثبيت minimal

**ج**: تحقق من الأخطاء:

```bash
# إذا ظهر: ModuleNotFoundError
pip install -r requirements-minimal.txt

# إذا ظهر: streamlit not recognized
python -m streamlit run app.py

# أو ببساطة شغّل:
START.bat
```

---

## 🔧 استكشاف الأخطاء

### خطأ: `No module named 'plotly'`

**الحل**:
```bash
pip install -r requirements-minimal.txt
```

---

### خطأ: `No module named 'tensorflow'`

**الحل 1** (إذا لا تحتاجه):
لا تقلق! البرنامج يعمل بدونه

**الحل 2** (إذا تحتاجه):
```bash
pip install -r requirements.txt
```
⚠️ تحذير: حجم كبير!

---

## 📊 مقارنة سريعة

| الميزة | minimal | full |
|--------|---------|------|
| الحجم | ~200 MB | ~5-8 GB |
| الوقت | 1-3 دقائق | 10-30 دقيقة |
| الواجهة | ✅ | ✅ |
| البيانات | ✅ | ✅ |
| الرسوم البيانية | ✅ | ✅ |
| قاعدة البيانات | ✅ | ✅ |
| Excel | ✅ | ✅ |
| AI للجسم | ❌ | ✅ |
| معالجة فيديو | ❌ | ✅ |
| Deep Learning | ❌ | ✅ |

---

## 🚀 البداية السريعة

### Windows:

```bash
# 1. افتح Command Prompt في مجلد المشروع
cd C:\Users\elman\OneDrive\Documents\GitHub\yasooo

# 2. ثبّت المكتبات الأساسية
pip install -r requirements-minimal.txt

# 3. شغّل البرنامج
START.bat
```

### Linux/Mac:

```bash
# 1. انتقل لمجلد المشروع
cd ~/yasooo

# 2. ثبّت المكتبات الأساسية
pip install -r requirements-minimal.txt

# 3. شغّل البرنامج
python -m streamlit run app.py
```

---

## 💡 نصيحة أخيرة

**ابدأ دائماً بـ minimal!**

```bash
pip install -r requirements-minimal.txt
```

إذا احتجت المزيد لاحقاً، يمكنك دائماً ترقية لـ full:

```bash
pip install -r requirements.txt
```

لكن في معظم الحالات، **minimal كافٍ تماماً**! ✅

---

**آخر تحديث**: مارس 2026
**الإصدار**: 1.0.0
