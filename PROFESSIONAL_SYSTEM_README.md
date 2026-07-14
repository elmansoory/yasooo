# 🏅 **نظام تحليل احترافي للتزلج - Professional Figure Skating Analysis System**

## **نظام متقدم لتحليل أداء لاعبي التزلج مع إمكانيات تقترب من مستوى الحكام**

---

## 🎯 **نظرة عامة**

هذا النظام الاحترافي مصمم لتحليل أداء لاعبي التزلج الفني باستخدام:
- ✅ **MediaPipe Pose Detection** - كشف دقيق للوضعيات 3D
- ✅ **Jump Detection & Classification** - كشف وتصنيف القفزات تلقائياً
- ✅ **Dataset Management** - إدارة قاعدة بيانات تدريب احترافية
- ✅ **ML Training Pipeline** - تدريب نماذج تصنيف العناصر
- ✅ **Referee Testing Interface** - واجهة اختبار للمدربين والحكام

---

## 📦 **المكونات الرئيسية**

### 1️⃣ **Advanced Pose Detection** 🎥
**الملف:** `src/core/advanced_pose_detector.py`

**الميزات:**
- كشف 33 نقطة مرجعية للجسم (landmarks)
- تتبع 3D coordinates مع depth information
- World landmarks (إحداثيات حقيقية بالمتر)
- حساب center of mass تلقائياً
- كشف airborne segments (إطارات في الهواء)
- حساب body angle والدوران
- استخراج pose data كـ JSON

**الاستخدام:**
```python
from src.core.advanced_pose_detector import AdvancedPoseDetector

detector = AdvancedPoseDetector(
    model_complexity=2,  # أعلى دقة
    min_detection_confidence=0.7
)

# تحليل فيديو
pose_frames = detector.process_video(
    "program.mp4",
    save_visualization=True,
    output_path="annotated.mp4"
)

# حفظ البيانات
detector.export_to_json(pose_frames, "pose_data.json")
```

---

### 2️⃣ **Jump Detection System** 🦘
**الملف:** `src/analysis/jump_detector.py`

**الميزات:**
- كشف القفزات تلقائياً من airborne segments
- قياس ارتفاع القفزة (بالسم)
- قياس مسافة القفزة (بالمتر)
- عد الدورات (rotation counting)
- حساب سرعة الدوران (RPM)
- تقدير GOE تلقائياً (-5 to +5)
- كشف الأخطاء (under-rotation, landing issues)
- تحليل زوايا الإقلاع والهبوط

**النتائج:**
```python
{
    'isu_code': '3A',           # Triple Axel
    'rotations': 3.5,
    'height_cm': 45.2,
    'airtime': 0.72,
    'rotation_speed': 180,      # RPM
    'estimated_goe': +2,
    'is_clean': True,
    'errors': [],
    'warnings': []
}
```

**الاستخدام:**
```python
from src.analysis.jump_detector import JumpDetector

detector = JumpDetector(fps=30)
jumps = detector.detect_jumps(pose_frames)

for jump in jumps:
    print(f"{jump.get_isu_code()}: {jump.height_cm:.1f}cm, GOE: {jump.estimated_goe:+d}")
```

---

### 3️⃣ **Dataset Management** 📚
**الملف:** `src/utils/dataset_manager.py`

**الميزات:**
- إضافة وإدارة فيديوهات التدريب
- تعليق يدوي دقيق على العناصر (annotation)
- تخزين Ground Truth من الحكام الحقيقيين
- إنشاء train/test splits
- تصدير إلى DataFrame/CSV
- إحصائيات شاملة

**البنية:**
```
data/skating_dataset/
├── videos/                     # الفيديوهات
├── annotations/                # التعليقات (JSON)
├── features/                   # الخصائص المستخرجة
├── splits/                     # train/test splits
└── index.json                  # فهرس Dataset
```

**الاستخدام:**
```python
from src.utils.dataset_manager import DatasetManager, AnnotationTool

# Create dataset
dm = DatasetManager("data/skating_dataset")

# Add video
video_id = dm.add_video("hanyu_2018_olympics.mp4")

# Annotate elements
tool = AnnotationTool(dm)
tool.load_video(video_id)

tool.annotate_element(
    element_type="jump",
    isu_code="4Lo",
    start_frame=120,
    end_frame=150,
    base_value=10.5,
    goe=+3,
    annotator_name="ISU Judge"
)

# Create train/test split
dm.create_train_test_split(test_ratio=0.2)

# Export
df = dm.export_to_dataframe()
```

---

### 4️⃣ **ML Training Pipeline** 🤖
**الملف:** `src/models/element_classifier_trainer.py`

**الميزات:**
- تدريب نماذج تصنيف العناصر (jumps, spins, steps)
- دعم Multiple models:
  - Random Forest
  - Gradient Boosting
  - SVM
  - Neural Networks
