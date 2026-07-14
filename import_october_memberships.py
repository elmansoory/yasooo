"""
استيراد الأعضاء من ملف عضوية أكتوبر October Memberships.xlsx
"""
import pandas as pd
import sys
from pathlib import Path

# إضافة مسار المشروع
sys.path.insert(0, str(Path(__file__).parent))

from src.database.database_manager import DatabaseManager
from src.database.models import Skater

def import_october_memberships():
    """استيراد الأعضاء من ملف العضوية"""

    print("=" * 70)
    print("📂 استيراد بيانات عضوية أكتوبر")
    print("=" * 70)

    # تهيئة قاعدة البيانات
    db_path = "sqlite:///skating_analysis.db"
    db_manager = DatabaseManager(db_path)
    db_manager.init_db()  # تهيئة الجلسة

    # قراءة ملف Excel
    file_path = "October Memberships.xlsx"
    print(f"\n📖 قراءة الملف: {file_path}")

    try:
        df = pd.read_excel(file_path)
        print(f"✅ تم قراءة {len(df)} سجل")

        # إحصائيات
        stats = {
            'total': len(df),
            'imported': 0,
            'skipped': 0,
            'errors': 0
        }

        print("\n🔄 بدء الاستيراد...")
        print("-" * 70)

        with db_manager.get_session() as session:
            for idx, row in df.iterrows():
                member_name = row['Member']

                # تخطي الصفوف الفارغة
                if pd.isna(member_name) or str(member_name).strip() == '':
                    stats['skipped'] += 1
                    continue

                member_name = str(member_name).strip()

                try:
                    # التحقق من عدم التكرار
                    existing = session.query(Skater).filter_by(name=member_name).first()

                    if existing:
                        print(f"  ⏭️  موجود مسبقاً: {member_name}")
                        stats['skipped'] += 1
                        continue

                    # استخراج البيانات
                    level = row.get('Level')
                    coach = row.get('Coach')
                    bundle = row.get('Bundle')

                    # تحديد الجنس تلقائياً (يمكن تحسينه لاحقاً)
                    gender = None

                    # إنشاء السجل
                    skater = Skater(
                        name=member_name,
                        country="مصر",
                        discipline="Singles",
                        gender=gender,
                        level=str(level) if pd.notna(level) else None,
                        coach_name=str(coach) if pd.notna(coach) else None,
                        bundle=str(bundle) if pd.notna(bundle) else None,
                        membership_status="active",
                        notes=f"مستورد من ملف عضوية أكتوبر",
                        total_videos=0,
                        total_analyses=0
                    )

                    session.add(skater)
                    print(f"  ✅ تمت الإضافة: {member_name} ({level if pd.notna(level) else 'N/A'}) - {bundle if pd.notna(bundle) else 'N/A'}")
                    stats['imported'] += 1

                except Exception as e:
                    print(f"  ❌ خطأ في {member_name}: {e}")
                    stats['errors'] += 1
                    continue

        # عرض الإحصائيات النهائية
        print("\n" + "=" * 70)
        print("📊 نتائج الاستيراد")
        print("=" * 70)
        print(f"  📁 إجمالي السجلات في الملف: {stats['total']}")
        print(f"  ✅ تمت الإضافة: {stats['imported']}")
        print(f"  ⏭️  تم تخطيها (موجودة مسبقاً): {stats['skipped']}")
        print(f"  ❌ أخطاء: {stats['errors']}")
        print("=" * 70)

        print("\n✨ اكتمل الاستيراد بنجاح!")

        # عرض إحصائيات قاعدة البيانات
        print("\n" + "=" * 70)
        print("📊 إحصائيات قاعدة البيانات")
        print("=" * 70)

        with db_manager.get_session() as session:
            total_players = session.query(Skater).filter(
                ~Skater.notes.like('%مدرب%')
            ).count()

            total_coaches = session.query(Skater).filter(
                Skater.notes.like('%مدرب%')
            ).count()

            active_members = session.query(Skater).filter(
                Skater.membership_status == 'active'
            ).count()

            print(f"  👥 إجمالي اللاعبين: {total_players}")
            print(f"  🎓 إجمالي المدربين: {total_coaches}")
            print(f"  ✅ الأعضاء النشطون: {active_members}")
            print(f"  📊 المجموع الكلي: {total_players + total_coaches}")

        print("=" * 70)

    except FileNotFoundError:
        print(f"\n❌ خطأ: الملف '{file_path}' غير موجود!")
        print("💡 تأكد من وجود ملف 'October Memberships.xlsx' في نفس المجلد")
    except Exception as e:
        print(f"\n❌ خطأ: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import_october_memberships()
