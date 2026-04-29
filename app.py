"""
🎿 نظام تحليل أداء لاعبي التزلج
Skating Analysis & Attendance System
"""
import streamlit as st
import pandas as pd
import sqlite3
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np

st.set_page_config(
    page_title="نظام تحليل التزلج 🎿",
    page_icon="🎿",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main {background-color: #f0f2f6;}
    .stMetric {background-color: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);}
    h1 {color: #1f77b4; text-align: center; padding: 20px 0;}
    h2 {color: #2c3e50;}
    h3 {color: #34495e;}
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 15px;
        margin: 10px 0;
    }
    .info-box {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 5px;
        padding: 15px;
        margin: 10px 0;
    }
    div[data-testid="stForm"] {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_connection():
    return sqlite3.connect('skating_database.db', check_same_thread=False)

def get_data(query, params=None):
    conn = get_connection()
    if params:
        return pd.read_sql_query(query, conn, params=params)
    return pd.read_sql_query(query, conn)

def execute_query(query, params=None):
    conn = get_connection()
    cursor = conn.cursor()
    if params:
        cursor.execute(query, params)
    else:
        cursor.execute(query)
    conn.commit()
    return cursor.lastrowid

def clear_cache():
    st.cache_resource.clear()
    st.cache_data.clear()

LEVELS = ["Alpha", "Beta", "Gamma", "Delta", "Pre-Free", "Free Skate 1", "Free Skate 2", "Free Skate 3", "Advanced"]
BUNDLES = ["On-Ice Silver", "On-Ice Bronze", "On-Ice Gold", "Off-Ice Silver", "Off-Ice Bronze", "Off-Ice Gold"]
SESSION_TYPES = ["on-ice", "off-ice", "both"]

def get_coaches():
    df = get_data("SELECT DISTINCT coach FROM members WHERE coach IS NOT NULL AND coach != '' ORDER BY coach")
    coaches = df['coach'].tolist()
    att_coaches = get_data("SELECT DISTINCT coach FROM attendance WHERE coach IS NOT NULL AND coach != '' ORDER BY coach")
    all_coaches = list(set(coaches + att_coaches['coach'].tolist()))
    all_coaches.sort()
    return all_coaches

# ───────────────────────────────────────────
# الصفحة الرئيسية
# ───────────────────────────────────────────
def show_homepage():
    st.title("🎿 نظام تحليل أداء لاعبي التزلج")
    st.markdown("### مرحباً بك في نظام إدارة وتحليل الأداء الشامل")

    members_df = get_data("SELECT * FROM members")
    attendance_df = get_data("SELECT * FROM attendance")
    memberships_df = get_data("SELECT * FROM memberships")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("👥 إجمالي الأعضاء", len(members_df))
    with col2:
        st.metric("📅 سجلات الحضور", len(attendance_df))
    with col3:
        avg_attendance = len(attendance_df) / len(members_df) if len(members_df) > 0 else 0
        st.metric("📊 متوسط الحضور", f"{avg_attendance:.1f}")
    with col4:
        st.metric("💳 العضويات النشطة", len(memberships_df))

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📈 توزيع الحضور عبر الزمن")
        if len(attendance_df) > 0:
            attendance_by_date = attendance_df.groupby('date').size().reset_index(name='count')
            attendance_by_date['date'] = pd.to_datetime(attendance_by_date['date'])
            attendance_by_date = attendance_by_date.sort_values('date')
            fig = px.line(
                attendance_by_date, x='date', y='count',
                title='عدد الحضور اليومي',
                labels={'date': 'التاريخ', 'count': 'عدد الحضور'}
            )
            fig.update_traces(line_color='#1f77b4', line_width=3)
            fig.update_layout(hovermode='x unified')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("لا توجد بيانات حضور")

    with col2:
        st.subheader("👥 توزيع المستويات")
        if len(members_df) > 0 and 'level' in members_df.columns:
            level_counts = members_df['level'].dropna()
            level_counts = level_counts[level_counts != ''].value_counts()
            if len(level_counts) > 0:
                fig = px.pie(
                    values=level_counts.values, names=level_counts.index,
                    title='توزيع الأعضاء حسب المستوى', hole=0.4
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("لا توجد بيانات مستويات")

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🏆 أعلى 10 أعضاء حضوراً")
        if len(attendance_df) > 0:
            member_attendance = attendance_df.groupby('member_id').size().reset_index(name='attendance_count')
            member_attendance = member_attendance.merge(
                members_df[['id', 'name']], left_on='member_id', right_on='id'
            )
            member_attendance = member_attendance.sort_values('attendance_count', ascending=False).head(10)
            fig = px.bar(
                member_attendance, x='name', y='attendance_count',
                title='أعلى 10 أعضاء حضوراً',
                labels={'name': 'الاسم', 'attendance_count': 'عدد الحضور'},
                color='attendance_count', color_continuous_scale='blues'
            )
            fig.update_layout(showlegend=False, xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("🎯 توزيع الحضور حسب نوع الحصة")
        if len(attendance_df) > 0 and 'session_type' in attendance_df.columns:
            session_counts = attendance_df['session_type'].value_counts()
            fig = px.pie(
                values=session_counts.values, names=session_counts.index,
                title='On-Ice vs Off-Ice', hole=0.4
            )
            st.plotly_chart(fig, use_container_width=True)


# ───────────────────────────────────────────
# صفحة إدارة الأعضاء
# ───────────────────────────────────────────
def show_members_page():
    st.title("👥 إدارة الأعضاء")

    tab1, tab2, tab3 = st.tabs(["📋 قائمة الأعضاء", "➕ إضافة عضو", "✏️ تعديل / حذف"])

    with tab1:
        members_df = get_data("SELECT * FROM members ORDER BY name")
        if len(members_df) == 0:
            st.warning("لا يوجد أعضاء في النظام")
            return

        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            search = st.text_input("🔍 بحث بالاسم", "")
        with col2:
            levels = ["الكل"] + sorted(members_df['level'].dropna().unique().tolist())
            selected_level = st.selectbox("🎯 المستوى", levels)
        with col3:
            coaches = ["الكل"] + sorted(members_df['coach'].dropna().unique().tolist())
            selected_coach = st.selectbox("👨‍🏫 المدرب", coaches)

        filtered = members_df.copy()
        if search:
            filtered = filtered[filtered['name'].str.contains(search, case=False, na=False)]
        if selected_level != "الكل":
            filtered = filtered[filtered['level'] == selected_level]
        if selected_coach != "الكل":
            filtered = filtered[filtered['coach'] == selected_coach]

        st.markdown(f"**عدد الأعضاء: {len(filtered)}**")

        # Show with attendance count
        att_counts = get_data("SELECT member_id, COUNT(*) as att_count FROM attendance GROUP BY member_id")
        if len(att_counts) > 0:
            filtered = filtered.merge(att_counts, left_on='id', right_on='member_id', how='left')
            filtered['att_count'] = filtered['att_count'].fillna(0).astype(int)
            display = filtered[['name', 'level', 'coach', 'bundle', 'att_count']].copy()
            display.columns = ['الاسم', 'المستوى', 'المدرب', 'الباقة', 'عدد الحضور']
        else:
            display = filtered[['name', 'level', 'coach', 'bundle']].copy()
            display.columns = ['الاسم', 'المستوى', 'المدرب', 'الباقة']

        display.index = range(1, len(display) + 1)
        st.dataframe(display, use_container_width=True, height=500)

    with tab2:
        st.subheader("➕ إضافة عضو جديد")
        with st.form("add_member_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("الاسم *", placeholder="أدخل اسم العضو")
                level = st.selectbox("المستوى", [""] + LEVELS)
                gender = st.selectbox("الجنس", ["", "ذكر", "أنثى"])
            with col2:
                coach = st.text_input("المدرب", placeholder="اسم المدرب")
                bundle = st.selectbox("الباقة", [""] + BUNDLES)
                birth_date = st.date_input("تاريخ الميلاد", value=None, min_value=datetime(1990, 1, 1).date())

            submitted = st.form_submit_button("✅ إضافة العضو", use_container_width=True)
            if submitted:
                if not name.strip():
                    st.error("❌ الرجاء إدخال اسم العضو")
                else:
                    existing = get_data("SELECT id FROM members WHERE name = ?", params=(name.strip(),))
                    if len(existing) > 0:
                        st.error(f"❌ العضو '{name}' موجود مسبقاً")
                    else:
                        bd_str = birth_date.strftime('%Y-%m-%d') if birth_date else None
                        execute_query(
                            "INSERT INTO members (name, gender, birth_date, level, coach, bundle) VALUES (?,?,?,?,?,?)",
                            (name.strip(), gender or None, bd_str, level or None, coach.strip() or None, bundle or None)
                        )
                        st.success(f"✅ تم إضافة العضو '{name}' بنجاح!")
                        clear_cache()

    with tab3:
        st.subheader("✏️ تعديل أو حذف عضو")
        members_df = get_data("SELECT * FROM members ORDER BY name")
        if len(members_df) == 0:
            st.info("لا يوجد أعضاء")
            return

        member_names = members_df['name'].tolist()
        selected = st.selectbox("اختر العضو", member_names, key="edit_member_select")

        if selected:
            member = members_df[members_df['name'] == selected].iloc[0]

            with st.form("edit_member_form"):
                col1, col2 = st.columns(2)
                with col1:
                    new_name = st.text_input("الاسم", value=member['name'])
                    new_level = st.selectbox("المستوى", [""] + LEVELS,
                                             index=(LEVELS.index(member['level']) + 1) if member.get('level') in LEVELS else 0)
                    new_gender = st.selectbox("الجنس", ["", "ذكر", "أنثى"],
                                              index=["", "ذكر", "أنثى"].index(member['gender']) if member.get('gender') in ["ذكر", "أنثى"] else 0)
                with col2:
                    new_coach = st.text_input("المدرب", value=member.get('coach') or "")
                    new_bundle = st.selectbox("الباقة", [""] + BUNDLES,
                                              index=(BUNDLES.index(member['bundle']) + 1) if member.get('bundle') in BUNDLES else 0)

                col_save, col_delete = st.columns(2)
                with col_save:
                    save = st.form_submit_button("💾 حفظ التعديلات", use_container_width=True)
                with col_delete:
                    delete = st.form_submit_button("🗑️ حذف العضو", use_container_width=True, type="secondary")

                if save:
                    execute_query(
                        "UPDATE members SET name=?, level=?, coach=?, gender=?, bundle=? WHERE id=?",
                        (new_name.strip(), new_level or None, new_coach.strip() or None,
                         new_gender or None, new_bundle or None, int(member['id']))
                    )
                    st.success("✅ تم حفظ التعديلات بنجاح!")
                    clear_cache()
                    st.rerun()

                if delete:
                    execute_query("DELETE FROM attendance WHERE member_id=?", (int(member['id']),))
                    execute_query("DELETE FROM memberships WHERE member_id=?", (int(member['id']),))
                    execute_query("DELETE FROM members WHERE id=?", (int(member['id']),))
                    st.success(f"✅ تم حذف العضو '{selected}' وجميع بياناته")
                    clear_cache()
                    st.rerun()


# ───────────────────────────────────────────
# صفحة تسجيل الحضور
# ───────────────────────────────────────────
def show_attendance_page():
    st.title("📅 إدارة الحضور")

    tab1, tab2, tab3 = st.tabs(["➕ تسجيل حضور", "📋 سجل الحضور", "📊 تحليل الحضور"])

    with tab1:
        st.subheader("➕ تسجيل حضور جديد")
        members_df = get_data("SELECT id, name FROM members ORDER BY name")

        if len(members_df) == 0:
            st.warning("لا يوجد أعضاء. أضف أعضاء أولاً.")
            return

        with st.form("attendance_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                selected_members = st.multiselect(
                    "👥 اختر الأعضاء (يمكن اختيار أكثر من واحد)",
                    members_df['name'].tolist()
                )
                session_date = st.date_input("📅 التاريخ", value=datetime.today())
            with col2:
                session_type = st.selectbox("🎿 نوع الحصة", SESSION_TYPES)
                coaches_list = get_coaches()
                coach_options = [""] + coaches_list + ["أخرى..."]
                coach_select = st.selectbox("👨‍🏫 المدرب", coach_options)
                if coach_select == "أخرى...":
                    coach_input = st.text_input("اسم المدرب")
                else:
                    coach_input = coach_select

            submitted = st.form_submit_button("✅ تسجيل الحضور", use_container_width=True)
            if submitted:
                if not selected_members:
                    st.error("❌ الرجاء اختيار عضو واحد على الأقل")
                else:
                    date_str = session_date.strftime('%Y-%m-%d')
                    coach_val = coach_input.strip() or None
                    added = 0
                    skipped = 0

                    for member_name in selected_members:
                        member_row = members_df[members_df['name'] == member_name]
                        if len(member_row) == 0:
                            continue
                        member_id = int(member_row.iloc[0]['id'])

                        sessions = [session_type] if session_type != "both" else ["on-ice", "off-ice"]
                        for stype in sessions:
                            existing = get_data(
                                "SELECT id FROM attendance WHERE member_id=? AND date=? AND session_type=?",
                                params=(member_id, date_str, stype)
                            )
                            if len(existing) > 0:
                                skipped += 1
                            else:
                                execute_query(
                                    "INSERT INTO attendance (member_id, date, status, session_type, coach) VALUES (?,?,?,?,?)",
                                    (member_id, date_str, 'present', stype, coach_val)
                                )
                                added += 1

                    msg = f"✅ تم تسجيل {added} سجل حضور"
                    if skipped > 0:
                        msg += f" ({skipped} موجود مسبقاً تم تجاهله)"
                    st.success(msg)
                    clear_cache()

    with tab2:
        st.subheader("📋 سجل الحضور")
        members_df = get_data("SELECT id, name FROM members ORDER BY name")

        col1, col2, col3 = st.columns(3)
        with col1:
            filter_member = st.selectbox("👥 العضو", ["الكل"] + members_df['name'].tolist(), key="att_member_filter")
        with col2:
            filter_date_from = st.date_input("من تاريخ", value=datetime(2025, 10, 1).date(), key="att_date_from")
        with col3:
            filter_date_to = st.date_input("إلى تاريخ", value=datetime.today().date(), key="att_date_to")

        query = """
            SELECT a.id, m.name as member_name, a.date, a.session_type, a.coach, a.status
            FROM attendance a
            JOIN members m ON a.member_id = m.id
            WHERE a.date >= ? AND a.date <= ?
        """
        params = [filter_date_from.strftime('%Y-%m-%d'), filter_date_to.strftime('%Y-%m-%d')]

        if filter_member != "الكل":
            member_row = members_df[members_df['name'] == filter_member]
            if len(member_row) > 0:
                query += " AND a.member_id = ?"
                params.append(int(member_row.iloc[0]['id']))

        query += " ORDER BY a.date DESC, m.name"
        att_df = get_data(query, params=params)

        st.markdown(f"**عدد السجلات: {len(att_df)}**")

        if len(att_df) > 0:
            display = att_df[['member_name', 'date', 'session_type', 'coach', 'status']].copy()
            display.columns = ['الاسم', 'التاريخ', 'نوع الحصة', 'المدرب', 'الحالة']
            display.index = range(1, len(display) + 1)
            st.dataframe(display, use_container_width=True, height=450)

            # Delete a record
            st.markdown("---")
            st.subheader("🗑️ حذف سجل حضور")
            att_id = st.number_input("أدخل رقم السجل للحذف (من عمود الـ ID)", min_value=1, step=1)
            if st.button("🗑️ حذف السجل"):
                execute_query("DELETE FROM attendance WHERE id=?", (int(att_id),))
                st.success(f"✅ تم حذف السجل رقم {att_id}")
                clear_cache()
                st.rerun()
        else:
            st.info("لا توجد سجلات في هذه الفترة")

    with tab3:
        st.subheader("📊 تحليل الحضور")
        att_df = get_data("""
            SELECT a.date, a.session_type, a.coach, m.name, m.level
            FROM attendance a
            JOIN members m ON a.member_id = m.id
            ORDER BY a.date
        """)

        if len(att_df) == 0:
            st.info("لا توجد بيانات")
            return

        att_df['date'] = pd.to_datetime(att_df['date'])
        att_df['month'] = att_df['date'].dt.to_period('M').astype(str)

        col1, col2 = st.columns(2)

        with col1:
            daily = att_df.groupby('date').size().reset_index(name='count')
            fig = px.bar(daily, x='date', y='count', title='الحضور اليومي',
                        labels={'date': 'التاريخ', 'count': 'العدد'}, color_discrete_sequence=['#1f77b4'])
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            coach_att = att_df['coach'].dropna().value_counts().head(10)
            if len(coach_att) > 0:
                fig = px.bar(x=coach_att.index, y=coach_att.values,
                            title='أعلى 10 مدربين حضوراً',
                            labels={'x': 'المدرب', 'y': 'عدد الحصص'},
                            color_discrete_sequence=['#2ca02c'])
                fig.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            session_dist = att_df['session_type'].value_counts()
            fig = px.pie(values=session_dist.values, names=session_dist.index,
                        title='On-Ice vs Off-Ice', hole=0.4)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            level_att = att_df['level'].dropna().value_counts()
            if len(level_att) > 0:
                fig = px.bar(x=level_att.index, y=level_att.values,
                            title='الحضور حسب المستوى',
                            labels={'x': 'المستوى', 'y': 'عدد الحضور'},
                            color_discrete_sequence=['#ff7f0e'])
                st.plotly_chart(fig, use_container_width=True)


# ───────────────────────────────────────────
# صفحة ملفات الأعضاء
# ───────────────────────────────────────────
def show_member_profiles_page():
    st.title("🧑‍💼 ملفات الأعضاء")

    members_df = get_data("SELECT * FROM members ORDER BY name")
    if len(members_df) == 0:
        st.warning("لا يوجد أعضاء في النظام")
        return

    col1, col2 = st.columns([1, 3])
    with col1:
        search = st.text_input("🔍 بحث", "")
    filtered_names = members_df['name'].tolist()
    if search:
        filtered_names = [n for n in filtered_names if search.lower() in n.lower()]

    if not filtered_names:
        st.info("لا توجد نتائج")
        return

    selected_member = st.selectbox("اختر عضو", filtered_names)

    if selected_member:
        member = members_df[members_df['name'] == selected_member].iloc[0]
        member_id = int(member['id'])

        st.markdown("---")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("### 📝 المعلومات الأساسية")
            st.write(f"**الاسم:** {member['name']}")
            st.write(f"**المستوى:** {member.get('level') or '—'}")
            st.write(f"**المدرب:** {member.get('coach') or '—'}")
            st.write(f"**الباقة:** {member.get('bundle') or '—'}")
            st.write(f"**الجنس:** {member.get('gender') or '—'}")

        with col2:
            st.markdown("### 📊 إحصائيات الحضور")
            attendance = get_data("SELECT * FROM attendance WHERE member_id = ?", params=(member_id,))
            total = len(attendance)
            on_ice = len(attendance[attendance['session_type'] == 'on-ice']) if total > 0 else 0
            off_ice = len(attendance[attendance['session_type'] == 'off-ice']) if total > 0 else 0

            st.metric("إجمالي الحضور", total)
            col_a, col_b = st.columns(2)
            col_a.metric("On-Ice", on_ice)
            col_b.metric("Off-Ice", off_ice)

            if total > 0:
                last_att = attendance['date'].max()
                st.write(f"**آخر حضور:** {last_att}")

        with col3:
            st.markdown("### 💳 المعلومات المالية")
            memberships = get_data("SELECT * FROM memberships WHERE member_id = ?", params=(member_id,))
            if len(memberships) > 0:
                total_paid = memberships['amount'].sum()
                total_discount = memberships['discount'].sum() if 'discount' in memberships.columns else 0
                st.metric("المدفوع", f"{total_paid:,.0f} جنيه")
                if total_discount > 0:
                    st.metric("الخصم", f"{total_discount:,.0f} جنيه")

                for _, mem in memberships.iterrows():
                    st.write(f"- {mem.get('bundle_type', '—')}: **{mem.get('amount', 0):,.0f} ج**")
            else:
                st.info("لا توجد عضوية مسجلة")

        st.markdown("---")

        if total > 0:
            st.subheader("📅 الحضور الشهري")
            attendance['date'] = pd.to_datetime(attendance['date'])
            attendance['month'] = attendance['date'].dt.to_period('M').astype(str)
            monthly = attendance.groupby(['month', 'session_type']).size().reset_index(name='count')
            fig = px.bar(monthly, x='month', y='count', color='session_type',
                        title=f'الحضور الشهري - {selected_member}',
                        labels={'month': 'الشهر', 'count': 'عدد الأيام', 'session_type': 'النوع'},
                        barmode='group')
            st.plotly_chart(fig, use_container_width=True)

            st.subheader("📜 سجل الحضور الكامل")
            display = attendance[['date', 'session_type', 'coach']].copy()
            display.columns = ['التاريخ', 'نوع الحصة', 'المدرب']
            display = display.sort_values('التاريخ', ascending=False)
            display.index = range(1, len(display) + 1)
            st.dataframe(display, use_container_width=True)


# ───────────────────────────────────────────
# صفحة التقارير
# ───────────────────────────────────────────
def show_reports_page():
    st.title("📊 التقارير والإحصائيات")

    members_df = get_data("SELECT * FROM members")
    attendance_df = get_data("SELECT * FROM attendance")
    memberships_df = get_data("SELECT * FROM memberships")

    tab1, tab2, tab3 = st.tabs(["📈 الحضور", "💰 المدفوعات", "👥 الأعضاء"])

    with tab1:
        st.subheader("تقرير الحضور")
        if len(attendance_df) > 0:
            attendance_df['date'] = pd.to_datetime(attendance_df['date'])
            attendance_df['month'] = attendance_df['date'].dt.to_period('M').astype(str)

            col1, col2 = st.columns(2)
            with col1:
                monthly_stats = attendance_df.groupby('month').size().reset_index(name='count')
                fig = px.bar(monthly_stats, x='month', y='count', title='الحضور الشهري',
                            labels={'month': 'الشهر', 'count': 'عدد الحضور'})
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                if 'coach' in attendance_df.columns:
                    coach_stats = attendance_df['coach'].dropna().value_counts().head(8)
                    if len(coach_stats) > 0:
                        fig = px.pie(values=coach_stats.values, names=coach_stats.index,
                                    title='توزيع الحضور حسب المدرب')
                        st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("لا توجد بيانات حضور")

    with tab2:
        st.subheader("تقرير المدفوعات")
        if len(memberships_df) > 0:
            col1, col2 = st.columns(2)
            with col1:
                total_revenue = memberships_df['amount'].sum()
                total_discount = memberships_df['discount'].sum() if 'discount' in memberships_df.columns else 0
                net_revenue = total_revenue - total_discount

                st.metric("إجمالي الإيرادات", f"{total_revenue:,.0f} جنيه")
                st.metric("إجمالي الخصومات", f"{total_discount:,.0f} جنيه")
                st.metric("صافي الإيرادات", f"{net_revenue:,.0f} جنيه")

            with col2:
                if 'bundle_type' in memberships_df.columns:
                    bundle_revenue = memberships_df.groupby('bundle_type')['amount'].sum().dropna()
                    bundle_revenue = bundle_revenue[bundle_revenue.index != '']
                    if len(bundle_revenue) > 0:
                        fig = px.bar(x=bundle_revenue.index, y=bundle_revenue.values,
                                    title='الإيرادات حسب الباقة',
                                    labels={'x': 'الباقة', 'y': 'المبلغ'})
                        st.plotly_chart(fig, use_container_width=True)

            # Full table
            st.subheader("📋 جدول العضويات الكامل")
            mem_with_names = get_data("""
                SELECT m.name as member_name, ms.bundle_type, ms.amount, ms.discount, ms.payment_date
                FROM memberships ms
                JOIN members m ON ms.member_id = m.id
                ORDER BY m.name
            """)
            if len(mem_with_names) > 0:
                display = mem_with_names.copy()
                display.columns = ['الاسم', 'الباقة', 'المبلغ', 'الخصم', 'تاريخ الدفع']
                display.index = range(1, len(display) + 1)
                st.dataframe(display, use_container_width=True, height=400)
        else:
            st.info("لا توجد بيانات مدفوعات")

    with tab3:
        st.subheader("تقرير الأعضاء")
        col1, col2 = st.columns(2)

        with col1:
            st.metric("إجمالي الأعضاء", len(members_df))

            if 'level' in members_df.columns:
                level_dist = members_df['level'].dropna().value_counts()
                level_dist = level_dist[level_dist.index != '']
                if len(level_dist) > 0:
                    fig = px.bar(x=level_dist.index, y=level_dist.values,
                                title='الأعضاء حسب المستوى',
                                labels={'x': 'المستوى', 'y': 'العدد'},
                                color_discrete_sequence=['#9467bd'])
                    fig.update_layout(xaxis_tickangle=-45)
                    st.plotly_chart(fig, use_container_width=True)

        with col2:
            if 'coach' in members_df.columns:
                coach_dist = members_df['coach'].dropna().value_counts()
                coach_dist = coach_dist[coach_dist.index != '']
                if len(coach_dist) > 0:
                    fig = px.pie(values=coach_dist.values, names=coach_dist.index,
                                title='الأعضاء حسب المدرب', hole=0.35)
                    st.plotly_chart(fig, use_container_width=True)


# ───────────────────────────────────────────
# القائمة الرئيسية
# ───────────────────────────────────────────
def main():
    with st.sidebar:
        st.title("🎿 القائمة الرئيسية")
        st.markdown("---")

        page = st.radio(
            "اختر الصفحة",
            [
                "🏠 الرئيسية",
                "👥 إدارة الأعضاء",
                "📅 تسجيل الحضور",
                "🧑‍💼 ملفات الأعضاء",
                "📊 التقارير والإحصائيات"
            ]
        )

        st.markdown("---")
        members_count = get_data("SELECT COUNT(*) as count FROM members")['count'].iloc[0]
        attendance_count = get_data("SELECT COUNT(*) as count FROM attendance")['count'].iloc[0]

        st.markdown("### 📊 إحصائيات سريعة")
        st.write(f"👥 الأعضاء: **{members_count}**")
        st.write(f"📅 الحضور: **{attendance_count}**")
        st.markdown("---")
        st.info("💡 نظام شامل لإدارة وتحليل أداء لاعبي التزلج")

    if page == "🏠 الرئيسية":
        show_homepage()
    elif page == "👥 إدارة الأعضاء":
        show_members_page()
    elif page == "📅 تسجيل الحضور":
        show_attendance_page()
    elif page == "🧑‍💼 ملفات الأعضاء":
        show_member_profiles_page()
    elif page == "📊 التقارير والإحصائيات":
        show_reports_page()


if __name__ == "__main__":
    main()
