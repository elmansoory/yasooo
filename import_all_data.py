#!/usr/bin/env python3
"""
برنامج استيراد شامل لجميع البيانات من ملفات Excel
"""
import pandas as pd
import sqlite3
from datetime import datetime
import sys

def create_database():
    """إنشاء قاعدة البيانات"""
    conn = sqlite3.connect('skating_database.db')
    cursor = conn.cursor()

    # جدول الأعضاء
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        gender TEXT,
        birth_date TEXT,
        level TEXT,
        coach TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # جدول الحضور
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        member_id INTEGER,
        date TEXT NOT NULL,
        session_type TEXT,
        coach TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (member_id) REFERENCES members(id)
    )
    ''')

    # جدول العضويات/الدفعات
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS memberships (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        member_id INTEGER,
        level TEXT,
        coach TEXT,
        bundle TEXT,
        amount REAL,
        discount REAL,
        payment_date TEXT,
        paid_to TEXT,
        payment_method TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (member_id) REFERENCES members(id)
    )
    ''')

    conn.commit()
    return conn

def import_october_memberships(conn):
    """استيراد بيانات العضويات من October Memberships.xlsx"""
    print("\n📋 استيراد بيانات العضويات...")

    try:
        df = pd.read_excel("October Memberships.xlsx")
        cursor = conn.cursor()

        imported = 0
        for _, row in df.iterrows():
            member_name = str(row['Member']).strip()
            if member_name and member_name != 'nan':
                # إدراج أو تحديث العضو
                cursor.execute('''
                INSERT OR IGNORE INTO members (name, level, coach)
                VALUES (?, ?, ?)
                ''', (
                    member_name,
                    str(row.get('Level', '')),
                    str(row.get('Coach', ''))
                ))

                # الحصول على member_id
                cursor.execute('SELECT id FROM members WHERE name = ?', (member_name,))
                member_id = cursor.fetchone()[0]

                # إدراج بيانات العضوية
                payment_date = row.get('DOP')
                if pd.notna(payment_date):
                    try:
                        payment_date = pd.to_datetime(payment_date).strftime('%Y-%m-%d')
                    except:
                        payment_date = None
                else:
                    payment_date = None

                cursor.execute('''
                INSERT INTO memberships
                (member_id, level, coach, bundle, amount, discount, payment_date, paid_to, payment_method)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    member_id,
                    str(row.get('Level', '')) if pd.notna(row.get('Level')) else '',
                    str(row.get('Coach', '')) if pd.notna(row.get('Coach')) else '',
                    str(row.get('Bundle', '')) if pd.notna(row.get('Bundle')) else '',
                    float(row.get('Amount', 0)) if pd.notna(row.get('Amount')) else 0,
                    float(row.get('Discount ', 0)) if pd.notna(row.get('Discount ')) else 0,
                    payment_date,
                    str(row.get('Paid to', '')) if pd.notna(row.get('Paid to')) else '',
                    str(row.get('Pain in', '')) if pd.notna(row.get('Pain in')) else ''
                ))

                imported += 1

        conn.commit()
        print(f"✅ تم استيراد {imported} عضوية")
        return imported

    except Exception as e:
        print(f"❌ خطأ في استيراد العضويات: {e}")
        return 0

def import_attendance_file(conn, file_path, month_name):
    """استيراد بيانات الحضور من ملف Excel"""
    print(f"\n📅 استيراد حضور {month_name}...")

    try:
        df = pd.read_excel(file_path)
        cursor = conn.cursor()

        # استخراج التواريخ من رؤوس الأعمدة
        dates = []
        for col in df.columns:
            if isinstance(col, datetime):
                dates.append(col.strftime('%Y-%m-%d'))

        print(f"   وجدت {len(dates)} يوم")

        # قراءة البيانات بدءاً من الصف 3
        imported = 0

        # المرور على كل صف (بدءاً من الصف 5 حيث تبدأ أسماء اللاعبين)
        for row_idx in range(5, len(df)):
            row = df.iloc[row_idx]

            # البحث عن اسم اللاعب في الأعمدة
            player_name = None
            for col_idx, cell_value in enumerate(row):
                if isinstance(cell_value, str) and len(cell_value.strip()) > 2:
                    # تجاهل أسماء المدربين المعروفة
                    if cell_value.strip() not in ['Ahmed saad', 'Esraa Nabil', 'Clara Amgad',
                                                   'Hajar Munir', 'Eman moustafa', 'Coach']:
                        player_name = cell_value.strip()
                        break

            if not player_name:
                continue

            # إدراج أو تحديث اللاعب
            cursor.execute('INSERT OR IGNORE INTO members (name) VALUES (?)', (player_name,))
            cursor.execute('SELECT id FROM members WHERE name = ?', (player_name,))
            result = cursor.fetchone()
            if not result:
                continue
            member_id = result[0]

            # المرور على الأعمدة لإيجاد علامات الحضور
            col_idx = 0
            for date_str in dates:
                # كل تاريخ له 3 أعمدة: Off-ice, On-ice, Coach
                base_idx = col_idx * 3

                if base_idx + 2 < len(row):
                    # التحقق من الحضور (إذا كان هناك أي علامة)
                    on_ice = str(row.iloc[base_idx + 1]) if pd.notna(row.iloc[base_idx + 1]) else ''
                    coach = str(row.iloc[base_idx + 2]) if pd.notna(row.iloc[base_idx + 2]) else ''

                    # إذا كان هناك حضور
                    if on_ice and on_ice != 'nan' and on_ice.strip():
                        cursor.execute('''
                        INSERT OR IGNORE INTO attendance
                        (member_id, date, session_type, coach)
                        VALUES (?, ?, ?, ?)
                        ''', (
                            member_id,
                            date_str,
                            'On-ice',
                            coach if coach and coach != 'nan' else ''
                        ))
                        imported += 1

                col_idx += 1

        conn.commit()
        print(f"✅ تم استيراد {imported} سجل حضور")
        return imported

    except Exception as e:
        print(f"❌ خطأ في استيراد الحضور: {e}")
        import traceback
        traceback.print_exc()
        return 0

def get_database_stats(conn):
    """عرض إحصائيات قاعدة البيانات"""
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM members')
    members_count = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM attendance')
    attendance_count = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM memberships')
    memberships_count = cursor.fetchone()[0]

    print(f"\n{'='*60}")
    print("📊 إحصائيات قاعدة البيانات:")
    print(f"{'='*60}")
    print(f"👥 عدد الأعضاء: {members_count}")
    print(f"📅 سجلات الحضور: {attendance_count}")
    print(f"💳 سجلات العضويات: {memberships_count}")
    print(f"{'='*60}")

def main():
    """البرنامج الرئيسي"""
    print("🚀 بدء استيراد البيانات...")

    # إنشاء قاعدة البيانات
    conn = create_database()

    # استيراد العضويات
    import_october_memberships(conn)

    # استيراد الحضور - أكتوبر
    import_attendance_file(conn, "October 2025 Attendence.xlsx", "أكتوبر 2025")

    # استيراد الحضور - أغسطس (إذا كان موجوداً)
    try:
        import_attendance_file(conn, "August 2025 Attendence.xlsx", "أغسطس 2025")
    except:
        print("⚠️  ملف أغسطس غير متوفر")

    # عرض الإحصائيات
    get_database_stats(conn)

    conn.close()
    print("\n✅ تم الانتهاء من الاستيراد بنجاح!")

if __name__ == "__main__":
    main()
