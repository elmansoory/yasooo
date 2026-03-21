# 🔧 دليل حل المشاكل الشائعة

## 📋 المحتويات
1. [مشاكل التثبيت](#مشاكل-التثبيت)
2. [مشاكل المكتبات](#مشاكل-المكتبات)
3. [مشاكل قاعدة البيانات](#مشاكل-قاعدة-البيانات)
4. [مشاكل التشغيل](#مشاكل-التشغيل)
5. [مشاكل الأداء](#مشاكل-الأداء)

---

## 🔴 مشاكل التثبيت

### ❌ خطأ: `Python is not recognized`

**السبب**: Python غير مضاف إلى PATH

**الحل**:
1. أعد تثبيت Python من https://www.python.org/downloads/
2. **مهم**: فعّل خيار "Add Python to PATH" أثناء التثبيت
3. أعد تشغيل Command Prompt
4. تحقق:
   ```cmd
   python --version
   ```

**الحل البديل** (إضافة يدوية للـ PATH):
1. اضغط `Windows + R`
2. اكتب `sysdm.cpl` واضغط Enter
3. علامة تبويب "Advanced" → "Environment Variables"
4. في "System variables" ابحث عن "Path"
5. أضف:
   - `C:\Users\[اسمك]\AppData\Local\Programs\Python\Python311\`
   - `C:\Users\[اسمك]\AppData\Local\Programs\Python\Python311\Scripts\`

---

### ❌ خطأ: `pip is not recognized`

**الحل**:
```cmd
python -m pip install --upgrade pip
```

ثم:
```cmd
python -m pip install -r requirements.txt
```

---

## 🔴 مشاكل المكتبات

### ❌ خطأ: `Missing optional dependency 'openpyxl'`

**الرسالة الكاملة**:
```
ImportError: Missing optional dependency 'openpyxl'. Use pip or conda to install openpyxl.
```

**السبب**: مكتبة openpyxl غير مثبتة (ضرورية لقراءة ملفات Excel)

**الحل السريع**:
```cmd
pip install openpyxl
```

**الحل الشامل**:
```cmd
pip install -r requirements.txt
```

**التحقق**:
```cmd
pip list | findstr openpyxl
```
يجب أن يظهر: `openpyxl    3.1.0` (أو أحدث)

**النتيجة المتوقعة بعد الحل**:
عند تشغيل `python import_all_data.py` ستجد:
```
✅ تم استيراد 102 عضو
✅ تم استيراد 839 سجل حضور
✅ تم استيراد 53 عضوية
```

بدلاً من:
```
❌ عدد الأعضاء: 0
❌ سجلات الحضور: 0
```

---

### ❌ خطأ: `No module named 'streamlit'`

**الحل**:
```cmd
pip install streamlit
```

---

### ❌ خطأ: `No module named 'pandas'`

**الحل**:
```cmd
pip install pandas
```

---

### ❌ خطأ: `No module named 'sqlalchemy'`

**الحل**:
```cmd
pip install sqlalchemy
```

---

### ❌ خطأ: `No module named 'plotly'`

**الحل**:
```cmd
pip install plotly
```

---

### ❌ خطأ في تثبيت opencv-python

**الرسالة**:
```
ERROR: Could not build wheels for opencv-python
```

**الحل**:
```cmd
pip install opencv-python-headless
```

ثم عدّل `requirements.txt`:
- احذف السطر: `opencv-python>=4.8.0`
- أضف: `opencv-python-headless>=4.8.0`

---

## 🔴 مشاكل قاعدة البيانات

### ❌ قاعدة البيانات فارغة (0 أعضاء، 0 حضور)

**السبب المحتمل 1**: لم يتم تشغيل برنامج الاستيراد

**الحل**:
```cmd
python import_all_data.py
```

**السبب المحتمل 2**: مكتبة openpyxl غير مثبتة

**الحل**:
```cmd
pip install openpyxl
python import_all_data.py
```

---

### ❌ خطأ: `database is locked`

**السبب**: قاعدة البيانات مفتوحة في برنامج آخر

**الحل**:
1. أغلق جميع نوافذ Streamlit
2. أغلق أي برنامج يفتح `skating_database.db`
3. شغّل البرنامج مرة أخرى

---

### ❌ البيانات القديمة لا تتحدث

**الحل**:
1. أوقف Streamlit (Ctrl+C)
2. شغّل برنامج الاستيراد:
   ```cmd
   python import_all_data.py
   ```
3. شغّل Streamlit مرة أخرى:
   ```cmd
   streamlit run app.py
   ```
4. اضغط "Ctrl+Shift+R" في المتصفح (لمسح الكاش)

---

## 🔴 مشاكل التشغيل

### ❌ خطأ: `Address already in use`

**السبب**: المنفذ 8501 قيد الاستخدام

**الحل 1** (استخدام منفذ آخر):
```cmd
streamlit run app.py --server.port 8502
```

**الحل 2** (إيقاف العملية القديمة):
```cmd
netstat -ano | findstr :8501
taskkill /PID [رقم_العملية] /F
```

---

### ❌ الصفحة لا تفتح تلقائياً

**الحل**:
1. افتح المتصفح يدوياً
2. اذهب إلى: http://localhost:8501

---

### ❌ خطأ: `FileNotFoundError: data/members.xlsx`

**السبب**: ملفات Excel غير موجودة

**الحل**:
تحقق من وجود الملفات:
```
yasooo/
├── data/
│   ├── members.xlsx
│   ├── august_attendance.xlsx
│   └── october_attendance.xlsx
```

إذا كانت غير موجودة، حمّل المشروع كاملاً من GitHub.

---

## 🔴 مشاكل الأداء

### ⚠️ البرنامج بطيء

**الحلول**:
1. أغلق البرامج الأخرى
2. تأكد من وجود 4GB RAM متاحة على الأقل
3. استخدم Chrome أو Edge (أسرع من Firefox لـ Streamlit)
4. امسح كاش المتصفح:
   - Chrome: `Ctrl+Shift+Delete`
   - اختر "Cached images and files"
   - اضغط "Clear data"

---

### ⚠️ الرسوم البيانية لا تظهر

**الحل**:
1. تأكد من اتصال الإنترنت (Plotly يحتاج اتصال للمرة الأولى)
2. امسح كاش المتصفح
3. أعد تحميل الصفحة (Ctrl+Shift+R)
4. جرب متصفح آخر

---

### ⚠️ رسالة: `Please wait... Loading data`

**إذا استمرت أكثر من دقيقة**:

**الحل**:
1. افتح Command Prompt حيث يعمل Streamlit
2. ابحث عن رسائل الخطأ
3. اضغط Ctrl+C لإيقاف البرنامج
4. شغّله مرة أخرى

---

## 🔴 مشاكل عامة

### ❌ خطأ: `UnicodeDecodeError`

**السبب**: مشكلة في ترميز الملفات

**الحل**:
```cmd
chcp 65001
streamlit run app.py
```

---

### ❌ خطأ: `ModuleNotFoundError: No module named 'app'`

**السبب**: تشغيل الأمر من مجلد خاطئ

**الحل**:
```cmd
cd C:\Path\To\yasooo
streamlit run app.py
```

---

## ✅ التحقق من التثبيت الصحيح

شغّل هذه الأوامر للتحقق:

### 1. تحقق من Python:
```cmd
python --version
```
✅ يجب أن يظهر: `Python 3.10.x` أو أحدث

### 2. تحقق من pip:
```cmd
pip --version
```
✅ يجب أن يظهر رقم إصدار pip

### 3. تحقق من المكتبات الأساسية:
```cmd
pip list | findstr streamlit
pip list | findstr pandas
pip list | findstr openpyxl
pip list | findstr sqlalchemy
```
✅ يجب أن تظهر جميعها

### 4. تحقق من قاعدة البيانات:
```cmd
python import_all_data.py
```
✅ يجب أن يظهر:
```
✅ تم استيراد 102 عضو
✅ تم استيراد 839 سجل حضور
✅ تم استيراد 53 عضوية
```

### 5. تحقق من البرنامج:
```cmd
streamlit run app.py
```
✅ يجب أن يفتح في المتصفح على http://localhost:8501

---

## 📞 إذا استمرت المشكلة

### خطوات التشخيص:

1. **احذف البيئة القديمة**:
   ```cmd
   pip uninstall streamlit pandas openpyxl sqlalchemy plotly -y
   ```

2. **أعد التثبيت من الصفر**:
   ```cmd
   pip install -r requirements.txt
   ```

3. **احذف قاعدة البيانات**:
   ```cmd
   del skating_database.db
   ```

4. **أعد بناء قاعدة البيانات**:
   ```cmd
   python import_all_data.py
   ```

5. **شغّل البرنامج**:
   ```cmd
   streamlit run app.py
   ```

---

## 🎯 نصائح للوقاية من المشاكل

✅ **دائماً**:
- ثبّت Python في مسار بدون مسافات: `C:\Python311\` بدلاً من `C:\Program Files\Python\`
- فعّل "Add Python to PATH" أثناء التثبيت
- أعد تشغيل Command Prompt بعد تثبيت أي شيء
- استخدم `python -m pip` بدلاً من `pip` إذا واجهت مشاكل

❌ **لا تفعل**:
- لا تثبت Python في مجلد محمي (Program Files)
- لا تستخدم مسافات في أسماء المجلدات
- لا تفتح قاعدة البيانات في أكثر من برنامج
- لا تعدّل الملفات أثناء تشغيل Streamlit

---

## 📝 سجل الأخطاء الشائعة

| الخطأ | السبب | الحل السريع |
|-------|-------|-------------|
| `openpyxl not found` | مكتبة غير مثبتة | `pip install openpyxl` |
| `Python not recognized` | PATH غير مضبوط | أعد تثبيت Python |
| `0 members` | لم يتم استيراد البيانات | `python import_all_data.py` |
| `Port in use` | المنفذ محجوز | `streamlit run app.py --server.port 8502` |
| `Database locked` | ملف مفتوح | أغلق جميع البرامج وأعد المحاولة |

---

**آخر تحديث**: مارس 2026
**الإصدار**: 1.0.0

🎿 **للمساعدة الإضافية، راجع**: `WINDOWS_SETUP.md` أو `HOW_TO_USE.md`