- Feature engineering تلقائي
- Cross-validation
- Feature importance analysis
- حفظ وتحميل النماذج

**الاستخدام:**
```python
from src.models.element_classifier_trainer import (
    ElementClassifierTrainer,
    TrainingConfig
)

# Configure training
config = TrainingConfig(
    model_type="random_forest",
    n_estimators=100,
    verbose=True
)

# Create trainer
trainer = ElementClassifierTrainer(config)

# Prepare data
X_train, y_train, feature_names = trainer.prepare_dataset(train_df)
X_test, y_test, _ = trainer.prepare_dataset(test_df)

# Train
results = trainer.train(X_train, y_train, X_test, y_test)

# Save model
trainer.save_model("models/element_classifier")

# Predict
predicted, confidence = trainer.predict(features)
```

**Feature Engineering:**
```
Features:
├── duration (seconds)
├── frame_count
├── element_type_encoded (jump/spin/step)
├── rotations (for jumps)
├── level (for spins/steps 1-4)
├── base_value
└── goe
```

---

### 5️⃣ **Referee Testing Interface** 👨‍⚖️
**الملف:** `src/pages/referee_testing_interface.py`

**الميزات:**
- واجهة Streamlit احترافية
- 3 أوضاع:
  - 🎥 **تحليل فيديو جديد** - تحليل كامل
  - 📊 **مراجعة نتائج** - مراجعة التحليلات السابقة
  - 📝 **تعليق يدوي** - إضافة Ground Truth

**وضع التحليل:**
- تفعيل/تعطيل المكونات (Pose, Jumps, ML)
- تحليل الفيديو مع progress bar
- عرض نتائج مفصلة
- مقارنة مع التقييم اليدوي

**وضع المقارنة:**
- النظام الآلي vs الحكم البشري
- حساب الفرق (difference)
- تقييم الدقة

**التشغيل:**
```bash
streamlit run src/pages/referee_testing_interface.py
```

---

## 🚀 **التثبيت والإعداد**

### المتطلبات:
```bash
pip install mediapipe opencv-python numpy pandas scikit-learn joblib streamlit plotly
```

### التثبيت الكامل:
```bash
# 1. Clone repository
git clone https://github.com/elmansoory/yasooo.git
cd yasooo

# 2. Install dependencies
pip install -r requirements_professional.txt

# 3. Create directories
mkdir -p data/skating_dataset/{videos,annotations,features,splits}
mkdir -p models
mkdir -p temp
```

---

## 📊 **سير العمل (Workflow)**

### **المرحلة 1: جمع البيانات** 📥
```python
from src.utils.dataset_manager import DatasetManager

dm = DatasetManager("data/skating_dataset")

# Add 100-500 videos with manual annotations
for video_file in video_files:
    video_id = dm.add_video(video_file)
    # Manual annotation by coaches/judges
```

### **المرحلة 2: التعليق اليدوي** ✍️
```python
from src.utils.dataset_manager import AnnotationTool

tool = AnnotationTool(dm)

# For each video:
tool.load_video(video_id)

# Annotate each element with ISU code, GOE, etc.
tool.annotate_element(...)
```

### **المرحلة 3: تدريب النموذج** 🎓
```python
from src.models.element_classifier_trainer import train_element_classifier

# Train on annotated dataset
trainer, results = train_element_classifier()

print(f"Accuracy: {results.accuracy_test:.3f}")
```

### **المرحلة 4: الاختبار** 🧪
```bash
# Run referee testing interface
streamlit run src/pages/referee_testing_interface.py

# Upload new video
# Compare AI vs Human scoring
# Measure accuracy
```

---

## 📈 **ما يمكن قياسه الآن**

### ✅ **يعمل جيداً:**
- كشف القفزات (jumps detection)
- كشف الأشخاص في الهواء (airborne detection)
- قياس المدة والإطارات
- عد الدورات (تقريبياً)
- حساب السرعة
- كشف السقوط (falls)

### ⚡ **يعمل بشكل مقبول:**
- تصنيف نوع القفزة (يحتاج تحسين)
- قياس الارتفاع (تقديري - يحتاج calibration)
- تقدير GOE (±1-2)

### 🔴 **يحتاج تطوير إضافي:**
- تصنيف دقيق لأنواع القفزات (Axel vs Lutz vs Flip...)
- تحليل الدورانات (spins) بتفاصيلها
- تحليل تسلسلات الخطوات (step sequences)
- Program Components Scoring
- Real-time processing

---

## 🎯 **الدقة المتوقعة**

### مع Dataset صغير (100-500 videos):
- **Jump Detection:** ~85-90%
- **Rotation Counting:** ~70-80% (±0.25 rotations)
- **GOE Estimation:** ~60-70% (±1 GOE)
- **Element Classification:** ~75-85%

