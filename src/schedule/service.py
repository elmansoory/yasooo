"""
خدمة بيانات جدول الحصص الأسبوعي.
Schedule data service. All functions take a live sqlite3 connection.
"""
import pandas as pd

DAYS_AR = ["الإثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]


def _validate(day_of_week, start_time, end_time, capacity):
    if not (0 <= int(day_of_week) <= 6):
        raise ValueError("يوم غير صحيح")
    if str(end_time) <= str(start_time):
        raise ValueError("وقت النهاية يجب أن يكون بعد وقت البداية")
    if capacity is not None and int(capacity) < 0:
        raise ValueError("السعة يجب أن تكون رقماً موجباً")


def add_session(conn, title, day_of_week, start_time, end_time,
                coach=None, level=None, location=None, capacity=None, notes=None):
    _validate(day_of_week, start_time, end_time, capacity)
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO schedule_sessions
           (title, day_of_week, start_time, end_time, coach, level, location, capacity, notes)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (title.strip(), int(day_of_week), str(start_time), str(end_time),
         coach, level, location,
         (int(capacity) if capacity not in (None, 0) else None), notes),
    )
    conn.commit()
    return cur.lastrowid


def update_session(conn, session_id, title, day_of_week, start_time, end_time,
                   coach=None, level=None, location=None, capacity=None, notes=None):
    _validate(day_of_week, start_time, end_time, capacity)
    cur = conn.cursor()
    cur.execute(
        """UPDATE schedule_sessions SET title=?, day_of_week=?, start_time=?, end_time=?,
           coach=?, level=?, location=?, capacity=?, notes=? WHERE id=?""",
        (title.strip(), int(day_of_week), str(start_time), str(end_time),
         coach, level, location,
         (int(capacity) if capacity not in (None, 0) else None), notes, int(session_id)),
    )
    conn.commit()
    return cur.rowcount


def delete_session(conn, session_id):
    cur = conn.cursor()
    cur.execute("DELETE FROM schedule_sessions WHERE id=?", (int(session_id),))
    conn.commit()
    return cur.rowcount


def list_sessions(conn):
    return pd.read_sql_query(
        "SELECT * FROM schedule_sessions ORDER BY day_of_week ASC, start_time ASC",
        conn,
    )
