"""
صفحة إدارة المسابقات - إنشاء المسابقات، تسجيل اللاعبين، وتدوين النتائج.
Competitions management. Receives DB helpers from app.py.
"""
from datetime import date

import streamlit as st

from src.competitions import service


def show_competitions_page(get_data, execute_query, get_connection, clear_cache):
    st.title("🏆 إدارة المسابقات")
    conn = get_connection()

    tab1, tab2, tab3 = st.tabs([
        "📋 المسابقات", "📝 التسجيل والنتائج", "👤 سجل اللاعب"])

    with tab1:
        _list_create(conn, clear_cache)
    with tab2:
        _manage(conn, get_data, clear_cache)
    with tab3:
        _member_history(conn, get_data)


def _list_create(conn, clear_cache):
    with st.expander("➕ إنشاء مسابقة جديدة", expanded=False):
        with st.form("new_comp", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                name = st.text_input("اسم المسابقة")
                comp_date = st.date_input("التاريخ", value=date.today())
                level = st.text_input("المستوى / الفئة", "")
            with c2:
                location = st.text_input("المكان", "")
                notes = st.text_area("ملاحظات", "")
            if st.form_submit_button("💾 حفظ المسابقة", type="primary"):
                if not name.strip():
                    st.error("اكتب اسم المسابقة.")
                else:
                    service.create_competition(conn, name, comp_date.strftime("%Y-%m-%d"),
                                               location or None, level or None, notes or None)
                    clear_cache()
                    st.success("✅ تم إنشاء المسابقة.")
                    st.rerun()

    st.markdown("#### 📋 المسابقات المسجّلة")
    df = service.list_competitions(conn)
    if df.empty:
        st.info("لا توجد مسابقات بعد.")
        return
    show = df[["name", "comp_date", "location", "level", "entries"]].copy()
    show.columns = ["المسابقة", "التاريخ", "المكان", "المستوى", "عدد المشاركين"]
    show.index = range(1, len(show) + 1)
    st.dataframe(show, use_container_width=True)

    with st.expander("🗑 حذف مسابقة"):
        ids = df["id"].astype(int).tolist()
        labels = {int(r["id"]): f'{r["name"]} ({r["comp_date"]})' for _, r in df.iterrows()}
        cid = st.selectbox("اختر المسابقة", ids, format_func=lambda i: labels[i], key="comp_del")
        st.caption("سيُحذف معها كل تسجيلات ونتائج اللاعبين.")
        if st.button("🗑 حذف المسابقة", type="secondary"):
            service.delete_competition(conn, cid)
            clear_cache()
            st.success("تم الحذف.")
            st.rerun()


def _manage(conn, get_data, clear_cache):
    comps = service.list_competitions(conn)
    if comps.empty:
        st.info("أنشئ مسابقة أولاً من تبويب «📋 المسابقات».")
        return
    ids = comps["id"].astype(int).tolist()
    labels = {int(r["id"]): f'{r["name"]} ({r["comp_date"]})' for _, r in comps.iterrows()}
    cid = st.selectbox("اختر المسابقة", ids, format_func=lambda i: labels[i], key="comp_manage")

    st.markdown("##### ➕ تسجيل لاعبين")
    members = get_data("SELECT id, name FROM members ORDER BY name")
    entries = service.list_entries(conn, cid)
    cc1, cc2 = st.columns([3, 1])
    with cc2:
        seg = st.selectbox("الشوط", list(service.SEGMENTS.keys()),
                           format_func=lambda s: service.SEGMENTS[s], key="comp_seg")
    # استبعد فقط من سُجّلوا في هذا الشوط (يُسمح بالتسجيل في أكثر من شوط)
    if entries.empty:
        entered_ids = set()
    else:
        entered_ids = set(entries[entries["segment"] == seg]["member_id"].astype(int).tolist())
    avail = members[~members["id"].astype(int).isin(entered_ids)]
    with cc1:
        if avail.empty:
            st.caption("كل اللاعبين مسجّلون في هذا الشوط.")
            pick = []
        else:
            mlabels = {int(r["id"]): r["name"] for _, r in avail.iterrows()}
            pick = st.multiselect("اختر لاعبين", avail["id"].astype(int).tolist(),
                                  format_func=lambda i: mlabels[i], key="comp_pick")
    if st.button("➕ تسجيل المختارين", type="primary", disabled=not pick):
        for m in pick:
            service.add_entry(conn, cid, m, seg)
        clear_cache()
        st.success(f"تم تسجيل {len(pick)} لاعب.")
        st.rerun()

    st.markdown("##### 🏅 النتائج / الترتيب")
    entries = service.list_entries(conn, cid)
    if entries.empty:
        st.info("لا يوجد لاعبون مسجّلون بعد.")
        return
    disp = entries.copy()
    disp["الشوط"] = disp["segment"].map(lambda s: service.SEGMENTS.get(s, s))
    disp = disp[["name", "level", "الشوط", "rank", "score"]]
    disp.columns = ["اللاعب", "المستوى", "الشوط", "الترتيب", "النقاط"]
    disp.index = range(1, len(disp) + 1)
    st.dataframe(disp, use_container_width=True)

    with st.expander("✏️ تدوين نتيجة لاعب"):
        elabels = {int(r["id"]): f'{r["name"]} — {service.SEGMENTS.get(r["segment"], r["segment"])}'
                   for _, r in entries.iterrows()}
        eid = st.selectbox("اختر اللاعب", entries["id"].astype(int).tolist(),
                           format_func=lambda i: elabels[i], key="comp_entry")
        r1, r2 = st.columns(2)
        rank = r1.number_input("الترتيب", min_value=0, value=0, step=1,
                               help="اترك 0 إذا لم يُحدَّد بعد")
        score = r2.number_input("النقاط", min_value=0.0, value=0.0, step=0.5)
        enotes = st.text_input("ملاحظات", "", key="comp_enotes")
        if st.button("💾 حفظ النتيجة", type="primary"):
            service.update_result(conn, eid, rank=rank, score=(score if score > 0 else None),
                                  notes=enotes or None)
            clear_cache()
            st.success("تم حفظ النتيجة.")
            st.rerun()
        if st.button("🗑 إلغاء تسجيل هذا اللاعب", type="secondary"):
            service.delete_entry(conn, eid)
            clear_cache()
            st.success("تم الإلغاء.")
            st.rerun()


def _member_history(conn, get_data):
    members = get_data("SELECT id, name FROM members ORDER BY name")
    if members.empty:
        st.info("لا يوجد لاعبون.")
        return
    labels = {int(r["id"]): f'{r["name"]} (#{int(r["id"])})' for _, r in members.iterrows()}
    mid = st.selectbox("اختر اللاعب", members["id"].astype(int).tolist(),
                       format_func=lambda i: labels[i], key="comp_hist")
    hist = service.member_history(conn, mid)
    if hist.empty:
        st.info("لا توجد مشاركات لهذا اللاعب.")
        return
    show = hist.copy()
    show["segment"] = show["segment"].map(lambda s: service.SEGMENTS.get(s, s))
    show.columns = ["المسابقة", "التاريخ", "المكان", "الشوط", "الترتيب", "النقاط"]
    show.index = range(1, len(show) + 1)
    st.dataframe(show, use_container_width=True)
