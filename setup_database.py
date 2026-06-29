"""
Setup Database - Quick Start
إنشاء قاعدة البيانات بسرعة
"""
import sqlite3
import pandas as pd
from datetime import datetime
import random

def create_database():
    """إنشاء قاعدة البيانات الأساسية"""
    print("📊 Creating database...")

    conn = sqlite3.connect('skating_database.db')
    cursor = conn.cursor()

    # Create members table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        gender TEXT,
        birth_date TEXT,
        level TEXT,
        coach TEXT,
        bundle TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Create attendance table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        member_id INTEGER,
        date TEXT NOT NULL,
        status TEXT DEFAULT 'present',
        session_type TEXT,
        coach TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (member_id) REFERENCES members (id)
    )
    ''')

    # Create memberships table (for payments)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS memberships (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        member_id INTEGER,
        bundle_type TEXT,
        amount REAL,
        payment_date TEXT,
        discount REAL DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (member_id) REFERENCES members (id)
    )
    ''')

    conn.commit()
    print("✅ Database structure created")

    # Ensure newer tables (evaluations, etc.) exist
    try:
        from src.database.migrations import ensure_schema
        ensure_schema(conn)
        print("✅ Evaluations table ensured")
    except Exception as exc:
        print(f"⚠️ Could not ensure extra schema: {exc}")

    # Add sample data
    add_sample_data(conn)

    conn.close()
    print("✅ Database ready!")

def add_sample_data(conn):
    """إضافة بيانات تجريبية"""
    print("📝 Adding sample data...")

    # Sample members
    members = [
        ("أحمد محمد", "ذكر", "2010-05-15", "Beta", "Coach Ahmed", "On-Ice Silver"),
        ("فاطمة علي", "أنثى", "2012-03-20", "Gamma", "Coach Sarah", "On-Ice Bronze"),
        ("محمد حسن", "ذكر", "2011-08-10", "Delta", "Coach Ahmed", "On-Ice Gold"),
        ("سارة خالد", "أنثى", "2013-01-25", "Beta", "Coach Sarah", "On-Ice Silver"),
        ("علي أحمد", "ذكر", "2010-11-30", "Gamma", "Coach Ahmed", "On-Ice Bronze"),
    ]

    cursor = conn.cursor()

    for member in members:
        cursor.execute('''
        INSERT INTO members (name, gender, birth_date, level, coach, bundle)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', member)

    conn.commit()

    # Add attendance records
    member_ids = [1, 2, 3, 4, 5]

    from datetime import timedelta
    base_date = datetime(2025, 1, 1)

    for day in range(30):
        current_date = base_date + timedelta(days=day)
        date_str = current_date.strftime('%Y-%m-%d')

        # Random attendance
        for member_id in member_ids:
            if random.random() > 0.3:  # 70% attendance rate
                cursor.execute('''
                INSERT INTO attendance (member_id, date, status, session_type, coach)
                VALUES (?, ?, 'present', 'on-ice', 'Coach Ahmed')
                ''', (member_id, date_str))

    conn.commit()

    # Add payments
    for member_id in member_ids:
        cursor.execute('''
        INSERT INTO memberships (member_id, bundle_type, amount, payment_date)
        VALUES (?, 'On-Ice Silver', 800.0, '2025-01-01')
        ''', (member_id,))

    conn.commit()

    print("✅ Sample data added")

if __name__ == "__main__":
    print("=" * 60)
    print("   Database Setup for Skating Analysis System")
    print("=" * 60)

    create_database()

    print("\n" + "=" * 60)
    print("✅ Setup complete!")
    print("=" * 60)
    print("\nNow you can run:")
    print("  python -m streamlit run app.py")
    print("  python -m streamlit run advanced_app.py")
    print("  python -m streamlit run professional_app.py")
