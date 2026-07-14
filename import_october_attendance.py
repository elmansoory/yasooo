"""
استيراد بيانات الحضور من ملف October 2025 Attendance
"""
import pandas as pd
from datetime import datetime
from src.database.database_manager import DatabaseManager
from src.database.models import Skater, Attendance


def import_october_attendance():
    """استيراد بيانات حضور شهر أكتوبر"""

    print("="*80)
    print("📥 بدء استيراد بيانات الحضور من October 2025 Attendance.xlsx")
    print("="*80)

    # قراءة الملف
    df = pd.read_excel("October 2025 Attendence.xlsx", header=None)

    # الصف 0: التواريخ
    # الصف 1: نوع الحصة (Off-ice, On-ice, Coach)
    # من الصف 2: البيانات

    # استخراج التواريخ (كل 3 أعمدة)
    dates = []
    for i in range(0, len(df.columns), 3):
        date_val = df.iloc[0, i]
        if pd.notna(date_val) and isinstance(date_val, datetime):
            dates.append({
                'date': date_val,
                'off_ice_col': i,
                'on_ice_col': i + 1,
                'coach_col': i + 2
            })

    print(f"\n📅 تم العثور على {len(dates)} يوم في الملف")
    print(f"من {dates[0]['date'].strftime('%Y-%m-%d')} إلى {dates[-1]['date'].strftime('%Y-%m-%d')}")

    # الاتصال بقاعدة البيانات
    db_manager = DatabaseManager("sqlite:///skating_analysis.db")
    db_manager.init_db()

    with db_manager.get_session() as session:
        # الحصول على جميع الأعضاء من قاعدة البيانات
        all_members = session.query(Skater).all()

        # إنشاء قاموس للبحث السريع
        members_dict = {}
        for member in all_members:
            # تنظيف الاسم
            clean_name = member.name.strip().lower()
            members_dict[clean_name] = member

        print(f"\n👥 تم تحميل {len(members_dict)} عضو من قاعدة البيانات")

        # إحصائيات الاستيراد
        total_records = 0
        matched_members = set()
        unmatched_names = set()

        # معالجة البيانات
        print("\n" + "="*80)
        print("🔄 معالجة البيانات...")
        print("="*80)

        # معالجة كل يوم
        for date_info in dates:
            date_val = date_info['date']

            # معالجة كل صف (من الصف 2 فما فوق)
            for row_idx in range(2, len(df)):
                # Off-ice session
                off_ice_val = df.iloc[row_idx, date_info['off_ice_col']]
                on_ice_val = df.iloc[row_idx, date_info['on_ice_col']]
                coach_val = df.iloc[row_idx, date_info['coach_col']]

                # معالجة Off-ice
                if pd.notna(off_ice_val) and str(off_ice_val).strip():
                    member_name = str(off_ice_val).strip().lower()

                    if member_name in members_dict:
                        member = members_dict[member_name]
                        matched_members.add(member.id)

                        # إنشاء سجل حضور
                        attendance = Attendance(
                            skater_id=member.id,
                            date=date_val,
                            status='present',
                            session_type='off-ice',
                            notes=f"Coach: {coach_val}" if pd.notna(coach_val) else None
                        )
                        session.add(attendance)
                        total_records += 1
                    else:
                        unmatched_names.add(str(off_ice_val).strip())

                # معالجة On-ice
                if pd.notna(on_ice_val) and str(on_ice_val).strip():
                    member_name = str(on_ice_val).strip().lower()

                    # تخطي إذا كانت كلمات خاصة
                    if member_name in ['coach', 'nan', '!!']:
                        continue

                    if member_name in members_dict:
                        member = members_dict[member_name]
                        matched_members.add(member.id)

                        # إنشاء سجل حضور
                        attendance = Attendance(
                            skater_id=member.id,
                            date=date_val,
                            status='present',
                            session_type='on-ice',
                            notes=f"Coach: {coach_val}" if pd.notna(coach_val) else None
                        )
                        session.add(attendance)
                        total_records += 1
                    else:
                        unmatched_names.add(str(on_ice_val).strip())

        # حفظ البيانات
        print(f"\n💾 حفظ البيانات...")
        session.commit()

        print("\n" + "="*80)
        print("✅ اكتمل الاستيراد بنجاح!")
        print("="*80)
        print(f"📊 إجمالي السجلات المُضافة: {total_records}")
        print(f"👥 عدد الأعضاء الذين تم تسجيل حضورهم: {len(matched_members)}")
        print(f"📅 عدد الأيام: {len(dates)}")

        if unmatched_names:
            print(f"\n⚠️  أسماء لم يتم مطابقتها ({len(unmatched_names)}):")
            for name in sorted(unmatched_names)[:20]:  # أول 20 فقط
                print(f"   - {name}")

        # إحصائيات نهائية
        total_attendance_db = session.query(Attendance).count()
        print(f"\n📊 إجمالي سجلات الحضور في قاعدة البيانات: {total_attendance_db}")

        print("\n" + "="*80)
        print("🎉 تم الاستيراد بنجاح!")
        print("="*80)


if __name__ == "__main__":
    import_october_attendance()
