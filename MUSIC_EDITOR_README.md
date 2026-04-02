# 🎵 Music Editor & Merger - دليل محرر الموسيقى

## نظرة عامة - Overview

محرر موسيقى احترافي مصمم خصيصاً لبرامج التزلج الفني مع الالتزام بمعايير ISU.

Professional music editor designed specifically for figure skating programs with ISU compliance.

---

## ✨ المميزات - Features

### 1. **إدارة الملفات الصوتية** 📁
- رفع ملفات متعددة (MP3, WAV, FLAC, M4A, OGG)
- معاينة الملفات قبل الاستخدام
- عرض معلومات تفصيلية (المدة، جودة الصوت، إلخ)

### 2. **قص ودمج المقاطع** ✂️
- قص أي جزء من الأغنية
- دمج مقاطع متعددة بسلاسة
- Crossfade بين المقاطع
- ترتيب المقاطع بسهولة (Drag & Drop)

### 3. **المؤثرات الصوتية** 🎨
- **Fade In/Out** - تلاشي في البداية والنهاية
- **Volume Control** - التحكم في مستوى الصوت لكل مقطع
- **Normalization** - توحيد مستويات الصوت
- **Dynamic Range Compression** - ضغط النطاق الديناميكي

### 4. **كشف الإيقاع** 🥁
- كشف تلقائي للإيقاع (BPM)
- تحديد مواقع النبضات
- مزامنة الموسيقى مع الحركات

### 5. **الالتزام بمعايير ISU** ⏱️
- حدود زمنية تلقائية حسب الفئة:
  - **Short Program**:
    - Senior Men/Ladies: 2:50 (170s)
    - Junior: 2:30 (150s)
  - **Free Skate**:
    - Senior Men: 4:30 (270s)
    - Senior Ladies: 4:00 (240s)
    - Junior: 3:30 (210s)
- تنبيهات عند تجاوز الحد الزمني
- عداد مدة البرنامج الحالية

### 6. **خط زمني مرئي** 📊
- عرض مرئي للمقاطع المدمجة
- ترتيب سهل للمقاطع
- مؤشر حد ISU الزمني

---

## 📦 التثبيت - Installation

### المتطلبات الأساسية:

```bash
# Install pydub (required)
pip install pydub

# Install librosa for beat detection (optional but recommended)
pip install librosa soundfile

# Or install all at once
pip install -r requirements-audio.txt
```

### FFmpeg (مطلوب):

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Windows:**
- Download from: https://ffmpeg.org/download.html
- Add to PATH environment variable

---

## 🚀 الاستخدام - Usage

### 1. تشغيل التطبيق:

```bash
python -m streamlit run professional_app.py
```

### 2. من القائمة الجانبية اختر:
**🎵 Music Editor & Merger**

### 3. رفع الملفات الصوتية:

1. اذهب إلى تبويب **"📁 Upload & Manage"**
2. اسحب وأفلت ملفات MP3 أو اضغط لاختيار الملفات
3. انتظر التحميل والمعاينة

### 4. إنشاء المقاطع:

1. اذهب إلى تبويب **"✂️ Add Clips"**
2. اختر ملف صوتي
3. حدد وقت البداية والنهاية
4. أضف المؤثرات (fade, volume)
5. اضغط **"➕ Add Clip to Timeline"**

### 5. ترتيب الخط الزمني:

1. اذهب إلى تبويب **"🎬 Timeline"**
2. رتب المقاطع (⬆️ ⬇️)
3. احذف المقاطع غير المرغوبة (🗑️)
4. راقب المدة الكلية

### 6. التصدير:

1. اذهب إلى تبويب **"🎵 Preview & Export"**
2. اختر إعدادات الدمج (crossfade, normalize)
3. اضغط **"🎵 Create Program Music"**
4. معاينة النتيجة
5. تحميل الملف النهائي

---

## 💡 أمثلة - Examples

### مثال 1: برنامج قصير بسيط

```python
from src.utils.audio_processor import AudioProcessor, AudioClip, ProgramMusic

# Initialize processor
processor = AudioProcessor()

# Create clips
clips = [
    AudioClip(
        filepath='intro_song.mp3',
        start_time=0.0,
        end_time=50.0,
        duration=50.0,
        fade_in=2.0,
        fade_out=1.0,
        name='Opening'
    ),
    AudioClip(
        filepath='dramatic_song.mp3',
        start_time=30.0,
        end_time=90.0,
        duration=60.0,
        fade_in=1.0,
        fade_out=1.0,
        name='Middle'
    ),
    AudioClip(
        filepath='finale_song.mp3',
        start_time=10.0,
        end_time=70.0,
        duration=60.0,
        fade_in=1.0,
        fade_out=3.0,
        name='Finale'
    ),
]

# Create program
program = ProgramMusic(
    program_type='short',
    target_duration=170,  # 2:50
    clips=clips
)

# Export
output = processor.create_program_music(
    program,
    'my_short_program.mp3',
    normalize=True
)
```

### مثال 2: كشف الإيقاع