### مع Dataset كبير (1000+ videos):
- **Jump Detection:** ~90-95%
- **Rotation Counting:** ~85-90%
- **GOE Estimation:** ~75-85%
- **Element Classification:** ~85-95%

---

## 📝 **إنشاء Dataset**

### **خطوات بناء Dataset احترافي:**

#### 1. **جمع الفيديوهات (100-500)**
```
المصادر:
├── مسابقات رسمية (Olympics, Worlds, Grand Prix)
├── تدريبات موثقة
├── فيديوهات من نادي التزلج المحلي
└── فيديوهات YouTube (بإذن)
```

#### 2. **التعليق اليدوي**
```
لكل فيديو:
├── معلومات اللاعب (name, country, level)
├── نوع البرنامج (short, free)
├── كل عنصر:
│   ├── ISU Code (3A, 4T, CCoSp4, etc.)
│   ├── Start/End frames
│   ├── Base Value (from ISU)
│   ├── GOE (-5 to +5) من حكم
│   ├── Rotations/Level
│   └── Notes
└── النقاط الإجمالية (Ground Truth)
```

#### 3. **التحقق (Verification)**
```
- 2-3 حكام مستقلين لكل فيديو
- حساب Inter-rater reliability
- حل الخلافات بالنقاش
```

---

## 🔬 **التطوير المستقبلي**

### **المرحلة القادمة:**

#### **1. تحسين Pose Detection**
- استخدام Multi-camera setup
- 3D reconstruction حقيقي
- Foot/skate tracking

#### **2. تحليل الدورانات**
- كشف أنواع الدورانات (Camel, Sit, Upright, Layback)
- حساب RPM دقيق
- تحليل centering/traveling
- تصنيف Level (1-4)

#### **3. تحليل تسلسلات الخطوات**
- كشف الخطوات والدورانات (turns)
- تقييم التنوع (variety)
- تقييم الصعوبة (difficulty)

#### **4. Deep Learning Models**
- CNN for video classification
- LSTM for temporal analysis
- Transformer models for sequences

---

## 📚 **المراجع**

### **ISU Resources:**
- ISU Technical Panels Handbook
- ISU Communication (latest)
- Scale of Values (SOV)

### **Computer Vision:**
- MediaPipe Pose Documentation
- YOLOv8 Documentation
- OpenPose Papers

### **Papers:**
- "Automated Figure Skating Jump Classification" (various)
- "3D Pose Estimation for Sports Analysis"
- "Video-based Action Recognition"

---

## 🏆 **الهدف النهائي**

### **"نظام مساعد للحكام"** وليس بديل كامل

```
الاستخدام المثالي:
┌─────────────────────────────┐
│   1. النظام الآلي           │
│      ↓                       │
│   تحليل أولي (30 ثانية)    │
│      ↓                       │
│   2. الحكم البشري           │
│      ↓                       │
│   مراجعة وتأكيد (2 دقائق)  │
│      ↓                       │
│   3. النتيجة النهائية       │
└─────────────────────────────┘

الفائدة:
✅ توفير 70-80% من الوقت
✅ تقليل الأخطاء البشرية
✅ consistency أعلى
✅ تدريب حكام جدد
```

---

## 💡 **نصائح مهمة**

### للمدربين:
1. ✅ ابدأ بـ dataset صغير (50-100 فيديو)
2. ✅ تأكد من جودة التعليقات اليدوية
3. ✅ استخدم فيديوهات بجودة عالية (1080p+, 60fps+)
4. ✅ اختبر النظام مع حكام حقيقيين

### للمطورين:
1. ✅ ابدأ بكشف القفزات - الأسهل
2. ✅ ثم انتقل للدورانات والخطوات
3. ✅ استخدم Transfer Learning
4. ✅ Data Augmentation مهم جداً

---

## 📞 **الدعم**

- 📧 GitHub Issues: [elmansoory/yasooo/issues](https://github.com/elmansoory/yasooo/issues)
- 📚 Documentation: هذا الملف + كود مُعلّق
- 💬 Discussions: للأسئلة والاقتراحات

---

## 📄 **الترخيص**

MIT License - استخدم بحرية مع الإشارة للمصدر

---

<div align="center">

# 🏅 **نظام احترافي لتحليل التزلج الفني**

**مبني على MediaPipe • OpenCV • Scikit-learn • Streamlit**

**صُنع بـ ❤️ للارتقاء برياضة التزلج في العالم العربي 🇪🇬**

---

⭐ **إذا أعجبك المشروع، لا تنسى Star!** ⭐

[GitHub](https://github.com/elmansoory/yasooo) • [Issues](https://github.com/elmansoory/yasooo/issues) • [Wiki](https://github.com/elmansoory/yasooo/wiki)

</div>
