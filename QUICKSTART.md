# 🚀 البدء السريع - Quick Start

## التثبيت السريع في 3 دقائق

### الطريقة 1: Docker (الأسهل) 🐳

```bash
# 1. استنساخ المشروع
git clone https://github.com/elmansoory/yasooo.git
cd yasooo

# 2. تشغيل بـ Docker
docker-compose up -d

# 3. افتح المتصفح
# http://localhost:8501
```

✅ **جاهز! التطبيق يعمل الآن**

---

### الطريقة 2: التثبيت المحلي ⚡

```bash
# 1. استنساخ المشروع
git clone https://github.com/elmansoory/yasooo.git
cd yasooo

# 2. إنشاء بيئة افتراضية
python -m venv venv
source venv/bin/activate  # Linux/Mac
# أو
venv\Scripts\activate  # Windows

# 3. تثبيت المتطلبات
pip install -r requirements.txt

# 4. تشغيل التطبيق
streamlit run app.py
```

✅ **التطبيق يعمل على http://localhost:8501**

---

## الاستخدام السريع

### 1️⃣ إضافة متزلج

```python
# من واجهة التطبيق:
# 👥 إدارة المتزلجين > ➕ إضافة متزلج
```

أو برمجياً:

```python
from src.database.database_manager import DatabaseManager
from src.database.models import Skater

db = DatabaseManager('sqlite:///skating_analysis.db')
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

print("✅ تمت إضافة المتزلج")
```

---

### 2️⃣ تحليل فيديو

```python
# من الواجهة:
# 📹 تحليل فيديو جديد > ارفع الفيديو > 🚀 بدء التحليل
```

أو برمجياً:

```python
from src.core.video_processor import VideoProcessor
from src.core.pose_detector import PoseDetector
from src.analysis.scoring_engine import ScoringEngine

# 1. معالجة الفيديو
with VideoProcessor('video.mp4') as proc:
    # 2. كشف الوضعيات
    detector = PoseDetector()

    for frame_idx, frame in proc.extract_frames(skip_frames=2):
        pose_data = detector.detect(frame)
        if pose_data:
            print(f"إطار {frame_idx}: زوايا={pose_data.angles}")

# 3. حساب الدرجات
engine = ScoringEngine()
elements = [
    {'code': '3A', 'goe': 2},
    {'code': '3Lz', 'goe': 1}
]

score = engine.calculate_total_score(
    elements=elements,
    skating_skills=8.5,
    transitions=8.0,
    performance=8.25
)

print(f"الدرجة النهائية: {score.total_score}")
```

---

### 3️⃣ عرض معايير ISU

```python
from src.config.isu_standards import ISUStandards

standards = ISUStandards()

# عرض القفزات
print("القفزات:")
for code, info in standards.JUMPS.items():
    print(f"  {code}: {info['name']} - {info['base_value']}")

# الحصول على معلومات قفزة
jump_info = standards.get_element_info('3A')
print(f"\nTriple Axel: {jump_info}")

# حساب GOE
base_value = 8.0
goe = 2
goe_value = standards.calculate_goe_value(base_value, goe)
print(f"القيمة الأساسية: {base_value}")
print(f"GOE: +{goe}")
print(f"قيمة GOE: {goe_value}")
print(f"المجموع: {base_value + goe_value}")
```

---

## أمثلة متقدمة

### مثال 1: تحليل كامل لبرنامج

