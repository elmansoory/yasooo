# سجل التحديثات - Changelog

## [النسخة الأحدث] - 2025-11-19

### 🔧 إصلاحات (Fixes)

#### إصلاح خطأ SQLAlchemy الحرج
- **المشكلة**: خطأ `InvalidRequestError: Attribute name 'metadata' is reserved`
- **السبب**: استخدام كلمة محجوزة `metadata` كاسم عمود في قاعدة البيانات
- **الحل**: تغيير `Analysis.metadata` إلى `Analysis.analysis_metadata`
- **الملف المُصلح**: `src/database/models.py:96`
- **Commit**: e75fb42

```python
# قبل (Before):
metadata = Column(JSON)

# بعد (After):
analysis_metadata = Column(JSON)
```

### 📦 التحديثات الأخرى

- إضافة الأرشيفات المضغوطة إلى `.gitignore`
- Commit: abd7010

---

## [الإصدار الأولي] - 2025-11-19

### ✨ الميزات الجديدة (Features)

#### نظام تحليل التزلج الفني الكامل
- Commit: fdf0b2c

**المكونات الأساسية:**
- معايير ISU 2024 الكاملة (24 قفزة + 35 دوران)
- معالجة الفيديو باستخدام OpenCV
- كشف الوضعيات بـ MediaPipe (33 نقطة مفصل)
- محرك التسجيل التلقائي مع حساب GOE
- تطبيق Streamlit بالواجهة العربية

**البنية التقنية:**
- `src/config/isu_standards.py`: قاعدة بيانات معايير ISU
- `src/core/pose_detector.py`: كشف الوضعيات بـ MediaPipe
- `src/core/video_processor.py`: معالجة الفيديو
- `src/analysis/scoring_engine.py`: حسابات التسجيل ISU
- `src/database/`: نماذج SQLAlchemy وإدارة قاعدة البيانات
- `app.py`: تطبيق Streamlit الكامل (437 سطر)
- `demo.py`: نسخة تجريبية تفاعلية (167 سطر)

**البنية التحتية:**
- إعداد Docker (Dockerfile, docker-compose.yml)
- CI/CD مع GitHub Actions
- مجموعة اختبارات للمكونات الأساسية
- توثيق شامل (README, QUICKSTART)

**الإحصائيات:**
- 37 ملف بإجمالي 4,929 سطر كود
- دعم صيغ MP4, AVI, MOV, MKV
- دعم متعدد اللغات (عربي/إنجليزي)

---

## طريقة التشغيل السريعة

### النسخة التجريبية (بدون تثبيت!)
```bash
python demo.py
```

### التطبيق الكامل
```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## ملاحظات مهمة

⚠️ **تأكد من استخدام النسخة الأحدث!**

إذا واجهت خطأ SQLAlchemy:
```
InvalidRequestError: Attribute name 'metadata' is reserved
```

قم بتحميل الملفات الأحدث:
- `yasooo-latest.tar.gz` أو
- `yasooo-latest.zip`

---

## المساهمة

راجع `CLAUDE.md` للحصول على دليل كامل للمطورين ومساعدي الذكاء الاصطناعي.

---

آخر تحديث: 2025-11-19
