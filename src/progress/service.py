"""
خدمة بيانات تقييمات اللاعبين - قراءة/كتابة تقييمات الأداء عبر الزمن
Evaluation data service. All functions take a live sqlite3 connection.
"""
import pandas as pd
from datetime import datetime


def save_evaluation(conn, member_id, evaluation_date, tes=0.0, pcs=0.0,
                    total_score=None, jump_success_rate=None, elements_count=0,
                    falls_count=0, deductions=0.0, coach=None, notes=None,
                    evaluation_type="training", source="manual"):
    """يحفظ تقييماً جديداً ويعيد المعرّف."""
    if total_score is None:
        total_score = round(float(tes) + float(pcs) - float(deductions or 0), 2)
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO evaluations
           (member_id, evaluation_date, evaluation_type, tes, pcs, total_score,
            jump_success_rate, elements_count, falls_count, deductions, coach,
            notes, source, created_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (int(member_id), str(evaluation_date), evaluation_type, float(tes),
         float(pcs), float(total_score),
         (None if jump_success_rate is None else float(jump_success_rate)),
         int(elements_count or 0), int(falls_count or 0), float(deductions or 0),
         coach, notes, source, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    )
    conn.commit()
    return cur.lastrowid


def get_member_evaluations(conn, member_id):
    """يعيد تقييمات لاعب مرتبة تصاعدياً حسب التاريخ."""
    df = pd.read_sql_query(
        "SELECT * FROM evaluations WHERE member_id=? ORDER BY evaluation_date ASC, id ASC",
        conn, params=(int(member_id),),
    )
    return df


def get_all_evaluations(conn):
    """يعيد كل التقييمات مع اسم اللاعب."""
    return pd.read_sql_query(
        """SELECT e.*, m.name AS member_name, m.level AS member_level
           FROM evaluations e JOIN members m ON e.member_id = m.id
           ORDER BY e.evaluation_date ASC""",
        conn,
    )


def get_club_average_over_time(conn):
    """متوسط درجة النادي شهرياً."""
    return pd.read_sql_query(
        """SELECT substr(evaluation_date,1,7) AS month,
                  AVG(total_score) AS avg_score, COUNT(*) AS n
           FROM evaluations
           GROUP BY month ORDER BY month""",
        conn,
    )


def get_club_average_score(conn):
    """متوسط آخر درجة لكل لاعب على مستوى النادي."""
    df = pd.read_sql_query(
        """SELECT member_id, total_score, evaluation_date FROM evaluations
           ORDER BY member_id, evaluation_date DESC""",
        conn,
    )
    if df.empty:
        return 0.0
    latest = df.groupby("member_id").first()
    return float(latest["total_score"].mean())


def top_improvers(conn, limit=5):
    """أكثر اللاعبين تطوراً (الفرق بين أول وآخر تقييم)."""
    df = get_all_evaluations(conn)
    if df.empty:
        return pd.DataFrame(columns=["member_id", "member_name", "first", "last", "improvement", "count"])
    rows = []
    for mid, g in df.groupby("member_id"):
        g = g.sort_values("evaluation_date")
        if len(g) < 2:
            continue
        first = float(g["total_score"].iloc[0])
        last = float(g["total_score"].iloc[-1])
        rows.append({
            "member_id": mid,
            "member_name": g["member_name"].iloc[0],
            "first": round(first, 2),
            "last": round(last, 2),
            "improvement": round(last - first, 2),
            "count": len(g),
        })
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    return out.sort_values("improvement", ascending=False).head(limit).reset_index(drop=True)


def get_member_attendance(conn, member_id):
    """سجل حضور اللاعب."""
    return pd.read_sql_query(
        "SELECT * FROM attendance WHERE member_id=? ORDER BY date ASC",
        conn, params=(int(member_id),),
    )


def member_summary(conn, member_id):
    """ملخص أرقام تطوّر اللاعب."""
    ev = get_member_evaluations(conn, member_id)
    summary = {
        "count": len(ev),
        "latest": None, "best": None, "average": None,
        "improvement": None, "latest_date": None,
        "avg_jump": None,
    }
    if ev.empty:
        return summary, ev
    summary["latest"] = round(float(ev["total_score"].iloc[-1]), 2)
    summary["best"] = round(float(ev["total_score"].max()), 2)
    summary["average"] = round(float(ev["total_score"].mean()), 2)
    summary["latest_date"] = ev["evaluation_date"].iloc[-1]
    if len(ev) >= 2:
        summary["improvement"] = round(
            float(ev["total_score"].iloc[-1]) - float(ev["total_score"].iloc[0]), 2)
    jr = ev["jump_success_rate"].dropna()
    if len(jr) > 0:
        summary["avg_jump"] = round(float(jr.mean()), 1)
    return summary, ev


def delete_evaluation(conn, eval_id):
    cur = conn.cursor()
    cur.execute("DELETE FROM evaluations WHERE id=?", (int(eval_id),))
    conn.commit()
    return cur.rowcount
