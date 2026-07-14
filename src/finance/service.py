"""
خدمة البيانات المالية - الإيرادات وتنبيهات تجديد الاشتراكات.
Finance data service. All functions take a live sqlite3 connection.
"""
from datetime import datetime

import pandas as pd

_LATEST_MEMBERSHIP = """
SELECT m.id AS member_id, m.name, m.level, m.coach,
       ms.id AS membership_id,
       ms.bundle_type, ms.amount, ms.discount, ms.payment_date,
       COALESCE(ms.duration_months, 1) AS duration_months,
       date(ms.payment_date, '+' || COALESCE(ms.duration_months, 1) || ' months') AS expiry_date
FROM members m
LEFT JOIN memberships ms ON ms.id = (
    SELECT ms2.id FROM memberships ms2
    WHERE ms2.member_id = m.id
    ORDER BY date(ms2.payment_date) DESC, ms2.id DESC
    LIMIT 1
)
ORDER BY m.name
"""


def revenue_totals(conn):
    """إجمالي الإيرادات والصافي وعدد المدفوعات."""
    df = pd.read_sql_query(
        "SELECT COALESCE(SUM(amount),0) AS gross, "
        "COALESCE(SUM(discount),0) AS discount, COUNT(*) AS count FROM memberships",
        conn,
    )
    gross = float(df["gross"].iloc[0])
    discount = float(df["discount"].iloc[0])
    return {"gross": gross, "discount": discount,
            "net": gross - discount, "count": int(df["count"].iloc[0])}


def monthly_revenue(conn):
    """الإيرادات الشهرية (حسب تاريخ الدفع)."""
    return pd.read_sql_query(
        """SELECT substr(payment_date, 1, 7) AS month,
                  SUM(amount) AS revenue,
                  SUM(amount) - SUM(COALESCE(discount, 0)) AS net,
                  COUNT(*) AS payments
           FROM memberships
           WHERE payment_date IS NOT NULL AND payment_date != ''
           GROUP BY month ORDER BY month""",
        conn,
    )


def revenue_by_bundle(conn):
    """الإيرادات حسب نوع الباقة."""
    return pd.read_sql_query(
        """SELECT COALESCE(bundle_type, 'غير محدد') AS bundle_type,
                  SUM(amount) AS revenue, COUNT(*) AS count
           FROM memberships
           GROUP BY bundle_type ORDER BY revenue DESC""",
        conn,
    )


def all_payments(conn):
    """سجل كل المدفوعات مع اسم اللاعب."""
    return pd.read_sql_query(
        """SELECT ms.id, m.name, ms.bundle_type, ms.amount, ms.discount,
                  ms.payment_date, COALESCE(ms.duration_months, 1) AS duration_months
           FROM memberships ms JOIN members m ON ms.member_id = m.id
           ORDER BY date(ms.payment_date) DESC, ms.id DESC""",
        conn,
    )


def membership_status(conn, within_days=14):
    """حالة اشتراك كل لاعب (نشط/يقترب الانتهاء/منتهٍ/لا يوجد)."""
    df = pd.read_sql_query(_LATEST_MEMBERSHIP, conn)
    if df.empty:
        df["status"] = []
        df["days_left"] = []
        return df

    today = datetime.now().date()
    statuses, days_left = [], []
    for _, r in df.iterrows():
        if pd.isna(r["membership_id"]):
            statuses.append("none")
            days_left.append(None)
            continue
        exp = r["expiry_date"]
        if pd.isna(r["payment_date"]) or not exp:
            statuses.append("unknown")
            days_left.append(None)
            continue
        try:
            exp_d = datetime.strptime(str(exp), "%Y-%m-%d").date()
        except (ValueError, TypeError):
            statuses.append("unknown")
            days_left.append(None)
            continue
        dl = (exp_d - today).days
        days_left.append(dl)
        if dl < 0:
            statuses.append("expired")
        elif dl <= within_days:
            statuses.append("expiring")
        else:
            statuses.append("active")
    df["status"] = statuses
    df["days_left"] = days_left
    return df


def renewal_alerts(conn, within_days=14):
    """اللاعبون الذين يحتاجون تجديداً (منتهٍ/يقترب) + بلا اشتراك."""
    df = membership_status(conn, within_days=within_days)
    if df.empty:
        return df
    alert = df[df["status"].isin(["expired", "expiring", "none"])].copy()
    order = {"expired": 0, "expiring": 1, "none": 2}
    alert["_o"] = alert["status"].map(order)
    alert = alert.sort_values(["_o", "days_left"], na_position="last").drop(columns="_o")
    return alert.reset_index(drop=True)
