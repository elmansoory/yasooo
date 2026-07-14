"""
Import Real Data from Excel Files
استيراد البيانات الحقيقية من ملفات Excel
"""
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime

def get_or_create_member(cursor, name, level=None, coach=None):
    """Get existing member or create new one"""
    name = str(name).strip()
    if not name or name == 'nan':
        return None
    cursor.execute("SELECT id FROM members WHERE name = ?", (name,))
    row = cursor.fetchone()
    if row:
        return row[0]
    cursor.execute(
        "INSERT INTO members (name, level, coach) VALUES (?, ?, ?)",
        (name, level, coach)
    )
    return cursor.lastrowid

def import_memberships(conn):
    """Import October Memberships"""
    print("📋 Importing memberships...")
    cursor = conn.cursor()
    df = pd.read_excel('October Memberships.xlsx')

    count = 0
    for _, row in df.iterrows():
        member_name = str(row.get('Member', '')).strip()
        if not member_name or member_name == 'nan':
            continue

        level = str(row.get('Level', '')).strip() if pd.notna(row.get('Level')) else None
        coach = str(row.get('Coach', '')).strip() if pd.notna(row.get('Coach')) else None
        bundle = str(row.get('Bundle', '')).strip() if pd.notna(row.get('Bundle')) else None
        amount = float(row.get('Amount', 0)) if pd.notna(row.get('Amount')) else 0.0
        discount = float(row.get('Discount ', 0)) if pd.notna(row.get('Discount ')) else 0.0
        dop = row.get('DOP')
        payment_date = None
        if pd.notna(dop):
            try:
                payment_date = pd.to_datetime(dop).strftime('%Y-%m-%d')
            except:
                payment_date = None

        level_clean = level if level and level != 'nan' else None
        coach_clean = coach if coach and coach != 'nan' else None

        member_id = get_or_create_member(cursor, member_name, level_clean, coach_clean)
        if member_id is None:
            continue

        # Update member info if we have it
        if level_clean:
            cursor.execute("UPDATE members SET level=? WHERE id=? AND (level IS NULL OR level='')",
                         (level_clean, member_id))
        if coach_clean:
            cursor.execute("UPDATE members SET coach=? WHERE id=? AND (coach IS NULL OR coach='')",
                         (coach_clean, member_id))

        # Check if membership already exists
        cursor.execute(
            "SELECT id FROM memberships WHERE member_id=? AND bundle_type=? AND amount=?",
            (member_id, bundle, amount)
        )
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO memberships (member_id, bundle_type, amount, payment_date, discount) VALUES (?,?,?,?,?)",
                (member_id, bundle, amount, payment_date, discount)
            )
            count += 1

    conn.commit()
    print(f"  ✅ Imported {count} membership records")

def import_attendance(conn):
    """Import October Attendance"""
    print("📅 Importing attendance records...")
    cursor = conn.cursor()

    df = pd.read_excel('October 2025 Attendence.xlsx')
    cols = df.columns.tolist()

    # Parse column groups: every 3 cols = (Off-ice, On-ice, Coach) for one date
    date_groups = []
    i = 0
    while i < len(cols):
        col = cols[i]
        if hasattr(col, 'strftime'):  # It's a datetime
            date_str = col.strftime('%Y-%m-%d')
            off_ice_col = col
            on_ice_col = cols[i+1] if i+1 < len(cols) else None
            coach_col = cols[i+2] if i+2 < len(cols) else None
            date_groups.append((date_str, off_ice_col, on_ice_col, coach_col))
            i += 3
        else:
            i += 1

    count = 0
    for date_str, off_ice_col, on_ice_col, coach_col in date_groups:
        # Rows 3+ contain player names
        for row_idx in range(3, len(df)):
            row = df.iloc[row_idx]

            # On-ice attendance
            on_ice_name = row.get(on_ice_col) if on_ice_col else None
            coach_name = str(row.get(coach_col, '')).strip() if coach_col else None
            if coach_name == 'nan':
                coach_name = None

            if pd.notna(on_ice_name) and str(on_ice_name).strip() not in ('nan', ''):
                player_name = str(on_ice_name).strip()
                member_id = get_or_create_member(cursor, player_name)
                if member_id:
                    cursor.execute(
                        "SELECT id FROM attendance WHERE member_id=? AND date=? AND session_type='on-ice'",
                        (member_id, date_str)
                    )
                    if not cursor.fetchone():
                        cursor.execute(
                            "INSERT INTO attendance (member_id, date, status, session_type, coach) VALUES (?,?,?,?,?)",
                            (member_id, date_str, 'present', 'on-ice', coach_name)
                        )
                        count += 1

            # Off-ice attendance
            off_ice_name = row.get(off_ice_col) if off_ice_col else None
            if pd.notna(off_ice_name) and str(off_ice_name).strip() not in ('nan', ''):
                player_name = str(off_ice_name).strip()
                member_id = get_or_create_member(cursor, player_name)
                if member_id:
                    cursor.execute(
                        "SELECT id FROM attendance WHERE member_id=? AND date=? AND session_type='off-ice'",
                        (member_id, date_str)
                    )
                    if not cursor.fetchone():
                        cursor.execute(
                            "INSERT INTO attendance (member_id, date, status, session_type, coach) VALUES (?,?,?,?,?)",
                            (member_id, date_str, 'present', 'off-ice', coach_name)
                        )
                        count += 1

    conn.commit()
    print(f"  ✅ Imported {count} attendance records")

def run():
    print("=" * 60)
    print("   Importing Real Data into Database")
    print("=" * 60)

    conn = sqlite3.connect('skating_database.db')

    # Clear old sample data
    cursor = conn.cursor()
    print("🗑️  Clearing old sample data...")
    cursor.execute("DELETE FROM memberships")
    cursor.execute("DELETE FROM attendance")
    cursor.execute("DELETE FROM members")
    conn.commit()

    import_memberships(conn)
    import_attendance(conn)

    # Summary
    cursor.execute("SELECT COUNT(*) FROM members")
    members_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM attendance")
    att_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM memberships")
    mem_count = cursor.fetchone()[0]

    conn.close()

    print()
    print("=" * 60)
    print("✅ Import complete!")
    print(f"  👥 Members: {members_count}")
    print(f"  📅 Attendance records: {att_count}")
    print(f"  💳 Membership records: {mem_count}")
    print("=" * 60)

if __name__ == "__main__":
    run()