```python
from src.utils.audio_processor import AudioProcessor

processor = AudioProcessor()

# Detect beats
beats = processor.detect_beats('my_song.mp3')

print(f"Tempo: {tempo} BPM")
print(f"Beat times: {beats[:10]}")
```

---

## 🎯 نصائح احترافية - Pro Tips

### 1. **اختيار الموسيقى:**
- ✅ اختر أغاني عالية الجودة (320kbps+)
- ✅ تأكد من توافق الموسيقى مع أسلوب البرنامج
- ✅ راعِ التنوع (هادئ، درامي، سريع)

### 2. **القص والدمج:**
- ✅ استخدم Fade In/Out لانتقالات سلسة
- ✅ اختر نقاط القطع على النبضات الموسيقية
- ✅ استخدم Crossfade للانتقال الطبيعي

### 3. **معايير ISU:**
- ✅ اترك مجال 5-10 ثوان أقل من الحد الأقصى
- ✅ تأكد من بداية ونهاية واضحة
- ✅ تجنب التوقف المفاجئ للموسيقى

### 4. **جودة الصوت:**
- ✅ استخدم Normalize لتوحيد مستويات الصوت
- ✅ تجنب التضخيم الزائد (clipping)
- ✅ صدر بجودة عالية (320kbps MP3)

### 5. **التخطيط:**
- 💡 خطط البرنامج قبل إنشاء الموسيقى
- 💡 حدد مواقع العناصر الرئيسية
- 💡 اجعل الذروات الموسيقية تتزامن مع العناصر الصعبة
- 💡 احفظ التكوين للتعديلات المستقبلية

---

## 📋 الأسئلة الشائعة - FAQ

### Q1: ما هي الصيغ المدعومة؟
**A:** MP3, WAV, FLAC, M4A, OGG, WMA

### Q2: هل يمكن استخدام أغاني من YouTube؟
**A:** نعم، استخدم Video Downloader في التطبيق أولاً لتحميل الصوت.

### Q3: كيف أعرف BPM الموسيقى؟
**A:** استخدم ميزة Beat Detection في تبويب Upload.

### Q4: هل يمكن حفظ المشروع والعودة له؟
**A:** نعم، استخدم "💾 Save Config" في الشريط الجانبي.

### Q5: ما هو Crossfade المناسب؟
**A:** عادة 0.5-2 ثانية للانتقالات السلسة.

### Q6: كيف أتعامل مع الموسيقى الطويلة؟
**A:** استخدم القص لاختيار الأجزاء الأفضل فقط.

---

## 🔧 استكشاف الأخطاء - Troubleshooting

### خطأ: "pydub not available"
**الحل:**
```bash
pip install pydub
```

### خطأ: "FFmpeg not found"
**الحل:**
- تأكد من تثبيت FFmpeg
- أضف FFmpeg إلى PATH

### خطأ: "Could not read audio file"
**الحل:**
- تأكد من صيغة الملف مدعومة
- تحقق من سلامة الملف
- جرب تحويل الملف إلى MP3

### البرنامج يتجاوز الحد الزمني:
**الحل:**
- قلل مدة المقاطع
- احذف مقاطع غير ضرورية
- اضبط أوقات البداية والنهاية

---

## 📚 موارد إضافية - Resources

### معايير ISU الرسمية:
- https://www.isu.org/figure-skating/rules

### أدوات الموسيقى:
- **Audacity** - محرر صوت مجاني
- **Beat Finder** - كشف BPM
- **Music Speed Changer** - تغيير السرعة

---

## 🤝 المساهمة - Contributing

لديك أفكار لتحسين محرر الموسيقى؟

1. Fork المشروع
2. أنشئ فرع للميزة الجديدة
3. Commit التغييرات
4. Push إلى الفرع
5. افتح Pull Request

---

## 📄 الترخيص - License

[Project License]

---

## 📞 الدعم - Support

- **GitHub Issues:** [Report a bug](https://github.com/elmansoory/yasooo/issues)
- **Documentation:** Check CLAUDE.md and README.md

---

## 🎵 مثال عملي - Practical Example

### برنامج حر لسيدات (4:00 دقائق):

```
🎵 Opening (0:00 - 0:50) - موسيقى هادئة
   ├─ Fade In: 2s
   ├─ Volume: 0dB
   └─ Elements: Entry, Spin

🎵 Build-up (0:50 - 1:50) - موسيقى متصاعدة
   ├─ Crossfade: 1s
   ├─ Volume: +2dB
   └─ Elements: Jump sequence

🎵 Peak (1:50 - 2:50) - ذروة درامية
   ├─ Crossfade: 1s
   ├─ Volume: +3dB
   └─ Elements: Triple jumps, Step sequence

🎵 Finale (2:50 - 4:00) - نهاية قوية
   ├─ Crossfade: 1s
   ├─ Fade Out: 3s
   └─ Elements: Final spin, Ending pose
```

**Total: 4:00 (240 seconds) ✅**

---

**حظاً موفقاً في إنشاء برامجك الموسيقية! 🎵⛸️**