```python
from src.analysis.scoring_engine import ScoringEngine

engine = ScoringEngine()

# عناصر برنامج حر
elements = [
    {'code': '4T', 'goe': 1},      # Quad Toe Loop
    {'code': '3A', 'goe': 3},      # Triple Axel
    {'code': '3Lz', 'goe': 2},     # Triple Lutz
    {'code': '3F', 'goe': 1},      # Triple Flip
    {'code': 'CCoSp4', 'goe': 2},  # Combo Spin Level 4
    {'code': 'StSq4', 'goe': 3},   # Step Sequence Level 4
]

# حساب الدرجة الكاملة
score = engine.calculate_total_score(
    elements=elements,
    skating_skills=9.0,
    transitions=8.75,
    performance=9.0,
    composition=8.5,
    interpretation=9.25,
    deductions={'fall': 1},  # سقطة واحدة
    program_type='free'
)

print("=" * 50)
print("نتائج التحليل")
print("=" * 50)
print(f"القيمة الأساسية: {score.total_base_value:.2f}")
print(f"مجموع GOE: {score.total_goe:+.2f}")
print(f"الدرجة التقنية: {score.technical_score:.2f}")
print(f"درجة المكونات: {score.program_components_score:.2f}")
print(f"الخصومات: -{score.total_deductions:.2f}")
print(f"الدرجة النهائية: {score.total_score:.2f}")
print("=" * 50)

# تفاصيل العناصر
print("\nتفاصيل العناصر:")
for elem in score.elements:
    print(f"  {elem.element_code}: {elem.element_name}")
    print(f"    القيمة: {elem.base_value:.2f} + GOE {elem.goe:+d} ({elem.goe_value:+.2f}) = {elem.total_score:.2f}")
```

---

### مثال 2: مقارنة متزلجين

```python
from src.database.database_manager import DatabaseManager
from src.database.models import Skater, Analysis
from sqlalchemy import func

db = DatabaseManager('sqlite:///skating_analysis.db')
db.init_db()

with db.get_session() as session:
    # أفضل 5 متزلجين
    top_skaters = session.query(
        Skater.name,
        func.avg(Analysis.overall_score).label('avg_score')
    ).join(
        Skater.videos
    ).join(
        Video.analyses
    ).group_by(
        Skater.id
    ).order_by(
        func.avg(Analysis.overall_score).desc()
    ).limit(5).all()

    print("🏆 أفضل 5 متزلجين:")
    for rank, (name, avg_score) in enumerate(top_skaters, 1):
        print(f"  {rank}. {name}: {avg_score:.2f}")
```

---

## الاختبارات

```bash
# تشغيل جميع الاختبارات
pytest

# مع التغطية
pytest --cov=src tests/

# اختبار محدد
pytest tests/test_scoring_engine.py -v
```

---

## النشر على السحابة

### Heroku

```bash
# إنشاء تطبيق
heroku create yasooo-skating

# إضافة PostgreSQL
heroku addons:create heroku-postgresql:hobby-dev

# النشر
git push heroku main

# فتح التطبيق
heroku open
```

### AWS / Google Cloud / Azure

راجع [دليل النشر الكامل](docs/deployment.md)

---

## المساعدة والدعم

- 📚 [الوثائق الكاملة](README.md)
- 🐛 [الإبلاغ عن مشكلة](https://github.com/elmansoory/yasooo/issues)
- 💬 [المناقشات](https://github.com/elmansoory/yasooo/discussions)

---

## نصائح سريعة

### ⚡ تحسين الأداء

```python
# استخدم skip_frames لتحليل أسرع
for idx, frame in proc.extract_frames(skip_frames=5):  # كل 5 إطارات
    # ...

# قلل دقة الفيديو
resized = proc.resize_frame(frame, (640, 480))
```

### 🎯 دقة أعلى

```python
# استخدم نموذج MediaPipe معقد
from src.config.config import get_config

config = get_config()
config.POSE_MODEL_COMPLEXITY = 2  # 0, 1, or 2 (الأبطأ والأدق)
```

### 💾 حفظ النتائج

```python
# التصدير إلى Excel
from src.database.database_manager import DatabaseManager

db = DatabaseManager('sqlite:///skating_analysis.db')
# ... استعلامات وتصدير
```

---

**🎉 مبروك! أنت الآن جاهز لاستخدام نظام تحليل التزلج الفني!**
