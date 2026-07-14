# 📘 دليل المستخدم الشامل
# Complete User Guide

**نظام تحليل أداء لاعبي التزلج على الجليد**  
**Figure Skating Analysis System**

**النسخة:** 2.0.0  
**التاريخ:** 2026-04-03  
**اللغة:** العربية / English

---

## 📑 جدول المحتويات

### القسم الأول: البداية
1. [مرحباً بك](#مرحباً-بك)
2. [متطلبات النظام](#متطلبات-النظام)
3. [التثبيت](#التثبيت)
4. [التشغيل الأول](#التشغيل-الأول)

### القسم الثاني: الميزات الأساسية
5. [لوحة التحكم](#لوحة-التحكم)
6. [إدارة الأعضاء](#إدارة-الأعضاء)
7. [تسجيل الحضور](#تسجيل-الحضور)
8. [التقارير](#التقارير)

### القسم الثالث: الميزات المتقدمة
9. [نظام المستويات والشارات](#نظام-المستويات-والشارات)
10. [الإشعارات التلقائية](#الإشعارات-التلقائية)
11. [مقارنة الأداء](#مقارنة-الأداء)
12. [تحليل الفيديو](#تحليل-الفيديو)

### القسم الرابع: الإدارة
13. [إعدادات النظام](#إعدادات-النظام)
14. [النسخ الاحتياطي](#النسخ-الاحتياطي)
15. [استكشاف الأخطاء](#استكشاف-الأخطاء)

### القسم الخامس: API والتكامل
16. [استخدام API](#استخدام-api)
17. [التكامل مع أنظمة أخرى](#التكامل)

---

## 🎯 مرحباً بك

### ما هو هذا النظام؟

**نظام تحليل أداء لاعبي التزلج** هو نظام شامل ومتكامل لإدارة وتحليل أداء لاعبي التزلج على الجليد. يوفر النظام:

✅ **إدارة شاملة** - للأعضاء والحضور والعضويات  
✅ **تحليل متقدم** - للأداء والتقدم  
✅ **تقارير احترافية** - PDF جاهز للطباعة  
✅ **نظام تحفيزي** - مستويات وشارات  
✅ **إشعارات ذكية** - تذكير تلقائي  
✅ **مقارنات تفصيلية** - بين اللاعبين  

### لمن هذا النظام؟

- 🏫 **المدارس والأكاديميات** - لإدارة الطلاب
- 👨‍🏫 **المدربين** - لمتابعة الأداء
- 🏆 **النوادي الرياضية** - للتنظيم والإدارة
- 📊 **الإداريين** - للتقارير والإحصائيات
- 👤 **اللاعبين** - لمتابعة التقدم الشخصي

---

## 💻 متطلبات النظام

### الحد الأدنى

```
المعالج: Intel Core i3 أو معادل
الذاكرة: 4 GB RAM
المساحة: 2 GB فارغة
نظام التشغيل: Windows 10/11, macOS 10.14+, Linux
Python: 3.10 أو أحدث
المتصفح: Chrome, Firefox, Safari, Edge (حديث)
```

### الموصى به

```
المعالج: Intel Core i5 أو أفضل
الذاكرة: 8 GB RAM
المساحة: 5 GB فارغة
SSD: لأداء أفضل
الإنترنت: لتحميل المكتبات والتحديثات
```

---

## 🔧 التثبيت

### الطريقة 1: التثبيت السريع (موصى بها)

#### Windows:

```batch
# 1. افتح Command Prompt أو PowerShell

# 2. استنسخ المشروع
git clone https://github.com/elmansoory/yasooo.git
cd yasooo

# 3. انتقل للفرع المناسب
git checkout claude/skating-analysis-system-019JhsA9HHwcSgQ6oXnujCjf

# 4. ثبت المكتبات
pip install -r requirements.txt

# 5. شغّل النظام
streamlit run modern_app.py
```

#### macOS/Linux:

```bash
# 1. افتح Terminal

# 2. استنسخ المشروع
git clone https://github.com/elmansoory/yasooo.git
cd yasooo

# 3. انتقل للفرع المناسب
git checkout claude/skating-analysis-system-019JhsA9HHwcSgQ6oXnujCjf

# 4. ثبت المكتبات
pip3 install -r requirements.txt

# 5. شغّل النظام
streamlit run modern_app.py
```

### الطريقة 2: البيئة الافتراضية (مستحسنة)

```bash
# 1. إنشاء بيئة افتراضية
python -m venv venv

# 2. تفعيل البيئة
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 3. تثبيت المكتبات
pip install -r requirements.txt

# 4. تشغيل النظام
streamlit run modern_app.py
```

### التحقق من التثبيت

```bash
# تشغيل الاختبار الشامل
python test_system.py
```

يجب أن تحصل على:
```
✅ PASSED: 73
❌ FAILED: 0
📈 OVERALL SCORE: 100.0%
🎉 EXCELLENT! System is in great shape!
```

---

## 🚀 التشغيل الأول

### 1. تشغيل النظام

```bash
streamlit run modern_app.py
```

سيفتح النظام تلقائياً في المتصفح على:
```
http://localhost:8501
```

### 2. الواجهة الرئيسية

عند فتح النظام، ستجد:

#### القائمة الجانبية (Sidebar):
- 🏠 **الرئيسية** - لوحة التحكم
- 👤 **ملفات الأعضاء** - بيانات الأعضاء
- 📊 **التقارير** - التقارير والإحصائيات
- ⚙️ **الإعدادات** - إعدادات النظام

#### الصفحة الرئيسية تعرض:
- 📊 **بطاقات إحصائية** - إجمالي الأعضاء، الحضور، المتوسطات
- 📈 **رسوم بيانية** - تطور الحضور، التوزيعات
- 🏆 **أفضل 10** - أعلى الأعضاء حضوراً

---

## 📊 لوحة التحكم

### البطاقات الإحصائية

#### 1. إجمالي الأعضاء
- يعرض عدد الأعضاء المسجلين
- التغيير عن الفترة السابقة

#### 2. سجلات الحضور
- إجمالي أيام الحضور المسجلة
- عدد السجلات في قاعدة البيانات

#### 3. متوسط الحضور
- متوسط أيام الحضور لكل عضو
- مؤشر الانتظام

#### 4. أيام التدريب
- عدد الأيام الفريدة للتدريب
- الفترة الزمنية

### التبويبات (Tabs)

#### 📈 التحليلات
- رسم بياني لتطور الحضور عبر الزمن
- Area Chart تفاعلي
- إمكانية التكبير والتحريك

#### 🏆 الأفضل أداءً
- Bar Chart لأفضل 10 أعضاء
- ترتيب حسب الحضور
- ألوان تفاعلية

#### 👥 التوزيعات
- **توزيع الجنس**: Pie Chart
- **توزيع الأعمار**: Histogram

#### ⚙️ النظام
- إحصائيات الأداء
- Cache statistics
- معلومات قاعدة البيانات

---

## 👥 إدارة الأعضاء

### عرض ملفات الأعضاء

#### 1. البحث والفلترة

```
🔍 البحث: اكتب اسم العضو
🎭 الجنس: [الكل | ذكر | أنثى]
```

#### 2. معلومات العضو

**البطاقة الأساسية:**
- الاسم الكامل
- الجنس
- العمر (محسوب تلقائياً)
- إجمالي الحضور

**إحصائيات الحضور:**
- عدد أيام الحضور
- آخر حضور
- نسبة الحضور (%)
- السلسلة الحالية (Streak)

**الرسم البياني:**
- الحضور الشهري
- Line Chart تفاعلي

### إضافة عضو جديد

```python
# من لوحة الإدارة
1. اضغط "إضافة عضو جديد"
2. املأ البيانات:
   - الاسم *
   - الجنس *
   - تاريخ الميلاد
   - البريد الإلكتروني
   - رقم الهاتف
3. احفظ
```

### تعديل بيانات عضو

```python
1. ابحث عن العضو
2. اضغط "تعديل"
3. عدّل البيانات
4. احفظ
```

---

## 📝 تسجيل الحضور

### الطريقة 1: تسجيل يدوي

```python
1. صفحة الحضور
2. اختر التاريخ
3. اختر الأعضاء
4. اضغط "تسجيل الحضور"
```

### الطريقة 2: استيراد من Excel

```python
1. صفحة الحضور
2. "استيراد من Excel"
3. اختر الملف
4. تأكيد البيانات
5. استيراد
```

**تنسيق ملف Excel:**
```
| member_id | date       |
|-----------|------------|
| 1         | 2025-01-15 |
| 2         | 2025-01-15 |
```

### الطريقة 3: مسح QR Code (قريباً)

---

## 📄 التقارير

### أنواع التقارير

#### 1. تقرير عضو فردي

```python
from src.utils.pdf_generator import generate_member_pdf

generate_member_pdf(
    member_data={'name': 'محمد أحمد', 'id': 1, 'gender': 'ذكر'},
    attendance_data=attendance_df,
    output_path='reports/member_1.pdf'
)
```

**يتضمن:**
- معلومات شخصية
- إحصائيات الحضور
- رسم بياني شهري
- سجل الحضور الكامل

#### 2. تقرير النظام الشامل

```python
from src.utils.pdf_generator import generate_system_pdf

generate_system_pdf(
    members_df=members_df,
    attendance_df=attendance_df,
    memberships_df=memberships_df,
    output_path='reports/system_report.pdf'
)
```

**يتضمن:**
- نظرة عامة
- إحصائيات شاملة
- أفضل 20 عضو
- توزيعات
- إحصائيات شهرية

### تصدير البيانات

#### Excel
```python
members_df.to_excel('exports/members.xlsx', index=False)
attendance_df.to_excel('exports/attendance.xlsx', index=False)
```

#### CSV
```python
members_df.to_csv('exports/members.csv', index=False)
attendance_df.to_csv('exports/attendance.csv', index=False)
```

---

## 🏆 نظام المستويات والشارات

### المستويات السبعة

#### 1. 🌱 مبتدئ (Beginner)
```
المتطلبات: 0
الوصف: بداية الرحلة
```

#### 2. 📚 ابتدائي (Elementary)
```
الحضور: 10 أيام
النقاط: 100
الأيام: 30
الشارات: first_week
الوصف: تعلم الأساسيات
```

#### 3. 🎯 متوسط (Intermediate)
```
الحضور: 30 يوم
النقاط: 500
الأيام: 90
الشارات: first_week, consistent_10
الوصف: إتقان الأساسيات
```

#### 4. 🚀 متقدم (Advanced)
```
الحضور: 60 يوم
النقاط: 1500
الأيام: 180
الشارات: first_week, consistent_10, consistent_30
الوصف: مهارات احترافية
```

#### 5. 💎 خبير (Expert)
```
الحضور: 120 يوم
النقاط: 3000
الأيام: 365
الشارات: first_week, consistent_30, perfect_month
الوصف: احتراف عالي
```

#### 6. 👔 محترف (Professional)
```
الحضور: 200 يوم
النقاط: 5000
الأيام: 540
الشارات: first_week, consistent_30, perfect_month, year_warrior
الوصف: مستوى عالمي
```

#### 7. 👑 نخبة (Elite)
```
الحضور: 365 يوم
النقاط: 10000
الأيام: 730
الشارات: first_week, perfect_month, year_warrior, legend
الوصف: قمة الاحتراف
```

### نظام النقاط

```
💰 الحصول على النقاط:
- 10 نقاط لكل يوم حضور
- نقاط الشارات (10-2000 نقطة)
- نقاط الإنجازات الخاصة

📊 استخدام النقاط:
- تحديد المستوى
- الترتيب في لوحة الصدارة
- مقارنة الأداء
```

### الشارات (15+)

#### شارات الحضور:
- 🎉 **اليوم الأول** (10 نقاط) - حضور أول يوم
- 🌟 **الأسبوع الأول** (50 نقاط) - 7 أيام
- 💪 **المثابر** (100 نقطة) - 10 أيام متتالية
- 🔥 **الملتزم** (300 نقطة) - 30 يوم متتالي
- 🏆 **الشهر الكامل** (500 نقطة) - حضور كامل شهر
- ⚔️ **محارب السنة** (1000 نقطة) - 200+ يوم في سنة
- 👑 **الأسطورة** (2000 نقطة) - 365+ يوم

#### شارات الأداء:
- 🦘 **القفزة الأولى** (50 نقطة)
- 🌀 **الدوران المثالي** (150 نقطة)
- 🎯 **سيد الكومبو** (300 نقطة)

#### شارات خاصة:
- 🐦 **الطائر المبكر** (200 نقطة) - حضور صباحي
- 🦉 **بومة الليل** (200 نقطة) - تدريب مسائي
- 🤝 **روح الفريق** (250 نقطة) - تدريبات جماعية

### التحقق من التقدم

```python
from src.models.progression_system import ProgressionSystem

system = ProgressionSystem()
summary = system.get_player_summary(member_id, attendance_df)

print(f"المستوى: {summary['level_name']}")
print(f"النقاط: {summary['points']}")
print(f"الشارات: {summary['badges_count']}")
print(f"التقدم: {summary['progress_to_next']['progress']}%")
```

---

## 🔔 الإشعارات التلقائية

### أنواع الإشعارات

#### 1. ⏰ تذكير بالحضور
```
الوقت: قبل ساعة من التدريب
الرسالة: "مرحباً {name}! لديك تدريب اليوم الساعة {time}"
القنوات: Email, App
```

#### 2. 📅 تذكير بالتدريب
```
الوقت: يوم قبل التدريب
الرسالة: "لديك تدريب غداً الساعة {time}. استعد جيداً!"
القنوات: Email, SMS
```

#### 3. ⚠️ تنبيه غياب
```
الشرط: غياب 7+ أيام
الرسالة: "لاحظنا غيابك لمدة {days} أيام"
القنوات: Email, SMS, App
```

#### 4. 🏆 إنجاز جديد
```
الوقت: فوري عند الحصول على شارة
الرسالة: "مبروك! حصلت على شارة {badge_name}!"
القنوات: Email, App, Push
```

#### 5. ⭐ ترقية مستوى
```
الوقت: فوري عند الترقية
الرسالة: "رائع! ارتقيت إلى مستوى {level_name}!"
القنوات: Email, App, Push
```

#### 6. 🎂 عيد ميلاد
```
الوقت: يوم عيد الميلاد
الرسالة: "كل سنة وأنت طيب!"
القنوات: Email, App
```

### إعداد الإشعارات

```python
from src.utils.notification_system import NotificationManager, NotificationScheduler

# إنشاء مدير
manager = NotificationManager()

# جدولة تلقائية
scheduler = NotificationScheduler(manager)

# تفعيل الإشعارات
scheduler.schedule_attendance_reminders(members_df, training_times)
scheduler.check_absence_alerts(members_df, attendance_df, threshold=7)
scheduler.check_birthdays(members_df)
```

### تخصيص القوالب

```python
# تعديل قالب إشعار
manager.templates[NotificationType.ATTENDANCE_REMINDER] = {
    'title': 'تذكير مخصص',
    'message': 'رسالة مخصصة {name}!'
}
```

---

## 📊 مقارنة الأداء

### لوحة الصدارة (Leaderboard)

```python
from src.utils.performance_comparison import PerformanceComparator

comparator = PerformanceComparator()

# أفضل 10
leaderboard = comparator.create_leaderboard(
    members_df,
    attendance_df,
    top_n=10
)

print(leaderboard)
```

**النتيجة:**
```
الترتيب | الاسم      | النقاط | المستوى | الحضور | معدل الحضور
--------|-----------|--------|---------|--------|------------
1       | محمد      | 1500   | متقدم   | 150    | 95.5%
2       | أحمد      | 1200   | متوسط   | 120    | 88.2%
...
```

### مقارنة بين لاعبين

```python
# مقارنة بين 3 لاعبين
comparison = comparator.compare_players(
    player_ids=[1, 2, 3],
    members_df=members_df,
    attendance_df=attendance_df
)

# عرض النتائج
for player in comparison['players']:
    print(f"{player.name}: {player.points} نقطة (#{player.rank})")

# الرؤى التلقائية
for insight in comparison['insights']:
    print(f"- {insight}")
```

### الرسوم البيانية

```python
# إنشاء رسوم المقارنة
charts = comparator.create_comparison_charts(comparison['players'])

# عرض في Streamlit
import streamlit as st
st.plotly_chart(charts['points'])      # مقارنة النقاط
st.plotly_chart(charts['attendance']) # مقارنة الحضور  
st.plotly_chart(charts['radar'])      # مقارنة شاملة
st.plotly_chart(charts['attendance_rate'])  # معدل الحضور
```

### تحليل نقاط القوة/الضعف

```python
analysis = comparator.analyze_strengths_weaknesses(
    player_id=1,
    members_df=members_df,
    attendance_df=attendance_df
)

print(f"اللاعب: {analysis['player_name']}")
print(f"النتيجة الإجمالية: {analysis['overall_score']}/100")

print("\nنقاط القوة:")
for strength in analysis['strengths']:
    print(f"{strength['icon']} {strength['description']}")

print("\nنقاط الضعف:")
for weakness in analysis['weaknesses']:
    print(f"{weakness['icon']} {weakness['description']}")

print("\nاقتراحات:")
for suggestion in analysis['suggestions']:
    print(f"- {suggestion}")
```

---

**يتبع في الجزء الثاني...**

---

**🎿 نظام تحليل أداء لاعبي التزلج - دليل المستخدم**  
**النسخة 2.0.0 - صُنع بـ ❤️ في مصر 🇪🇬**
