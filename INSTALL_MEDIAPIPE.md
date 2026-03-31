# MediaPipe Installation Guide
# دليل تثبيت MediaPipe

## Problem / المشكلة

If you see this error:
```
module 'mediapipe' has no attribute 'solutions'
```

This means MediaPipe is not installed correctly or the wrong version is installed.

---

## Solution / الحل

### Option 1: Install Specific Version (Recommended)

```bash
pip install mediapipe==0.10.9
```

### Option 2: Reinstall MediaPipe

If you already have MediaPipe installed:

```bash
pip uninstall mediapipe
pip install mediapipe==0.10.9
```

### Option 3: Install All Dependencies

Install everything from requirements.txt:

```bash
pip install -r requirements.txt
```

---

## Verify Installation / التحقق من التثبيت

After installation, verify MediaPipe works:

```python
python -c "import mediapipe as mp; print(mp.__version__); print('MediaPipe OK!')"
```

Expected output:
```
0.10.9
MediaPipe OK!
```

---

## Alternative: Use Basic App / البديل: استخدام التطبيق الأساسي

If you don't need professional pose detection features, use the basic app instead:

```bash
python -m streamlit run app.py
```

The basic app includes:
- ✅ Member management (إدارة الأعضاء)
- ✅ Attendance tracking (تتبع الحضور)
- ✅ Payment management (إدارة المدفوعات)
- ✅ Basic analytics (تحليلات أساسية)
- ✅ Dashboard and reports (لوحة التحكم والتقارير)

---

## Professional Features (Require MediaPipe) / المميزات الاحترافية

These features require MediaPipe to be installed:

- 🎥 Advanced Pose Detection (كشف وضعيات متقدم)
- 🦘 Jump Detection & Analysis (كشف وتحليل القفزات)
- 🌀 Spin Detection & Classification (كشف وتصنيف الدورانات)
- 🤖 ML-based Element Classification (تصنيف العناصر بالذكاء الاصطناعي)
- 🏅 Referee Testing Interface (واجهة اختبار الحكام)
- 📊 Advanced AI Analytics (تحليلات ذكاء اصطناعي متقدمة)

---

## System Requirements / متطلبات النظام

- Python 3.8 or higher
- Windows/Linux/Mac
- At least 4GB RAM (8GB recommended)
- Webcam or video files for analysis

---

## Common Issues / المشاكل الشائعة

### Issue 1: "No module named 'mediapipe'"
**Solution:** Install MediaPipe:
```bash
pip install mediapipe==0.10.9
```

### Issue 2: "module 'mediapipe' has no attribute 'solutions'"
**Solution:** Wrong version installed. Reinstall:
```bash
pip uninstall mediapipe
pip install mediapipe==0.10.9
```

### Issue 3: Installation fails on Windows
**Solution:** Try using Python 3.9 or 3.10 (MediaPipe works best with these versions):
```bash
# Check Python version
python --version

# If needed, download Python 3.10 from python.org
```

### Issue 4: "Cannot import name 'mp'"
**Solution:** Complete reinstall:
```bash
pip uninstall mediapipe opencv-python
pip install opencv-python==4.8.0
pip install mediapipe==0.10.9
```

---

## Quick Start After Installation / البدء السريع بعد التثبيت

### 1. Setup Database (first time only)
```bash
python setup_database.py
```

### 2. Run Professional App
```bash
python -m streamlit run professional_app.py
```

### 3. Or use Quick Start script (Windows)
```bash
QUICK_START.bat
```

---

## Need Help? / تحتاج مساعدة؟

1. Check Python version: `python --version` (should be 3.8+)
2. Check pip version: `pip --version`
3. Try virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```

---

## Contact / التواصل

- GitHub: [elmansoory/yasooo](https://github.com/elmansoory/yasooo)
- Issues: [Report a problem](https://github.com/elmansoory/yasooo/issues)
