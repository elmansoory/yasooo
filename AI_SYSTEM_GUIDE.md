# 🤖 دليل النظام الذكي للتعرف على الحركات
## AI Movement Recognition System Guide

---

## 📋 نظرة عامة - Overview

تم إضافة نظام ذكاء اصطناعي متقدم لتحليل التزلج الفني يستخدم تقنيات التعلم الآلي للتعرف تلقائياً على:

### الحركات المدعومة:

#### 🦘 القفزات - Jumps (24 نوع)
- **Axel Family** (A, 2A, 3A, 4A) - القفزة الوحيدة التي تبدأ من الأمام
- **Lutz** (Lz, 2Lz, 3Lz, 4Lz) - حافة خارجية خلفية + مسننات
- **Flip** (F, 2F, 3F, 4F) - حافة داخلية خلفية + مسننات
- **Loop** (Lo, 2Lo, 3Lo, 4Lo) - حافة خارجية خلفية
- **Salchow** (S, 2S, 3S, 4S) - حافة داخلية خلفية
- **Toe Loop** (T, 2T, 3T, 4T) - حافة خارجية خلفية + مسننات

#### 🌀 الدورانات - Spins (35+ نوع)
- **Upright Spin (USp)** - دوران منتصب (مستويات 1-4)
- **Sit Spin (SSp)** - دوران جلوس (مستويات 1-4)
- **Camel Spin (CSp)** - دوران الجمل (مستويات 1-4)
- **Flying Spin (FSp)** - دوران طائر (مستويات 1-4)
- **Combination Spin (CoSp)** - دوران مركب (مستويات 1-4)

#### 🚶 تسلسلات الخطوات - Step Sequences
- **StSq (1-4)** - تسلسل خطوات (مستويات 1-4)
- **ChSq (1)** - تسلسل فني

---

## 🏗️ البنية التقنية - Technical Architecture

### 📁 الملفات الرئيسية:

```
src/models/
├── movement_classifier.py      # نموذج التصنيف الرئيسي
│   ├── MovementClassifier      # المصنف الرئيسي
│   ├── JumpDetector           # كاشف القفزات (24 نوع)
│   ├── SpinDetector           # كاشف الدورانات (35+ نوع)
│   └── StepSequenceDetector   # كاشف تسلسلات الخطوات
│
└── training_engine.py          # محرك التدريب
    ├── TrainingEngine          # إدارة التدريب والتقييم
    └── FeatureExtractor        # استخراج الخصائص
```

### 🧠 كيف يعمل النظام:

```
1. استخراج الوضعيات (Pose Detection)
   ↓
2. استخراج الخصائص (Feature Extraction)
   ├─ خصائص الموضع (center of mass, angles)
   ├─ خصائص الحركة (velocity, rotation)
   ├─ خصائص القفز (airtime, takeoff/landing angles)
   ├─ خصائص الدوران (spin speed, axis stability)
   └─ خصائص عامة (duration, complexity)
   ↓
3. التصنيف (Classification)
   ├─ تحديد نوع الحركة (قفزة/دوران/خطوات)
   ├─ التعرف على العنصر المحدد
   ├─ تقدير GOE (-5 إلى +5)
   └─ حساب الثقة (Confidence)
   ↓
4. حساب الدرجات (Scoring)
   └─ استخدام معايير ISU
```

---

## 🚀 كيفية الاستخدام - How to Use

### من واجهة المستخدم (Streamlit):

1. **افتح التطبيق:**
   ```bash
   streamlit run app.py
   ```

2. **انتقل إلى "📹 تحليل فيديو جديد"**

3. **فعّل التحليل الذكي:**
   - ✅ ضع علامة على "🤖 استخدام التحليل الذكي (AI)"

4. **اختر إعدادات التحليل:**
   - اللاعب
   - نوع التحليل
   - نوع البرنامج (قصير/حر)

5. **ارفع الفيديو واضغط "🤖 بدء التحليل الذكي"**

### من الكود (Python):

