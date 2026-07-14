# 🪟 دليل التثبيت على Windows

## 🔴 المشاكل الموجودة:

من الصور المرفقة، المشاكل هي:

### 1️⃣ المكتبات غير مثبتة على جهازك
```
⚠️ المكتبات غير مثبتة
pip install mediapipe tensorflow opencv-python
```

### 2️⃣ خطأ في صفحة إدارة الأعضاء
```
KeyError: "['phone', 'skill_level'] not in index"
```
**تم إصلاحها! ✅** - حمّل آخر نسخة

---

## ✅ الحل السريع (3 خطوات):

### الخطوة 1: حمّل آخر نسخة من الكود

افتح **Command Prompt** أو **PowerShell** في مجلد المشروع:

```powershell
cd C:\Users\elman\Downloads\Compressed\yasooo-claude-skating-analysis-system-019JhsA9HHwcSgQ6oXnujCjf_2

# حمّل آخر التحديثات
git pull origin claude/skating-analysis-system-019JhsA9HHwcSgQ6oXnujCjf
```

### الخطوة 2: ثبّت المكتبات

```powershell
# تثبيت المكتبات الأساسية (إلزامي)
pip install streamlit pandas plotly

# تثبيت مكتبات الذكاء الاصطناعي (اختياري - للميزات المتقدمة)
pip install mediapipe opencv-python numpy

# تثبيت TensorFlow و PyTorch (اختياري - للتدريب)
pip install tensorflow torch
```

**ملاحظة:** إذا واجهت مشاكل مع TensorFlow أو PyTorch:
- يمكنك تخطيهم - التطبيق سيعمل بدونهم
- فقط MediaPipe مطلوب للتحليل الأساسي

### الخطوة 3: شغّل التطبيق

```powershell
python -m streamlit run ultimate_app.py
```

---

## 🎯 التحقق من التثبيت:

بعد تشغيل التطبيق، افتح:
```
http://localhost:8501
```

1. اذهب للصفحة الرئيسية
2. افتح قسم **"🔍 حالة مكتبات الذكاء الاصطناعي"**
3. تحقق من الحالة:
   - ✅ **MediaPipe**: يجب أن يظهر رقم الإصدار
   - ✅ **TensorFlow**: (اختياري)
   - ✅ **PyTorch**: (اختياري)
   - ✅ **محرك التحليل**: يجب أن يكون "متاح"

---

## 🐛 إذا استمرت المشاكل:

### مشكلة: `git pull` لا يعمل

**الحل:** حمّل الملف يدوياً من GitHub أو انسخ `ultimate_app.py` الجديد

### مشكلة: `pip install` فشل

**الحل 1:** جرّب واحد واحد:
```powershell
pip install mediapipe
pip install opencv-python
pip install numpy
```

**الحل 2:** استخدم نسخة Python 3.11 أو 3.12:
```powershell
python --version
```

### مشكلة: MediaPipe لا يثبّت

**الحل:** جرّب النسخة المحددة:
```powershell
pip install mediapipe==0.10.33
```

---

## 📊 الميزات المتاحة بدون مكتبات AI:

حتى بدون تثبيت مكتبات الذكاء الاصطناعي، يمكنك استخدام:

- ✅ **إدارة الأعضاء** - كاملة
- ✅ **تحليل الحضور** - كامل
- ✅ **الإحصائيات** - كاملة
- ✅ **إدارة الاشتراكات** - كاملة

الميزات التي تحتاج مكتبات AI:
- 🤖 **تدريب النموذج** - يحتاج MediaPipe + TensorFlow
- 🏅 **واجهة الحكام** - يحتاج MediaPipe فقط
- 🎥 **تحليل الفيديو الاحترافي** - يحتاج كل المكتبات

---

## 🆘 الدعم:

إذا استمرت المشاكل:

1. **أخذ صورة** (Screenshot) من:
   - رسالة الخطأ الكاملة
   - نتيجة `pip list` في Command Prompt
   - قسم "حالة المكتبات" في التطبيق

2. **شارك** الصور لأساعدك

3. **جرّب** التطبيق الأساسي أولاً:
   ```powershell
   python -m streamlit run app.py
   ```

---

**آخر تحديث:** 2026-04-10  
**الإصدار:** v2.1 - مع إصلاح أخطاء إدارة الأعضاء
