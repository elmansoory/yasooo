"""
بوابة أولياء الأمور - عرض للقراءة فقط لتقدّم الطفل عبر رمز وصول.
Parent portal (parent-facing, code only) + owner code admin (separate page).
The parent page NEVER shows member selectors or lists — it queries by exact code only.
"""
import streamlit as st

from src.parent import service as parent_svc
from src.progress import service as prog_svc
from src.progress import charts
from src.finance import service as fin_svc
from src.utils import settings as club_cfg

try:
    from src.utils.member_pdf import build_member_progress_pdf, PDF_AVAILABLE
except Exception:
    PDF_AVAILABLE = False

_STATUS_AR = {"active": "🟢 نشط", "expiring": "🟠 يقترب الانتهاء",
              "expired": "🔴 منتهٍ — يرجى التجديد", "none": "⚪ لا يوجد اشتراك",
              "unknown": "❔ غير معروف"}


# ─────────────────────────────────────────────────────────────
# PARENT-FACING PAGE (code only)
# ─────────────────────────────────────────────────────────────
def _parent_logout():
    for k in ("parent_code", "parent_pdf_bytes"):
        st.session_state.pop(k, None)


def show_parent_portal(get_data, execute_query, get_connection, clear_cache):
    st.title("👨‍👩‍👧 بوابة ولي الأمر")
    conn = get_connection()

    # تحقّق من الرمز في كل إعادة رسم لفرض الإيقاف/التجديد فوراً
    code = st.session_state.get("parent_code")
    mid = parent_svc.verify_code(conn, code) if code else None
    if code and mid is None:
        _parent_logout()
        st.warning("انتهت صلاحية الجلسة أو تم تغيير الرمز. يُرجى إدخال الرمز من جديد.")

    if mid is None:
        st.caption("أدخل رمز الوصول الخاص بطفلك لعرض تقدّمه (للقراءة فقط).")
        with st.form("parent_login"):
            entered = st.text_input("🔑 رمز الوصول", type="password")
            if st.form_submit_button("دخول", type="primary"):
                found = parent_svc.authenticate(conn, entered)
                if found is None:
                    st.error("رمز غير صحيح أو موقوف. تواصل مع إدارة النادي.")
                else:
                    st.session_state["parent_code"] = entered.strip()
                    st.session_state.pop("parent_pdf_bytes", None)
                    st.rerun()
        return

    member = get_data("SELECT * FROM members WHERE id=?", (int(mid),))
    if member.empty:
        _parent_logout()
        st.error("تعذّر العثور على بيانات اللاعب.")
        return
    m = member.iloc[0]

    top1, top2 = st.columns([4, 1])
    top1.subheader(f"🧒 {m['name']}")
    with top2:
        if st.button("🚪 خروج"):
            _parent_logout()
            st.rerun()

    info = []
    if m.get("level"):
        info.append(f"🎯 المستوى: {m['level']}")
    if m.get("coach"):
        info.append(f"👤 المدرب: {m['coach']}")
    if info:
        st.markdown(" &nbsp; | &nbsp; ".join(info))

    # Membership status
    status_df = fin_svc.membership_status(conn)
    if not status_df.empty:
        row = status_df[status_df["member_id"].astype(int) == int(mid)]
        if not row.empty:
            r = row.iloc[0]
            label = _STATUS_AR.get(r["status"], r["status"])
            if r["status"] in ("expired", "expiring"):
                st.warning(f"حالة الاشتراك: {label} — تاريخ الانتهاء: {r['expiry_date']}")
            elif r["status"] == "active":
                st.success(f"حالة الاشتراك: {label} — حتى {r['expiry_date']}")
            else:
                st.info(f"حالة الاشتراك: {label}")

    summary, ev = prog_svc.member_summary(conn, int(mid))
    att = prog_svc.get_member_attendance(conn, int(mid))

    st.markdown("---")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📋 عدد التقييمات", summary["count"])
    c2.metric("⭐ آخر درجة", summary["latest"] if summary["latest"] is not None else "—")
    c3.metric("🏅 أفضل درجة", summary["best"] if summary["best"] is not None else "—")
    c4.metric("📅 الحضور", len(att))

    if summary["count"] == 0:
        st.info("لا توجد تقييمات مسجّلة بعد لطفلك.")
    else:
        st.plotly_chart(charts.score_trend_plotly(ev), use_container_width=True)
        jf = charts.jump_success_plotly(ev)
        if jf:
            st.plotly_chart(jf, use_container_width=True)
        st.markdown("#### 📝 آخر التقييمات")
        show = ev.sort_values("evaluation_date", ascending=False).head(8)[
            ["evaluation_date", "evaluation_type", "total_score", "notes"]].copy()
        show.columns = ["التاريخ", "النوع", "الدرجة", "ملاحظات المدرب"]
        show.index = range(1, len(show) + 1)
        st.dataframe(show, use_container_width=True)

    af = charts.attendance_trend_plotly(att)
    if af:
        st.plotly_chart(af, use_container_width=True)

    # PDF download
    if PDF_AVAILABLE and summary["count"] > 0:
        st.markdown("---")
        if st.button("📄 توليد تقرير PDF", type="primary", key="parent_pdf"):
            with st.spinner("جاري إنشاء التقرير..."):
                try:
                    from src.utils import settings as club_settings
                    club_avg = prog_svc.get_club_average_over_time(conn)
                    pdf = build_member_progress_pdf(
                        m.to_dict(), att, ev, summary,
                        club_avg_df=club_avg, settings=club_settings.load_settings())
                    st.session_state["parent_pdf_bytes"] = pdf
                except Exception as exc:
                    st.error(f"تعذّر إنشاء التقرير: {exc}")
        if st.session_state.get("parent_pdf_bytes"):
            st.download_button("⬇️ تحميل التقرير", data=st.session_state["parent_pdf_bytes"],
                               file_name=f"تقرير_{m['name']}.pdf", mime="application/pdf")