```python
from src.models.movement_classifier import MovementClassifier, MovementFeatures
from src.models.training_engine import FeatureExtractor

# 1. تهيئة النماذج
classifier = MovementClassifier()
extractor = FeatureExtractor()

# 2. استخراج الخصائص من بيانات الوضعيات
pose_sequence = [...]  # بيانات الوضعيات من MediaPipe
features = extractor.extract_features(pose_sequence)

# 3. التصنيف
result = classifier.classify_movement(features)

# 4. النتيجة
print(f"نوع الحركة: {result['type']}")
print(f"الكود: {result['code']}")
print(f"الثقة: {result['confidence']:.1%}")
print(f"GOE المقدر: {result['estimated_goe']:+d}")
```

---

## 📊 خصائص الحركة - Movement Features

### الخصائص المستخرجة (19 خاصية):

```python
@dataclass
class MovementFeatures:
    # خصائص الموضع (4)
    center_of_mass_height: float
    body_rotation_angle: float
    leg_extension: float
    arm_position: float

    # خصائص الحركة (3)
    vertical_velocity: float
    rotational_velocity: float
    horizontal_velocity: float

    # خصائص القفز (4)
    airtime: float
    takeoff_angle: float
    landing_angle: float
    rotation_count: float

    # خصائص الدوران (3)
    spin_speed: float
    axis_stability: float
    body_position: str

    # خصائص عامة (2)
    duration: float
    complexity: float
```

---

## 🎯 دقة النموذج - Model Accuracy

### آلية تقدير GOE:

#### للقفزات:
- ✅ **جودة الهبوط** (landing_angle > 80°): +1
- ✅ **الارتفاع** (height > 1.5m): +1
- ✅ **الثقة العالية** (confidence > 0.7): base
- ❌ **هبوط ضعيف** (landing_angle < 60°): -1

#### للدورانات:
- ✅ **سرعة عالية** (spin_speed > 3.5 rev/s): +2
- ✅ **ثبات ممتاز** (axis_stability > 0.9): +1
- ✅ **مستوى 4**: +1
- ❌ **ثبات ضعيف** (axis_stability < 0.7): -1

#### لتسلسلات الخطوات:
- ✅ **تعقيد عالٍ** (complexity > 0.85): +2
- ✅ **سرعة عالية** (velocity > 2.0 m/s): +1

---

## 🔍 مثال على النتائج - Example Output

### تحليل برنامج قصير:

```
🤖 معلومات التحليل الذكي
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
عناصر مكتشفة: 6
متوسط الثقة: 78%
وضع التحليل: AI

🔍 الحركات المكتشفة:
┌───┬──────────────┬────────┬────────┬────────────┐
│ # │ النوع        │ الكود  │ الثقة  │ GOE المقدر │
├───┼──────────────┼────────┼────────┼────────────┤
│ 1 │ jump         │ 3A     │ 85%    │ +2         │
│ 2 │ jump         │ 3F     │ 76%    │ +1         │
│ 3 │ jump         │ 3Lz+3T │ 82%    │ +2         │
│ 4 │ spin         │ FCSp4  │ 79%    │ +2         │
│ 5 │ step_seq     │ StSq3  │ 71%    │ +1         │
│ 6 │ spin         │ CCoSp4 │ 88%    │ +3         │
└───┴──────────────┴────────┴────────┴────────────┘

🏆 النتيجة النهائية
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
الدرجة التقنية: 45.80
درجة المكونات: 38.50
الخصومات: -0.00
⭐ الدرجة النهائية: 84.30

🤖 توصيات الذكاء الاصطناعي
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ جودة ممتازة: الفيديو واضح والتحليل دقيق
👍 أداء قوي: التركيز على تحسين GOE سيرفع الدرجة
🦘 القفزات ممتازة: جودة تنفيذ عالية!
🌀 دورانات ممتازة: سرعة وثبات رائعين!
```

---

## ⚙️ تكوين وتخصيص - Configuration

### عتبات التصنيف (Thresholds):

```python
thresholds = {
    'min_jump_airtime': 0.3,      # ثانية
    'min_spin_duration': 2.0,     # ثانية
    'min_spin_speed': 1.5,        # دورة/ثانية
    'min_step_complexity': 0.5
}
```

### تعديل العتبات:

```python
classifier = MovementClassifier()
classifier.thresholds['min_jump_airtime'] = 0.4  # تشديد معيار القفز
```

---

## 🔧 التدريب والتحسين - Training & Improvement

### تحميل بيانات التدريب:

