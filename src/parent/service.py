"""
خدمة بوابة أولياء الأمور - رموز وصول لكل لاعب (للقراءة فقط).
Parent portal access service. Codes are bearer secrets — high entropy, revocable.
All functions take a live sqlite3 connection.
"""
import secrets
from datetime import datetime

import pandas as pd


def _new_code():
    return secrets.token_urlsafe(9)


def get_or_create_code(conn, member_id):
    """يعيد رمز اللاعب، ويُنشئه إن لم يوجد."""
    cur = conn.cursor()
    row = cur.execute(
        "SELECT code FROM parent_access WHERE member_id=?", (int(member_id),)
    ).fetchone()
    if row:
        return row[0]
    code = _new_code()
    cur.execute(
        "INSERT INTO parent_access (member_id, code, active) VALUES (?,?,1)",
        (int(member_id), code),
    )
    conn.commit()
    return code


def regenerate_code(conn, member_id):
    """يولّد رمزاً جديداً للّاعب (يُبطل القديم)."""
    code = _new_code()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO parent_access (member_id, code, active) VALUES (?,?,1)
           ON CONFLICT(member_id) DO UPDATE SET code=excluded.code, active=1""",
        (int(member_id), code),
    )
    conn.commit()
    return code


def set_active(conn, member_id, active):
    cur = conn.cursor()
    cur.execute(
        "UPDATE parent_access SET active=? WHERE member_id=?",
        (1 if active else 0, int(member_id)),
    )
    conn.commit()
    return cur.rowcount


def list_access(conn):
    """قائمة رموز الوصول مع أسماء اللاعبين (لوحة المالك)."""
    return pd.read_sql_query(
        """SELECT m.id AS member_id, m.name, pa.code, pa.active, pa.last_viewed_at
           FROM members m
           LEFT JOIN parent_access pa ON pa.member_id = m.id
           ORDER BY m.name""",
        conn,
    )


def verify_code(conn, code):
    """تحقق خفيف (بدون تحديث آخر اطلاع). يعيد member_id إن كان الرمز صحيحاً ونشطاً.

    يُستخدم في كل إعادة رسم لفرض الإيقاف/التجديد: الرمز القديم يفشل بعد التجديد،
    والرمز الموقوف يفشل فوراً.
    """
    if not code or not str(code).strip():
        return None
    row = conn.execute(
        "SELECT member_id FROM parent_access WHERE code=? AND active=1",
        (str(code).strip(),),
    ).fetchone()
    return int(row[0]) if row else None


def authenticate(conn, code):
    """يتحقق من رمز الوصول ويحدّث آخر اطلاع. يعيد member_id أو None."""
    mid = verify_code(conn, code)
    if mid is None:
        return None
    conn.execute(
        "UPDATE parent_access SET last_viewed_at=? WHERE member_id=?",
        (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), mid),
    )
    conn.commit()
    return mid