# ─────────────────────────────────────────────────────────────
# OWNER CODE ADMIN (separate sidebar page, PIN-protected)
# ─────────────────────────────────────────────────────────────
def _owner_gate():
    """بوابة المالك لحماية صفحة الرموز. تعيد True عند السماح بالعرض."""
    if st.session_state.get("owner_unlocked"):
        return True
    if not club_cfg.has_owner_pin():
        st.warning("🔒 لحماية رموز أولياء الأمور، اضبط رمز دخول للمالك أولاً (يُطلب مرة واحدة).")
        with st.form("set_owner_pin"):
            p1 = st.text_input("رمز دخول جديد للمالك", type="password")
            p2 = st.text_input("تأكيد الرمز", type="password")
            if st.form_submit_button("حفظ رمز الدخول", type="primary"):
                if not p1 or len(p1) < 4:
                    st.error("اختر رمزاً من 4 خانات على الأقل.")
                elif p1 != p2:
                    st.error("الرمزان غير متطابقين.")
                else:
                    club_cfg.set_owner_pin(p1)
                    st.session_state["owner_unlocked"] = True
                    st.rerun()
        return False
    with st.form("owner_login"):
        pin = st.text_input("🔒 رمز دخول المالك", type="password")
        if st.form_submit_button("دخول", type="primary"):
            if club_cfg.verify_owner_pin(pin):
                st.session_state["owner_unlocked"] = True
                st.rerun()
            else:
                st.error("رمز غير صحيح.")
    return False


def show_parent_admin(get_data, execute_query, get_connection, clear_cache):
    st.title("🔑 رموز أولياء الأمور")
    conn = get_connection()
    if not _owner_gate():
        return
    st.caption("أنشئ رمز وصول لكل لاعب وشاركه مع وليّ أمره. الرمز سرّي — من يملكه يرى تقدّم الطفل.")

    members = get_data("SELECT id, name FROM members ORDER BY name")
    if members.empty:
        st.warning("أضف لاعبين أولاً من «إدارة الأعضاء».")
        return

    labels = {int(r["id"]): f'{r["name"]} (#{int(r["id"])})' for _, r in members.iterrows()}
    mid = st.selectbox("اختر اللاعب", members["id"].astype(int).tolist(),
                       format_func=lambda i: labels[i], key="padmin_sel")

    access = parent_svc.list_access(conn)
    cur = access[access["member_id"].astype(int) == int(mid)]
    has_code = not cur.empty and cur.iloc[0]["code"]

    if has_code:
        row = cur.iloc[0]
        st.code(row["code"], language=None)
        st.caption(("الحالة: 🟢 مُفعّل" if row["active"] else "الحالة: 🔴 موقوف") +
                   (f" — آخر اطلاع: {row['last_viewed_at']}" if row["last_viewed_at"] else ""))
        b1, b2, b3 = st.columns(3)
        if b1.button("🔄 تجديد الرمز"):
            parent_svc.regenerate_code(conn, mid)
            clear_cache()
            st.rerun()
        if int(row["active"]) == 1:
            if b2.button("⏸ إيقاف"):
                parent_svc.set_active(conn, mid, False)
                clear_cache()
                st.rerun()
        else:
            if b2.button("▶️ تفعيل"):
                parent_svc.set_active(conn, mid, True)
                clear_cache()
                st.rerun()
    else:
        if st.button("➕ إنشاء رمز وصول", type="primary"):
            parent_svc.get_or_create_code(conn, mid)
            clear_cache()
            st.rerun()

    st.markdown("---")
    st.markdown("#### 📋 نظرة عامة على الرموز")
    show = access.copy()
    show["الحالة"] = show["active"].apply(
        lambda a: "🟢 مُفعّل" if a == 1 else ("🔴 موقوف" if a == 0 else "— بلا رمز"))
    show["الرمز"] = show["code"].apply(lambda c: "✅ موجود" if c else "—")
    out = show[["name", "الرمز", "الحالة", "last_viewed_at"]].copy()
    out.columns = ["اللاعب", "الرمز", "الحالة", "آخر اطلاع"]
    out.index = range(1, len(out) + 1)
    st.dataframe(out, use_container_width=True)
