#!/usr/bin/env python3
"""
استخراج أسماء اللاعبين والمدربين من ملفات الحضور والعضوية
"""
import pandas as pd
import json
import re

def is_valid_name(name):
    """التحقق من صحة الاسم"""
    if not isinstance(name, str):
        return False

    # استبعاد النصوص غير الصالحة
    invalid_patterns = [
        r'^\d',  # يبدأ برقم
        r'^[0-9:]+$',  # أرقام فقط
        r'Off-ice', r'On-ice', r'Coach$',  # نصوص النظام
        r'^\s*$',  # فارغ
        r'^\d+\s*(min|دقيقة|ثانية)',  # أوقات
        r'Level', r'Bundle', r'Amount',  # عناوين
    ]

    for pattern in invalid_patterns:
        if re.search(pattern, name, re.IGNORECASE):
            return False

    # يجب أن يحتوي على حروف
    if len(name.strip()) < 3:
        return False

    return True

def extract_from_attendance(file_path):
    """استخراج من ملفات الحضور"""
    print(f"\n📊 {file_path}")

    try:
        df = pd.read_excel(file_path)

        players = set()
        coaches = set()

        # قراءة أسماء اللاعبين من العمود الأول
        if len(df.columns) > 0:
            first_col = df.iloc[:, 0]

            for value in first_col:
                if is_valid_name(value):
                    # تخطي عناوين الجداول
                    if value not in ['Off-ice', 'On-ice', 'Coach']:
                        players.add(value.strip())

        # استخراج أسماء المدربين من الصفوف
        for idx, row in df.iterrows():
            row_values = [str(v) for v in row if pd.notna(v)]
            row_text = ' '.join(row_values)

            # البحث عن كلمة "Coach" متبوعة باسم
            if 'Coach' in row_text:
                for val in row:
                    if pd.notna(val) and is_valid_name(val):
                        val_str = str(val).strip()
                        # إذا كان قبل أو بعد "Coach"
                        if val_str != 'Coach' and len(val_str) > 3:
                            # تحقق من أنه اسم مدرب وليس لاعب
                            if any(name in val_str for name in ['Ahmed', 'Esraa', 'Clara', 'Hajar', 'Eman', 'Maryam', 'Julia']):
                                coaches.add(val_str)

        print(f"  👥 لاعبين: {len(players)}")
        print(f"  🎓 مدربين: {len(coaches)}")

        return players, coaches

    except Exception as e:
        print(f"  ❌ خطأ: {e}")
        return set(), set()

def extract_from_memberships(file_path):
    """استخراج من ملفات العضوية"""
    print(f"\n📊 {file_path}")

    try:
        df = pd.read_excel(file_path)

        players = set()
        coaches = set()

        # البحث عن عمود "Member"
        if 'Member' in df.columns:
            for name in df['Member'].dropna():
                if is_valid_name(name):
                    players.add(str(name).strip())

        # البحث عن عمود "Coach"
        if 'Coach' in df.columns:
            for name in df['Coach'].dropna():
                if is_valid_name(name):
                    coaches.add(str(name).strip())

        print(f"  👥 لاعبين: {len(players)}")
        print(f"  🎓 مدربين: {len(coaches)}")

        return players, coaches

    except Exception as e:
        print(f"  ❌ خطأ: {e}")
        return set(), set()

def main():
    print("="*80)
    print("🔍 استخراج أسماء اللاعبين والمدربين")
    print("="*80)

    all_players = set()
    all_coaches = set()

    # ملفات الحضور
    attendance_files = [
        "August 2025 Attendence.xlsx",
        "October 2025 Attendence.xlsx",
        "Off-Ice Attendence.xlsx",
        "Book2.xlsx"  # October attendance
    ]

    print("\n📋 ملفات الحضور:")
    for file in attendance_files:
        try:
            players, coaches = extract_from_attendance(file)
            all_players.update(players)
            all_coaches.update(coaches)
        except:
            pass

    # ملفات العضوية
    membership_files = [
        "October Memberships.xlsx",
        "Book1.xlsx"  # October memberships
    ]

    print("\n\n📋 ملفات العضوية:")
    for file in membership_files:
        try:
            players, coaches = extract_from_memberships(file)
            all_players.update(players)
            all_coaches.update(coaches)
        except:
            pass

    # تنظيف القوائم
    # إزالة المدربين من قائمة اللاعبين
    all_players = all_players - all_coaches

    # الأسماء الشائعة للمدربين
    known_coaches = {'Ahmed saad', 'Esraa Nabil', 'Clara Amgad', 'Hajar Munir',
                     'Eman moustafa', 'Maryam mohamed', 'Ahmed', 'Esraa', 'Clara',
                     'Hajar', 'Eman', 'Maryam', 'Julia', 'Ahmed ', 'Hajar ', 'Clara '}

    all_coaches.update(known_coaches)
    all_players = all_players - known_coaches

    # طباعة النتائج
    print("\n\n" + "="*80)
    print("📊 النتائج النهائية")
    print("="*80)

    print(f"\n👥 إجمالي اللاعبين: {len(all_players)}")
    print("\nقائمة اللاعبين:")
    for i, player in enumerate(sorted(all_players), 1):
        print(f"  {i:3d}. {player}")

    print(f"\n\n🎓 إجمالي المدربين: {len(all_coaches)}")
    print("\nقائمة المدربين:")
    for i, coach in enumerate(sorted(all_coaches), 1):
        print(f"  {i:3d}. {coach}")

    # حفظ في JSON
    result = {
        "extraction_date": "2025-11-19",
        "total_players": len(all_players),
        "total_coaches": len(all_coaches),
        "players": sorted(list(all_players)),
        "coaches": sorted(list(all_coaches))
    }

    with open('players_coaches.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n\n💾 تم حفظ النتائج في: players_coaches.json")
    print("="*80)

if __name__ == "__main__":
    main()