```python
from src.models.training_engine import TrainingEngine

engine = TrainingEngine()

# إضافة عينات تدريب
engine.add_training_sample(
    pose_sequence=[...],
    label='3A',
    metadata={'skater': 'John Doe', 'competition': 'Olympics 2024'}
)

# أو تحميل من ملف
engine.load_training_data('training_data.json')
```

### تقسيم البيانات:

```python
# 80% تدريب، 20% تحقق
engine.split_data(validation_ratio=0.2)
```

### التقييم:

```python
results = engine.evaluate()

print(f"الدقة الإجمالية: {results['accuracy']:.2%}")
print(f"دقة القفزات: {results['category_accuracy']['jumps']:.2%}")
print(f"دقة الدورانات: {results['category_accuracy']['spins']:.2%}")
print(f"دقة الخطوات: {results['category_accuracy']['steps']:.2%}")
```

### حفظ وتحميل النموذج:

```python
# حفظ
engine.save_model('my_model.pkl')

# تحميل
engine.load_model('my_model.pkl')
```

### توليد تقرير:

```python
report = engine.generate_report()
print(report)
```

---

## 📈 الميزات المستقبلية - Future Features

### قيد التطوير:

- [ ] **دمج MediaPipe** للكشف الحقيقي عن الوضعيات من الفيديو
- [ ] **تدريب نماذج Deep Learning** (LSTM, Transformer)
- [ ] **كشف الأخطاء الشائعة** (under-rotation, wrong edge, etc.)
- [ ] **تحليل زمني مفصل** (frame-by-frame breakdown)
- [ ] **مقارنة مع متزلجين آخرين** (benchmark comparison)
- [ ] **تحليل الطاقة والتعب** (energy and fatigue analysis)

### التحسينات المخططة:

- [ ] **زيادة دقة كشف القفزات المركبة** (combination jumps)
- [ ] **تحسين كشف الحافة** (edge detection)
- [ ] **إضافة كشف الأخطاء التقنية** (technical errors)
- [ ] **دعم تحليل الفيديو بالوقت الفعلي** (real-time analysis)

---

## 🐛 استكشاف الأخطاء - Troubleshooting

### المشكلة: دقة منخفضة في التصنيف

**الحلول:**
```python
# 1. تحسين جودة الفيديو
- استخدم فيديوهات بدقة HD على الأقل
- تأكد من رؤية الجسم بالكامل
- إضاءة جيدة وخلفية واضحة

# 2. ضبط العتبات
classifier.thresholds['min_jump_airtime'] = 0.25  # تخفيف المعايير

# 3. إضافة المزيد من بيانات التدريب
engine.add_training_sample(...)
```

### المشكلة: بطء في التحليل

**الحلول:**
```python
# استخدام نماذج أخف
- تقليل دقة الفيديو قبل المعالجة
- استخدام GPU للمعالجة
- تحليل كل n إطار بدلاً من جميع الإطارات
```

---

## 📚 المراجع - References

### معايير ISU:
- [ISU Technical Panel Handbook](https://www.isu.org)
- ISU Scale of Values (SOV) 2024
- ISU Guidelines for Program Components

### الأوراق البحثية:
- Human Pose Estimation using MediaPipe
- Action Recognition in Sports Videos
- Sequential Movement Classification

---

## 👥 المساهمة - Contributing

### كيفية تحسين النموذج:

1. **جمع بيانات تدريب:**
   - قم بتسمية الفيديوهات بشكل صحيح
   - أضف بيانات الوضعيات والتصنيفات

2. **إضافة ميزات جديدة:**
   - استخرج خصائص إضافية
   - جرب خوارزميات تصنيف مختلفة

3. **تحسين الدقة:**
   - اختبر على مجموعات بيانات متنوعة
   - ضبط المعاملات والعتبات

---

## 📞 الدعم - Support

للأسئلة والمشاكل التقنية:
- راجع ملفات التوثيق الأخرى
- تحقق من الأمثلة في `examples/`
- ارفع issue على GitHub

---

**آخر تحديث:** 2025-11-19
**الإصدار:** 3.0.0 - AI System Integrated

═══════════════════════════════════════════════════════════
✨ **نظام ذكاء اصطناعي متقدم للتعرف على حركات التزلج الفني**
═══════════════════════════════════════════════════════════
