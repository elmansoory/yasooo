"""
خدمة بيانات المسابقات - إنشاء المسابقات، تسجيل اللاعبين، وتدوين النتائج.
Competitions data service. All functions take a live sqlite3 connection.
"""
import pandas as pd

SEGMENTS = {"short": "برنامج قصير", "free": "برنامج حر", "test": "اختبار", "other": "أخرى"}


def create_competition(conn, name, comp_date=None, location=None, level=None, notes=None):
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO competitions (name, comp_date, location, level, notes)
           VALUES (?,?,?,?,?)""",
        (name.strip(), comp_date, location, level, notes),
    )
    conn.commit()
    return cur.lastrowid


def update_competition(conn, comp_id, name, comp_date=None, location=None, level=None, notes=None):
    cur = conn.cursor()
    cur.execute(
        """UPDATE competitions SET name=?, comp_date=?, location=?, level=?, notes=?
           WHERE id=?""",
        (name.strip(), comp_date, location, level, notes, int(comp_id)),
    )
    conn.commit()
    return cur.rowcount


def delete_competition(conn, comp_id):
    cur = conn.cursor()
    cur.execute("DELETE FROM competitions WHERE id=?", (int(comp_id),))
    conn.commit()
    return cur.rowcount


def list_competitions(conn):
    return pd.read_sql_query(
        """SELECT c.*, COUNT(e.id) AS entries
           FROM competitions c
           LEFT JOIN competition_entries e ON e.competition_id = c.id
           GROUP BY c.id
           ORDER BY date(c.comp_date) DESC, c.id DESC""",
        conn,
    )


def add_entry(conn, competition_id, member_id, segment="free"):
    """يسجّل لاعباً في مسابقة. يعيد المعرّف أو None عند التكرار."""
    cur = conn.cursor()
    cur.execute(
        """INSERT OR IGNORE INTO competition_entries
           (competition_id, member_id, segment) VALUES (?,?,?)""",
        (int(competition_id), int(member_id), segment),
    )
    conn.commit()
    return cur.lastrowid if cur.rowcount else None


def list_entries(conn, competition_id):
    return pd.read_sql_query(
        """SELECT e.id, e.member_id, m.name, m.level, e.segment,
                  e.rank, e.score, e.notes
           FROM competition_entries e JOIN members m ON e.member_id = m.id
           WHERE e.competition_id = ?
           ORDER BY (e.rank IS NULL), e.rank ASC, e.score DESC""",
        conn, params=(int(competition_id),),
    )


def update_result(conn, entry_id, rank=None, score=None, notes=None):
    cur = conn.cursor()
    cur.execute(
        "UPDATE competition_entries SET rank=?, score=?, notes=? WHERE id=?",
        ((int(rank) if rank not in (None, 0) else None),
         (float(score) if score is not None else None), notes, int(entry_id)),
    )
    conn.commit()
    return cur.rowcount


def delete_entry(conn, entry_id):
    cur = conn.cursor()
    cur.execute("DELETE FROM competition_entries WHERE id=?", (int(entry_id),))
    conn.commit()
    return cur.rowcount


def member_history(conn, member_id):
    return pd.read_sql_query(
        """SELECT c.name, c.comp_date, c.location, e.segment, e.rank, e.score
           FROM competition_entries e JOIN competitions c ON e.competition_id = c.id
           WHERE e.member_id = ?
           ORDER BY date(c.comp_date) DESC""",
        conn, params=(int(member_id),),
    )
