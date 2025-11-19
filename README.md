# 🏒 نظام تحليل التزلج الفني المتقدم

## Figure Skating Analysis System

نظام متقدم لتحليل فيديوهات التزلج الفني باستخدام الذكاء الاصطناعي ومعايير الاتحاد الدولي للتزلج (ISU).

---

## 🌟 الميزات الرئيسية

### ✨ التحليل الذكي
- 🎯 **كشف الوضعيات** باستخدام MediaPipe
- 🤖 **تصنيف الحركات** بالذكاء الاصطناعي
- 📊 **تسجيل احترافي** وفق معايير ISU
- 🎥 **معالجة فيديو** متقدمة

### 📈 التتبع والتحليل
- 📉 **تتبع التقدم** عبر الزمن
- 📊 **إحصائيات مفصلة**
- 📝 **تقارير شاملة**
- 💾 **قاعدة بيانات** منظمة

### 🎯 معايير ISU
- ✅ **جميع القفزات** (Single إلى Quadruple)
- ✅ **جميع الدورانات** (7 أنواع × 5 مستويات)
- ✅ **تسلسلات الخطوات**
- ✅ **حساب GOE** (-5 إلى +5)
- ✅ **المكونات البرنامجية** (5 عناصر)

---

## 🚀 التثبيت والإعداد

### المتطلبات الأساسية

- Python 3.10 أو أحدث
- FFmpeg (لمعالجة الفيديو)
- 16GB RAM على الأقل
- GPU (اختياري للتدريب)

### خطوات التثبيت

```bash
# 1. استنساخ المشروع
git clone https://github.com/elmansoory/yasooo.git
cd yasooo

# 2. إنشاء بيئة افتراضية
python -m venv venv

# 3. تفعيل البيئة
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 4. تثبيت المتطلبات
pip install -r requirements.txt

# 5. إعداد المتغيرات البيئية
cp .env.example .env
# عدل ملف .env حسب الحاجة

# 6. تشغيل التطبيق
streamlit run app.py
```

---

## 📁 بنية المشروع

```
yasooo/
├── src/                    # الكود المصدري
│   ├── config/            # الإعدادات ومعايير ISU
│   ├── core/              # المعالجة الأساسية
│   ├── models/            # نماذج التصنيف
│   ├── analysis/          # محرك التحليل
│   ├── database/          # قاعدة البيانات
│   ├── ui/                # واجهة المستخدم
│   └── utils/             # الأدوات المساعدة
├── data/                   # البيانات
│   ├── models/            # النماذج المدربة
│   ├── videos/            # الفيديوهات
│   ├── cache/             # التخزين المؤقت
│   └── exports/           # التصديرات
├── tests/                  # الاختبارات
├── docs/                   # التوثيق
├── app.py                 # التطبيق الرئيسي
├── requirements.txt       # المتطلبات
└── README.md             # هذا الملف
```

---

## 💡 الاستخدام

### 1. إضافة متزلج

```python
from src.database.database_manager import DatabaseManager
from src.database.models import Skater

db = DatabaseManager('sqlite:///skating.db')
db.init_db()

with db.get_session() as session:
    skater = Skater(
        name="محمد أحمد",
        country="السعودية",
        gender="ذكر",
        category="Senior",
        discipline="Men"
    )
    session.add(skater)
```

### 2. تحليل فيديو

```python
from src.core.video_processor import VideoProcessor
from src.core.pose_detector import PoseDetector

# معالجة الفيديو
with VideoProcessor('video.mp4') as proc:
    for frame_idx, frame in proc.extract_frames(skip_frames=2):
        # كشف الوضعيات
        pose_detector = PoseDetector()
        pose_data = pose_detector.detect(frame)

        if pose_data:
            # تحليل الوضعية
            print(f"Frame {frame_idx}: {pose_data.angles}")
```

### 3. حساب الدرجات

```python
from src.analysis.scoring_engine import ScoringEngine

engine = ScoringEngine()

# حساب درجة برنامج كامل
elements = [
    {'code': '3A', 'goe': 2},
    {'code': '3Lz', 'goe': 1},
    {'code': 'CCoSp4', 'goe': 3}
]

score = engine.calculate_total_score(
    elements=elements,
    skating_skills=8.5,
    transitions=8.0,
    performance=8.25,
    composition=8.0,
    interpretation=8.5
)

print(f"الدرجة النهائية: {score.total_score}")
```

---

## 🎯 معايير ISU المدعومة

### القفزات (24 قفزة)

| النوع | Single | Double | Triple | Quad |
|-------|--------|--------|--------|------|
| Axel | 1.10 | 3.30 | 8.00 | 12.50 |
| Lutz | 0.60 | 2.10 | 5.90 | 11.50 |
| Flip | 0.50 | 1.80 | 5.30 | 11.00 |
| Loop | 0.50 | 1.70 | 4.90 | 10.50 |
| Salchow | 0.40 | 1.30 | 4.30 | 9.70 |
| Toe Loop | 0.40 | 1.30 | 4.20 | 9.50 |

### الدورانات (7 أنواع)

- Upright Spin (USp)
- Layback Spin (LSp)
- Camel Spin (CSp)
- Sit Spin (SSp)
- Combination Spin (CoSp)
- Flying Camel Spin (FCSp)
- Flying Sit Spin (FSSp)

### GOE Scale

```
+5: استثنائي
+4: ممتاز جداً
+3: ممتاز
+2: جيد جداً
+1: جيد
 0: متوسط
-1: ضعيف
-2: ضعيف جداً
-3: سيء
-4: سيء جداً
-5: سقوط/خطأ فادح
```

---

## 🧪 الاختبارات

```bash
# تشغيل جميع الاختبارات
pytest

# اختبارات مع التغطية
pytest --cov=src tests/

# اختبارات محددة
pytest tests/test_video_processor.py
```

---

## 📚 التوثيق

- [دليل المستخدم](docs/user_guide.md)
- [مرجع API](docs/api_reference.md)
- [معايير ISU](docs/isu_standards.md)

---

## 🤝 المساهمة

نرحب بالمساهمات! يرجى:

1. Fork المشروع
2. إنشاء فرع للميزة (`git checkout -b feature/AmazingFeature`)
3. Commit التغييرات (`git commit -m 'Add AmazingFeature'`)
4. Push للفرع (`git push origin feature/AmazingFeature`)
5. فتح Pull Request

---

## 📄 الترخيص

هذا المشروع مرخص تحت رخصة MIT - راجع ملف [LICENSE](LICENSE) للتفاصيل.

---

## 👨‍💻 المطور

**Elmansoory**

- GitHub: [@elmansoory](https://github.com/elmansoory)

---

## 🙏 شكر وتقدير

- [MediaPipe](https://mediapipe.dev/) - كشف الوضعيات
- [OpenCV](https://opencv.org/) - معالجة الفيديو
- [Streamlit](https://streamlit.io/) - واجهة المستخدم
- [ISU](https://www.isu.org/) - معايير التسجيل

---

## 📞 الدعم

للدعم والاستفسارات:
- فتح [Issue](https://github.com/elmansoory/yasooo/issues)
- البريد الإلكتروني: support@example.com

---

<div align="center">

**صنع بـ ❤️ للتزلج الفني**

</div>
