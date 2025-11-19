#!/usr/bin/env python3
"""
استيراد اللاعبين والمدربين إلى قاعدة البيانات
"""
import json
import sys
from pathlib import Path

# إضافة مسار src للمسار
sys.path.insert(0, str(Path(__file__).parent))

from src.database.database_manager import DatabaseManager
from src.database.models import Skater
from datetime import datetime

def import_data():
    """استيراد البيانات إلى قاعدة البيانات"""

    print("="*80)
    print("📥 استيراد اللاعبين والمدربين إلى قاعدة البيانات")
    print("="*80)

    # قراءة البيانات المستخرجة
    with open('players_coaches.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    players = data['players']
    coaches = data['coaches']

    print(f"\n📊 البيانات المستخرجة:")
    print(f"  👥 اللاعبين: {len(players)}")
    print(f"  🎓 المدربين: {len(coaches)}")

    # إنشاء قاعدة البيانات
    db_path = "sqlite:///skating_analysis.db"
    db = DatabaseManager(db_path)
    db.init_db()

    added_players = 0
    added_coaches = 0
    skipped = 0

    print("\n⏳ جاري الاستيراد...")

    with db.get_session() as session:
        # استيراد اللاعبين
        print(f"\n👥 استيراد اللاعبين:")
        for player_name in players:
            # التحقق من عدم وجوده مسبقاً
            existing = session.query(Skater).filter_by(name=player_name).first()

            if not existing:
                skater = Skater(
                    name=player_name,
                    country="Egypt",
                    discipline="Singles",  # افتراضي
                    total_videos=0,
                    total_analyses=0,
                    notes="تم الاستيراد من ملفات الحضور",
                    created_at=datetime.utcnow()
                )
                session.add(skater)
                print(f"  ✅ {player_name}")
                added_players += 1
            else:
                print(f"  ⏭️  {player_name} (موجود مسبقاً)")
                skipped += 1

        print(f"\n💾 جاري حفظ {added_players} لاعب...")

        # استيراد المدربين
        print(f"\n🎓 استيراد المدربين:")
        for coach_name in coaches:
            existing = session.query(Skater).filter_by(name=coach_name).first()

            if not existing:
                coach = Skater(
                    name=coach_name,
                    country="Egypt",
                    discipline="Coach",
                    total_videos=0,
                    total_analyses=0,
                    notes="مدرب - تم الاستيراد من ملفات الحضور",
                    created_at=datetime.utcnow()
                )
                session.add(coach)
                print(f"  ✅ {coach_name}")
                added_coaches += 1
            else:
                # تحديث الملاحظات للإشارة إلى أنه مدرب
                if "مدرب" not in str(existing.notes):
                    existing.notes = f"{existing.notes or ''}\nمدرب".strip()
                    print(f"  ✏️  {coach_name} (تحديث كمدرب)")
                else:
                    print(f"  ⏭️  {coach_name} (موجود مسبقاً)")
                skipped += 1

        print(f"\n💾 جاري حفظ {added_coaches} مدرب...")

    # الملخص
    print("\n" + "="*80)
    print("📊 ملخص الاستيراد")
    print("="*80)
    print(f"  ✅ لاعبين جدد: {added_players}")
    print(f"  ✅ مدربين جدد: {added_coaches}")
    print(f"  ⏭️  متخطى (موجود مسبقاً): {skipped}")
    print(f"  📊 الإجمالي: {added_players + added_coaches + skipped}")

    # عرض بعض الإحصائيات
    with db.get_session() as session:
        total_skaters = session.query(Skater).count()
        total_coaches = session.query(Skater).filter(
            Skater.notes.like('%مدرب%')
        ).count()

        print(f"\n📈 قاعدة البيانات الحالية:")
        print(f"  👥 إجمالي السجلات: {total_skaters}")
        print(f"  🎓 المدربين: {total_coaches}")
        print(f"  👨‍🎓 اللاعبين: {total_skaters - total_coaches}")

    db.close()
    print("\n✅ تم الانتهاء من الاستيراد!")
    print("="*80)

if __name__ == "__main__":
    import_data()
