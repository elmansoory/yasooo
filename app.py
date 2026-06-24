"""
🎿 نظام تحليل أداء لاعبي التزلج - النسخة الاحترافية
Skating Analysis & Attendance System - Professional Edition
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
    h1 {color: #1f77b4; text-align: center; padding: 20px 0;}
    h2 {color: #2c3e50;}
    h3 {color: #34495e;}
    div[data-testid="stForm"] {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
    .element-card {
        background: white;
        border-radius: 8px;
        padding: 12px 16px;
        margin: 6px 0;
        border-left: 4px solid #1f77b4;
        box-shadow: 0 1px 4px rgba(0,0,0,0.07);
    }
    .drill-card {
        background: #f8f9ff;
        border-radius: 8px;
        padding: 14px;
        margin: 8px 0;
        border: 1px solid #d0d8f0;
    }
    .champion-box {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        color: white;
        border-radius: 12px;
        padding: 24px;
        margin: 12px 0;
        text-align: center;
    }
    .goe-positive {background-color: #d4edda; border-radius:4px; padding:4px 8px; color:#155724;}
    .goe-negative {background-color: #f8d7da; border-radius:4px; padding:4px 8px; color:#721c24;}
    .score-badge {
        background: #1f77b4; color: white;
        border-radius: 20px; padding: 4px 14px;
        font-weight: bold; font-size: 1.1em;
    }
</style>
""", unsafe_allow_html=True)

# ─── DB HELPERS ───────────────────────────────────────────────────────
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
    att = get_data("SELECT DISTINCT coach FROM attendance WHERE coach IS NOT NULL AND coach != '' ORDER BY coach")
    return sorted(list(set(coaches + att['coach'].tolist())))


# ═══════════════════════════════════════════════════════════════════
# 🏠 الصفحة الرئيسية
# ═══════════════════════════════════════════════════════════════════
def show_homepage():
    st.title("🎿 نظام تحليل أداء لاعبي التزلج")
    st.markdown("### مرحباً بك في النظام الاحترافي الشامل لصناعة البطل")

    members_df = get_data("SELECT * FROM members")
    attendance_df = get_data("SELECT * FROM attendance")
    memberships_df = get_data("SELECT * FROM memberships")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("👥 الأعضاء", len(members_df))
    c2.metric("📅 سجلات الحضور", len(attendance_df))
    c3.metric("📊 متوسط الحضور", f"{len(attendance_df)/max(len(members_df),1):.1f}")
    c4.metric("💳 العضويات", len(memberships_df))

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📈 الحضور اليومي")
        if len(attendance_df) > 0:
            att_by_date = attendance_df.groupby('date').size().reset_index(name='count')
            att_by_date['date'] = pd.to_datetime(att_by_date['date'])
            att_by_date = att_by_date.sort_values('date')
            fig = px.line(att_by_date, x='date', y='count', title='عدد الحضور اليومي',
                         labels={'date': 'التاريخ', 'count': 'عدد الحضور'})
            fig.update_traces(line_color='#1f77b4', line_width=3)
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("👥 توزيع المستويات")
        if len(members_df) > 0:
            level_counts = members_df['level'].dropna()
            level_counts = level_counts[level_counts != ''].value_counts()
            if len(level_counts) > 0:
                fig = px.pie(values=level_counts.values, names=level_counts.index,
                            title='توزيع الأعضاء حسب المستوى', hole=0.4)
                st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🏆 أعلى 10 أعضاء حضوراً")
        if len(attendance_df) > 0:
            member_att = attendance_df.groupby('member_id').size().reset_index(name='count')
            member_att = member_att.merge(members_df[['id','name']], left_on='member_id', right_on='id')
            member_att = member_att.sort_values('count', ascending=False).head(10)
            fig = px.bar(member_att, x='name', y='count', color='count', color_continuous_scale='blues')
            fig.update_layout(showlegend=False, xaxis_tickangle=-40,
                             xaxis_title="", yaxis_title="عدد الحضور")
            st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.subheader("🎯 On-Ice vs Off-Ice")
        if len(attendance_df) > 0 and 'session_type' in attendance_df.columns:
            s = attendance_df['session_type'].value_counts()
            fig = px.pie(values=s.values, names=s.index, hole=0.4)
            st.plotly_chart(fig, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════
# 👥 إدارة الأعضاء
# ═══════════════════════════════════════════════════════════════════
def show_members_page():
    st.title("👥 إدارة الأعضاء")
    tab1, tab2, tab3 = st.tabs(["📋 قائمة الأعضاء", "➕ إضافة عضو", "✏️ تعديل / حذف"])

    with tab1:
        members_df = get_data("SELECT * FROM members ORDER BY name")
        c1, c2, c3 = st.columns(3)
        search = c1.text_input("🔍 بحث", "")
        levels = ["الكل"] + sorted(members_df['level'].dropna().unique().tolist())
        sel_level = c2.selectbox("المستوى", levels)
        coaches = ["الكل"] + sorted(members_df['coach'].dropna().unique().tolist())
        sel_coach = c3.selectbox("المدرب", coaches)

        filtered = members_df.copy()
        if search:
            filtered = filtered[filtered['name'].str.contains(search, case=False, na=False)]
        if sel_level != "الكل":
            filtered = filtered[filtered['level'] == sel_level]
        if sel_coach != "الكل":
            filtered = filtered[filtered['coach'] == sel_coach]

        att_c = get_data("SELECT member_id, COUNT(*) as att_count FROM attendance GROUP BY member_id")
        if len(att_c) > 0:
            filtered = filtered.merge(att_c, left_on='id', right_on='member_id', how='left')
            filtered['att_count'] = filtered['att_count'].fillna(0).astype(int)
            disp = filtered[['name','level','coach','bundle','att_count']].copy()
            disp.columns = ['الاسم','المستوى','المدرب','الباقة','عدد الحضور']
        else:
            disp = filtered[['name','level','coach','bundle']].copy()
            disp.columns = ['الاسم','المستوى','المدرب','الباقة']
        disp.index = range(1, len(disp)+1)
        st.markdown(f"**{len(filtered)} عضو**")
        st.dataframe(disp, use_container_width=True, height=500)

    with tab2:
        st.subheader("➕ إضافة عضو جديد")
        with st.form("add_member_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            name = c1.text_input("الاسم *")
            level = c1.selectbox("المستوى", [""]+LEVELS)
            gender = c1.selectbox("الجنس", ["","ذكر","أنثى"])
            coach = c2.text_input("المدرب")
            bundle = c2.selectbox("الباقة", [""]+BUNDLES)
            birth_date = c2.date_input("تاريخ الميلاد", value=None, min_value=datetime(1990,1,1).date())
            if st.form_submit_button("✅ إضافة", use_container_width=True):
                if not name.strip():
                    st.error("الرجاء إدخال الاسم")
                elif len(get_data("SELECT id FROM members WHERE name=?", (name.strip(),))) > 0:
                    st.error(f"العضو '{name}' موجود مسبقاً")
                else:
                    bd = birth_date.strftime('%Y-%m-%d') if birth_date else None
                    execute_query("INSERT INTO members (name,gender,birth_date,level,coach,bundle) VALUES (?,?,?,?,?,?)",
                                  (name.strip(), gender or None, bd, level or None, coach.strip() or None, bundle or None))
                    st.success(f"✅ تم إضافة '{name}'")
                    clear_cache()

    with tab3:
        st.subheader("✏️ تعديل أو حذف عضو")
        members_df = get_data("SELECT * FROM members ORDER BY name")
        selected = st.selectbox("اختر العضو", members_df['name'].tolist())
        if selected:
            member = members_df[members_df['name'] == selected].iloc[0]
            with st.form("edit_form"):
                c1, c2 = st.columns(2)
                new_name = c1.text_input("الاسم", value=member['name'])
                new_level = c1.selectbox("المستوى", [""]+LEVELS,
                    index=(LEVELS.index(member['level'])+1) if member.get('level') in LEVELS else 0)
                new_gender = c1.selectbox("الجنس", ["","ذكر","أنثى"],
                    index=["","ذكر","أنثى"].index(member['gender']) if member.get('gender') in ["ذكر","أنثى"] else 0)
                new_coach = c2.text_input("المدرب", value=member.get('coach') or "")
                new_bundle = c2.selectbox("الباقة", [""]+BUNDLES,
                    index=(BUNDLES.index(member['bundle'])+1) if member.get('bundle') in BUNDLES else 0)
                cs, cd = st.columns(2)
                save = cs.form_submit_button("💾 حفظ", use_container_width=True)
                delete = cd.form_submit_button("🗑️ حذف", use_container_width=True)
                if save:
                    execute_query("UPDATE members SET name=?,level=?,coach=?,gender=?,bundle=? WHERE id=?",
                                  (new_name.strip(), new_level or None, new_coach.strip() or None,
                                   new_gender or None, new_bundle or None, int(member['id'])))
                    st.success("✅ تم الحفظ"); clear_cache(); st.rerun()
                if delete:
                    execute_query("DELETE FROM attendance WHERE member_id=?", (int(member['id']),))
                    execute_query("DELETE FROM memberships WHERE member_id=?", (int(member['id']),))
                    execute_query("DELETE FROM members WHERE id=?", (int(member['id']),))
                    st.success(f"✅ تم حذف '{selected}'"); clear_cache(); st.rerun()


# ═══════════════════════════════════════════════════════════════════
# 📅 تسجيل الحضور
# ═══════════════════════════════════════════════════════════════════
def show_attendance_page():
    st.title("📅 إدارة الحضور")
    tab1, tab2, tab3 = st.tabs(["➕ تسجيل حضور", "📋 سجل الحضور", "📊 تحليل"])

    with tab1:
        members_df = get_data("SELECT id, name FROM members ORDER BY name")
        with st.form("att_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            sel_members = c1.multiselect("👥 الأعضاء (متعدد)", members_df['name'].tolist())
            sess_date = c1.date_input("📅 التاريخ", value=datetime.today())
            sess_type = c2.selectbox("🎿 نوع الحصة", SESSION_TYPES)
            coaches_list = get_coaches()
            coach_opt = c2.selectbox("👨‍🏫 المدرب", [""]+coaches_list+["أخرى..."])
            coach_in = c2.text_input("اسم المدرب (إذا اخترت أخرى)") if coach_opt == "أخرى..." else coach_opt
            if st.form_submit_button("✅ تسجيل الحضور", use_container_width=True):
                if not sel_members:
                    st.error("اختر عضواً واحداً على الأقل")
                else:
                    date_str = sess_date.strftime('%Y-%m-%d')
                    added = skipped = 0
                    for mn in sel_members:
                        mid = int(members_df[members_df['name']==mn].iloc[0]['id'])
                        for stype in ([sess_type] if sess_type != "both" else ["on-ice","off-ice"]):
                            if len(get_data("SELECT id FROM attendance WHERE member_id=? AND date=? AND session_type=?",
                                           (mid, date_str, stype))) > 0:
                                skipped += 1
                            else:
                                execute_query("INSERT INTO attendance (member_id,date,status,session_type,coach) VALUES (?,?,?,?,?)",
                                             (mid, date_str, 'present', stype, coach_in.strip() or None))
                                added += 1
                    st.success(f"✅ تم تسجيل {added} سجل" + (f" ({skipped} موجود مسبقاً)" if skipped else ""))
                    clear_cache()

    with tab2:
        members_df = get_data("SELECT id, name FROM members ORDER BY name")
        c1, c2, c3 = st.columns(3)
        filter_member = c1.selectbox("العضو", ["الكل"]+members_df['name'].tolist())
        date_from = c2.date_input("من", value=datetime(2025,10,1).date())
        date_to = c3.date_input("إلى", value=datetime.today().date())

        q = """SELECT a.id, m.name, a.date, a.session_type, a.coach
               FROM attendance a JOIN members m ON a.member_id=m.id
               WHERE a.date>=? AND a.date<=?"""
        params = [date_from.strftime('%Y-%m-%d'), date_to.strftime('%Y-%m-%d')]
        if filter_member != "الكل":
            mid = int(members_df[members_df['name']==filter_member].iloc[0]['id'])
            q += " AND a.member_id=?"
            params.append(mid)
        q += " ORDER BY a.date DESC"
        att_df = get_data(q, params=params)

        st.markdown(f"**{len(att_df)} سجل**")
        if len(att_df) > 0:
            disp = att_df[['name','date','session_type','coach']].copy()
            disp.columns = ['الاسم','التاريخ','نوع الحصة','المدرب']
            disp.index = range(1, len(disp)+1)
            st.dataframe(disp, use_container_width=True, height=450)

    with tab3:
        att_df = get_data("""SELECT a.date, a.session_type, a.coach, m.name, m.level
                             FROM attendance a JOIN members m ON a.member_id=m.id""")
        if len(att_df) == 0:
            st.info("لا توجد بيانات"); return
        att_df['date'] = pd.to_datetime(att_df['date'])
        c1, c2 = st.columns(2)
        with c1:
            daily = att_df.groupby('date').size().reset_index(name='count')
            fig = px.bar(daily, x='date', y='count', title='الحضور اليومي')
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            coach_att = att_df['coach'].dropna().value_counts().head(10)
            if len(coach_att) > 0:
                fig = px.bar(x=coach_att.index, y=coach_att.values, title='الحضور حسب المدرب')
                fig.update_layout(xaxis_tickangle=-40)
                st.plotly_chart(fig, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════
# 🧑‍💼 ملفات الأعضاء
# ═══════════════════════════════════════════════════════════════════
def show_member_profiles_page():
    st.title("🧑‍💼 ملفات الأعضاء")
    members_df = get_data("SELECT * FROM members ORDER BY name")
    if len(members_df) == 0:
        st.warning("لا يوجد أعضاء"); return

    search = st.text_input("🔍 بحث", "")
    names = members_df['name'].tolist()
    if search:
        names = [n for n in names if search.lower() in n.lower()]
    if not names:
        st.info("لا توجد نتائج"); return

    selected = st.selectbox("اختر عضو", names)
    if selected:
        member = members_df[members_df['name']==selected].iloc[0]
        mid = int(member['id'])
        st.markdown("---")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("### 📝 المعلومات")
            st.write(f"**الاسم:** {member['name']}")
            st.write(f"**المستوى:** {member.get('level') or '—'}")
            st.write(f"**المدرب:** {member.get('coach') or '—'}")
            st.write(f"**الباقة:** {member.get('bundle') or '—'}")
        with c2:
            att = get_data("SELECT * FROM attendance WHERE member_id=?", (mid,))
            st.markdown("### 📊 الحضور")
            st.metric("الإجمالي", len(att))
            if len(att) > 0:
                oi = len(att[att['session_type']=='on-ice'])
                ofi = len(att[att['session_type']=='off-ice'])
                ca, cb = st.columns(2)
                ca.metric("On-Ice", oi)
                cb.metric("Off-Ice", ofi)
                st.write(f"**آخر حضور:** {att['date'].max()}")
        with c3:
            mems = get_data("SELECT * FROM memberships WHERE member_id=?", (mid,))
            st.markdown("### 💳 المالية")
            if len(mems) > 0:
                st.metric("المدفوع", f"{mems['amount'].sum():,.0f} جنيه")
                for _, m in mems.iterrows():
                    st.write(f"- {m.get('bundle_type','—')}: **{m.get('amount',0):,.0f} ج**")

        if len(att) > 0:
            st.markdown("---")
            att['date'] = pd.to_datetime(att['date'])
            att['month'] = att['date'].dt.to_period('M').astype(str)
            monthly = att.groupby(['month','session_type']).size().reset_index(name='count')
            fig = px.bar(monthly, x='month', y='count', color='session_type',
                        title=f'الحضور الشهري - {selected}', barmode='group')
            st.plotly_chart(fig, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════
# 📊 التقارير
# ═══════════════════════════════════════════════════════════════════
def show_reports_page():
    st.title("📊 التقارير والإحصائيات")
    members_df = get_data("SELECT * FROM members")
    attendance_df = get_data("SELECT * FROM attendance")
    memberships_df = get_data("SELECT * FROM memberships")
    tab1, tab2, tab3 = st.tabs(["📈 الحضور","💰 المدفوعات","👥 الأعضاء"])

    with tab1:
        if len(attendance_df) > 0:
            attendance_df['date'] = pd.to_datetime(attendance_df['date'])
            attendance_df['month'] = attendance_df['date'].dt.to_period('M').astype(str)
            c1, c2 = st.columns(2)
            with c1:
                m = attendance_df.groupby('month').size().reset_index(name='count')
                fig = px.bar(m, x='month', y='count', title='الحضور الشهري')
                st.plotly_chart(fig, use_container_width=True)
            with c2:
                if 'coach' in attendance_df.columns:
                    cs = attendance_df['coach'].dropna().value_counts().head(8)
                    if len(cs) > 0:
                        fig = px.pie(values=cs.values, names=cs.index, title='الحضور حسب المدرب')
                        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        if len(memberships_df) > 0:
            c1, c2 = st.columns(2)
            with c1:
                st.metric("الإيرادات", f"{memberships_df['amount'].sum():,.0f} جنيه")
                disc = memberships_df['discount'].sum() if 'discount' in memberships_df.columns else 0
                st.metric("الخصومات", f"{disc:,.0f} جنيه")
                st.metric("الصافي", f"{memberships_df['amount'].sum()-disc:,.0f} جنيه")
            with c2:
                if 'bundle_type' in memberships_df.columns:
                    br = memberships_df.groupby('bundle_type')['amount'].sum()
                    fig = px.bar(x=br.index, y=br.values, title='الإيرادات حسب الباقة')
                    st.plotly_chart(fig, use_container_width=True)
            mn = get_data("""SELECT m.name, ms.bundle_type, ms.amount, ms.discount, ms.payment_date
                             FROM memberships ms JOIN members m ON ms.member_id=m.id ORDER BY m.name""")
            mn.columns = ['الاسم','الباقة','المبلغ','الخصم','تاريخ الدفع']
            mn.index = range(1, len(mn)+1)
            st.dataframe(mn, use_container_width=True, height=350)

    with tab3:
        c1, c2 = st.columns(2)
        with c1:
            st.metric("الأعضاء", len(members_df))
            ld = members_df['level'].dropna().value_counts()
            if len(ld) > 0:
                fig = px.bar(x=ld.index, y=ld.values, title='الأعضاء حسب المستوى',
                            color_discrete_sequence=['#9467bd'])
                fig.update_layout(xaxis_tickangle=-40)
                st.plotly_chart(fig, use_container_width=True)
        with c2:
            cd = members_df['coach'].dropna().value_counts()
            if len(cd) > 0:
                fig = px.pie(values=cd.values, names=cd.index, title='الأعضاء حسب المدرب', hole=0.35)
                st.plotly_chart(fig, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════
# 🏆 نظام التدريب الاحترافي - صناعة البطل
# ═══════════════════════════════════════════════════════════════════
def show_coaching_hub():
    from src.coaching.isu_data import (JUMPS, SPINS, STEP_SEQUENCES,
                                        GOE_CRITERIA_JUMPS, PROGRAM_COMPONENTS,
                                        LEVEL_PROGRESSION, JUDGING_RULES, INJURY_PREVENTION)
    from src.coaching.training_generator import (OFF_ICE_EXERCISES, ON_ICE_DRILLS,
                                                   generate_weekly_plan, generate_monthly_plan,
                                                   calculate_program_score)

    st.title("🏆 نظام التدريب الاحترافي — صناعة البطل العالمي")
    st.markdown("""
    <div class="champion-box">
        <h2 style="color:gold; margin:0;">🥇 من الجليد إلى منصة التتويج العالمي</h2>
        <p style="color:#ccc; margin-top:8px; font-size:1.05em;">
        نظام تدريب شامل مبني على معايير الاتحاد الدولي للتزلج (ISU) — تحليل الأداء، برامج التدريب، دليل المحكمين
        </p>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📋 مولّد برامج التدريب",
        "💪 مكتبة التمارين",
        "⚡ حاسبة النقاط ISU",
        "📖 دليل المحكمين",
        "🎯 مسار البطولة",
        "🔬 تحليل الأداء",
    ])

    # ── TAB 1: Training Program Generator ──────────────────────────
    with tab1:
        st.subheader("📋 مولّد برنامج التدريب الأسبوعي والشهري")
        col1, col2, col3 = st.columns(3)
        with col1:
            selected_level = st.selectbox("🎯 مستوى اللاعب", list(LEVEL_PROGRESSION.keys()) + ["Advanced"])
        with col2:
            goal = st.selectbox("🏆 الهدف", [
                "التحضير لمنافسة محلية",
                "التحضير لمنافسة إقليمية",
                "التحضير لبطولة وطنية",
                "التحضير للـ Grand Prix",
                "التحضير للبطولة العالمية",
                "رفع مستوى التقنية",
                "بناء اللياقة واللجسم",
            ])
        with col3:
            sessions = st.slider("حصص على الجليد في الأسبوع", 3, 7, 6)

        if st.button("🚀 توليد البرنامج الأسبوعي", use_container_width=True, type="primary"):
            plan = generate_weekly_plan(selected_level, goal, sessions)

            st.markdown("---")
            st.markdown(f"### 📅 البرنامج الأسبوعي — المستوى: **{selected_level}** | الهدف: **{goal}**")

            for day, content in plan.items():
                with st.expander(f"**{day}** — {content['focus_ar']}", expanded=False):
                    c1, c2 = st.columns(2)
                    with c1:
                        on_ice = content.get('on_ice', {})
                        dur = on_ice.get('duration', 0)
                        if dur > 0:
                            st.markdown(f"#### 🧊 على الجليد ({dur} دقيقة)")
                            for s in on_ice.get('sessions', []):
                                st.markdown(f"""<div class="element-card">
                                    <b>⏱ {s['time']}</b> &nbsp; {s['activity_ar']}
                                </div>""", unsafe_allow_html=True)
                        else:
                            st.info("🧊 يوم راحة من الجليد")
                    with c2:
                        off_ice = content.get('off_ice', {})
                        dur2 = off_ice.get('duration', 0)
                        if dur2 > 0:
                            st.markdown(f"#### 🏋️ خارج الجليد ({dur2} دقيقة)")
                            for s in off_ice.get('sessions', []):
                                st.markdown(f"""<div class="drill-card">
                                    <b>⏱ {s['time']}</b> &nbsp; {s['activity_ar']}
                                </div>""", unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("📆 خطة التدوير الشهرية (Periodization)")
        if st.button("📆 توليد الخطة الشهرية", use_container_width=True):
            phases = generate_monthly_plan(selected_level)
            cols = st.columns(4)
            for i, phase in enumerate(phases):
                with cols[i]:
                    color = ["#2196F3","#FF9800","#F44336","#4CAF50"][i]
                    st.markdown(f"""
                    <div style="background:{color}22; border:2px solid {color}; border-radius:10px; padding:16px; text-align:center; height:260px;">
                        <h4 style="color:{color}">الأسبوع {phase['week']}</h4>
                        <h5>{phase['name_ar']}</h5>
                        <p><b>الشدة:</b> {phase['intensity']}</p>
                        <p style="font-size:0.9em">{phase['focus_ar']}</p>
                    </div>""", unsafe_allow_html=True)
                    for pr in phase['priority_elements_ar']:
                        st.write(f"• {pr}")

    # ── TAB 2: Drills Library with Media ───────────────────────────
    with tab2:
        import streamlit.components.v1 as components
        from src.coaching.media_data import get_media, yt_search_embed, yt_search_url, EXERCISE_MEDIA

        def render_exercise_card(ex_dict, icon="🎯", extra_fields=None):
            """Render an exercise card with image, video embed and links"""
            name = ex_dict.get('name_ar', '')
            media = get_media(name)

            with st.expander(f"{icon} {name}"):
                # Top row: info + thumbnail
                col_info, col_thumb = st.columns([3, 2])
                with col_info:
                    for field_key, field_label in (extra_fields or []):
                        val = ex_dict.get(field_key)
                        if val:
                            st.markdown(f"**{field_label}** {val}")
                with col_thumb:
                    if media and media.get('image_url'):
                        try:
                            st.image(media['image_url'], use_container_width=True)
                        except:
                            pass

                if media:
                    # YouTube embed (search playlist)
                    embed_query = media.get('embed_query', name)
                    import urllib.parse
                    encoded = urllib.parse.quote_plus(embed_query)
                    embed_url = f"https://www.youtube.com/embed?listType=search&list={encoded}&autoplay=0"
                    components.html(
                        f'<iframe width="100%" height="230" src="{embed_url}" '
                        f'frameborder="0" allowfullscreen style="border-radius:8px;"></iframe>',
                        height=240,
                    )
                    # Source links
                    links_html = '<div style="margin-top:8px; display:flex; flex-wrap:wrap; gap:6px;">'
                    for src in media.get('sources', []):
                        links_html += (
                            f'<a href="{src["url"]}" target="_blank" style="'
                            f'padding:6px 14px; background:#1f77b4; color:white; '
                            f'border-radius:20px; text-decoration:none; font-size:0.82em; '
                            f'font-weight:bold;">{src["label"]}</a>'
                        )
                    links_html += '</div>'
                    st.markdown(links_html, unsafe_allow_html=True)
                else:
                    # Fallback: generic YouTube search button
                    search_url = yt_search_url(f"figure skating {name}")
                    st.markdown(
                        f'<a href="{search_url}" target="_blank" style="'
                        f'padding:7px 16px; background:#ff0000; color:white; '
                        f'border-radius:20px; text-decoration:none; font-size:0.85em; '
                        f'font-weight:bold;">▶ بحث على YouTube</a>',
                        unsafe_allow_html=True
                    )

        st.subheader("💪 مكتبة التمارين — مع صور وفيديوهات تعليمية")
        st.info("🎬 كل تمرين مرفق بفيديو تعليمي مضمّن من YouTube وروابط مصادر متعددة")

        drill_tab = st.radio("اختر النوع", [
            "🧊 على الجليد — قفزات",
            "🌀 على الجليد — سبينات",
            "🦶 على الجليد — خطوات",
            "🏋️ خارج الجليد — قوة",
            "🤸 خارج الجليد — مرونة",
            "❤️ خارج الجليد — لياقة",
            "⚖️ توازن وتنسيق",
            "🧠 تدريب ذهني",
        ], horizontal=True)

        if "قفزات" in drill_tab:
            level_cat = st.selectbox("مستوى التمارين", ["Alpha_Beta","Gamma_Delta","Advanced"])
            drills = ON_ICE_DRILLS['jump_drills'].get(level_cat, [])
            for d in drills:
                render_exercise_card(d, icon="🎯", extra_fields=[
                    ("description_ar", "📝 الشرح:"),
                    ("focus_ar", "🎯 التركيز:"),
                    ("duration_ar", "⏱ المدة:"),
                ])

        elif "سبينات" in drill_tab:
            for d in ON_ICE_DRILLS['spin_drills']:
                render_exercise_card(d, icon="🌀", extra_fields=[
                    ("description_ar", "📝 الشرح:"),
                    ("focus_ar", "🎯 التركيز:"),
                    ("duration_ar", "⏱ المدة:"),
                ])

        elif "خطوات" in drill_tab:
            for d in ON_ICE_DRILLS['steps_and_skating']:
                render_exercise_card(d, icon="🦶", extra_fields=[
                    ("description_ar", "📝 الشرح:"),
                    ("focus_ar", "🎯 التركيز:"),
                    ("duration_ar", "⏱ المدة:"),
                ])

        elif "قوة" in drill_tab:
            for ex in OFF_ICE_EXERCISES['strength']:
                render_exercise_card(ex, icon="🏋️", extra_fields=[
                    ("target_ar", "💪 العضلات:"),
                    ("skating_benefit_ar", "⛸ الفائدة:"),
                    ("technique_ar", "📋 التقنية:"),
                    ("sets", "🔢 المجموعات:"),
                    ("reps", "🔁 التكرار:"),
                ])

        elif "مرونة" in drill_tab:
            for ex in OFF_ICE_EXERCISES['flexibility']:
                render_exercise_card(ex, icon="🤸", extra_fields=[
                    ("target_ar", "🎯 المنطقة:"),
                    ("skating_benefit_ar", "⛸ الفائدة:"),
                    ("technique_ar", "📋 التقنية:"),
                    ("duration_ar", "⏱ المدة:"),
                ])

        elif "لياقة" in drill_tab:
            for ex in OFF_ICE_EXERCISES['cardio']:
                render_exercise_card(ex, icon="❤️", extra_fields=[
                    ("protocol_ar", "📋 البروتوكول:"),
                    ("skating_benefit_ar", "⛸ الفائدة:"),
                    ("duration_ar", "⏱ المدة:"),
                ])

        elif "توازن" in drill_tab:
            for ex in OFF_ICE_EXERCISES['balance_coordination']:
                render_exercise_card(ex, icon="⚖️", extra_fields=[
                    ("target_ar", "🎯 المستهدف:"),
                    ("skating_benefit_ar", "⛸ الفائدة:"),
                    ("duration_ar", "⏱ المدة:"),
                ])

        elif "ذهني" in drill_tab:
            for ex in OFF_ICE_EXERCISES['mental']:
                render_exercise_card(ex, icon="🧠", extra_fields=[
                    ("technique_ar", "📋 الطريقة:"),
                    ("skating_benefit_ar", "⛸ الفائدة:"),
                    ("duration_ar", "⏱ المدة:"),
                ])

    # ── TAB 3: ISU Score Calculator ─────────────────────────────────
    with tab3:
        st.subheader("⚡ حاسبة النقاط الرسمية (ISU Scale of Values)")
        st.info("أضف عناصر البرنامج ثم احسب المجموع التقني المتوقع (TES)")

        if 'program_elements' not in st.session_state:
            st.session_state.program_elements = []

        all_elements = {**JUMPS, **SPINS, **STEP_SEQUENCES}
        elem_options = [f"{k} — {v['name_ar']}" for k, v in all_elements.items()]

        with st.form("add_element_form"):
            c1, c2, c3 = st.columns([3,1,1])
            elem_sel = c1.selectbox("العنصر", elem_options)
            goe = c2.slider("GOE", -5, 5, 0)
            in_second_half = c3.checkbox("النصف الثاني (+10%)")
            if st.form_submit_button("➕ إضافة عنصر"):
                code = elem_sel.split(" — ")[0]
                st.session_state.program_elements.append({
                    "code": code, "goe": goe, "second_half": in_second_half
                })

        if st.session_state.program_elements:
            result = calculate_program_score(st.session_state.program_elements)

            total_bv_raw = sum(all_elements[e['code']]['bv'] for e in st.session_state.program_elements
                               if e['code'] in all_elements)
            total_with_sh = 0
            rows = []
            for e in st.session_state.program_elements:
                code = e['code']
                if code not in all_elements:
                    continue
                bv = all_elements[code]['bv']
                if e.get('second_half'):
                    bv = bv * 1.1
                goe_v = e['goe'] * 1.0
                score = bv + goe_v
                total_with_sh += score
                rows.append({
                    "العنصر": code,
                    "الاسم": all_elements[code]['name_ar'],
                    "القيمة الأساسية": f"{all_elements[code]['bv']:.2f}",
                    "نصف ثاني": "✅" if e.get('second_half') else "",
                    "GOE": f"{e['goe']:+d}",
                    "المجموع": f"{score:.2f}",
                })

            df_elements = pd.DataFrame(rows)
            st.dataframe(df_elements, use_container_width=True)

            c1, c2, c3 = st.columns(3)
            c1.metric("🎯 TES الإجمالي", f"{total_with_sh:.2f}")
            c2.metric("📊 عدد العناصر", len(st.session_state.program_elements))
            c3.metric("🏅 TES بدون GOE", f"{total_bv_raw:.2f}")

            if st.button("🗑️ مسح كل العناصر"):
                st.session_state.program_elements = []
                st.rerun()

            # PCS Estimator
            st.markdown("---")
            st.subheader("📐 تقدير Program Components Score (PCS)")
            pcs_cols = st.columns(5)
            pcs_names = list(PROGRAM_COMPONENTS.keys())
            pcs_values = {}
            for i, k in enumerate(pcs_names):
                with pcs_cols[i]:
                    comp = PROGRAM_COMPONENTS[k]
                    pcs_values[k] = st.slider(comp['name_ar'], 1.0, 10.0, 7.0, 0.25)
            factor = st.radio("المضاعف", ["×1.0 (برنامج قصير)","×2.0 (برنامج حر)"], horizontal=True)
            mult = 1.0 if "1.0" in factor else 2.0
            pcs_total = sum(pcs_values.values()) / 5 * 5 * mult
            st.metric(f"🎭 PCS الإجمالي (×{mult})", f"{pcs_total:.2f}")
            st.metric("🏆 النقطة الإجمالية المتوقعة", f"{total_with_sh + pcs_total:.2f}")
        else:
            st.info("أضف عناصر البرنامج باستخدام النموذج أعلاه")

    # ── TAB 4: Judging Guide ────────────────────────────────────────
    with tab4:
        st.subheader("📖 دليل المحكمين الرسمي — ISU International Judging System (IJS)")

        judge_section = st.selectbox("اختر القسم", [
            "🏃 البرنامج القصير والبرنامج الحر",
            "⚖️ مقياس GOE والمعايير",
            "🎭 Program Components (PCS)",
            "❌ الخصومات والعقوبات",
            "🔄 الدوران الناقص",
            "💡 قيم العناصر (Scale of Values)",
        ])

        if "البرنامج" in judge_section:
            for prog_key, prog in JUDGING_RULES.items():
                if prog_key in ["short_program","free_skate"]:
                    st.markdown(f"### {prog['name_ar']}")
                    st.markdown(f"**المدة:** {prog['duration_ar']}")
                    st.markdown(f"**نظام التسجيل:** {prog['scoring_ar']}")
                    st.markdown("**العناصر المطلوبة:**")
                    for i, elem in enumerate(prog['elements_ar'], 1):
                        st.markdown(f"""<div class="element-card">{i}. {elem}</div>""", unsafe_allow_html=True)
                    st.markdown("---")

        elif "GOE" in judge_section:
            st.markdown("### مقياس GOE من -5 إلى +5")
            st.markdown("كل محكم يمنح GOE بناءً على المعايير التالية:")
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("#### ✅ معايير GOE الإيجابي")
                for crit in GOE_CRITERIA_JUMPS['positive']:
                    st.markdown(f"""<div class="element-card" style="border-left-color:#28a745">✓ {crit}</div>""",
                               unsafe_allow_html=True)
            with c2:
                st.markdown("#### ❌ معايير GOE السلبي")
                for crit in GOE_CRITERIA_JUMPS['negative']:
                    st.markdown(f"""<div class="element-card" style="border-left-color:#dc3545">✗ {crit}</div>""",
                               unsafe_allow_html=True)
            st.markdown("---")
            st.markdown("### جدول قيم GOE")
            goe_data = pd.DataFrame([
                {"GOE": g, "القيمة": v, "التفسير": ["كارثي","سيء جداً","سيء","ضعيف","مقبول",
                                                        "جيد","جيد+","ممتاز","ممتاز+","استثنائي"][i]}
                for i, (g, v) in enumerate(zip(range(-5, 6), range(-5, 6)))
            ])
            st.dataframe(goe_data, use_container_width=True)

        elif "PCS" in judge_section:
            st.markdown("### مكونات درجة البرنامج (PCS) — 5 محاور")
            for k, comp in PROGRAM_COMPONENTS.items():
                with st.expander(f"**{k} — {comp['name_ar']}**"):
                    st.write(f"**التعريف:** {comp['description_ar']}")
                    st.markdown("**معايير التقييم:**")
                    for crit in comp['criteria_ar']:
                        st.write(f"• {crit}")

        elif "خصم" in judge_section or "عقوبات" in judge_section:
            st.markdown("### ❌ الخصومات الرسمية")
            for ded in JUDGING_RULES['deductions']['rules_ar']:
                st.markdown(f"""<div class="element-card" style="border-left-color:#dc3545">⚠️ {ded}</div>""",
                           unsafe_allow_html=True)
            st.markdown("---")
            st.warning("💡 مهم: إجمالي خصومات السقوط محدودة بـ -5.0 في البرنامج الواحد")

        elif "دوران" in judge_section:
            st.markdown("### 🔄 قواعد الدوران الناقص (Under-Rotation)")
            for rule in JUDGING_RULES['under_rotation']['rules_ar']:
                st.markdown(f"""<div class="element-card" style="border-left-color:#ff9800">📐 {rule}</div>""",
                           unsafe_allow_html=True)

        elif "قيم" in judge_section:
            st.markdown("### 💡 Scale of Values — القيم الأساسية لكل العناصر")
            jump_tab, spin_tab, step_tab = st.tabs(["🦅 القفزات","🌀 السبينات","🦶 الخطوات"])
            with jump_tab:
                jdf = pd.DataFrame([
                    {"الرمز": k, "الاسم": v['name_ar'], "الدورات": v['rotations'], "القيمة الأساسية": v['bv']}
                    for k, v in JUMPS.items()
                ])
                st.dataframe(jdf.sort_values("القيمة الأساسية", ascending=False), use_container_width=True)
            with spin_tab:
                sdf = pd.DataFrame([
                    {"الرمز": k, "الاسم": v['name_ar'], "القيمة الأساسية": v['bv']}
                    for k, v in SPINS.items()
                ])
                st.dataframe(sdf.sort_values("القيمة الأساسية", ascending=False), use_container_width=True)
            with step_tab:
                stdf = pd.DataFrame([
                    {"الرمز": k, "الاسم": v['name_ar'], "القيمة الأساسية": v['bv']}
                    for k, v in STEP_SEQUENCES.items()
                ])
                st.dataframe(stdf, use_container_width=True)

    # ── TAB 5: Championship Roadmap ─────────────────────────────────
    with tab5:
        st.subheader("🎯 مسار التطور — من المبتدئ إلى بطل العالم")

        c1, c2 = st.columns([1, 2])
        with c1:
            current_level = st.selectbox("مستوى اللاعب الحالي", list(LEVEL_PROGRESSION.keys()))
        with c2:
            if current_level in LEVEL_PROGRESSION:
                lvl = LEVEL_PROGRESSION[current_level]
                st.markdown(f"""
                <div style="background:#e8f4f8; border-radius:10px; padding:16px;">
                    <h4 style="color:#1f77b4;">{lvl['name_ar']}</h4>
                    <p>{lvl['description_ar']}</p>
                    <p><b>🎯 المنافسات المستهدفة:</b> {lvl['target_competition']}</p>
                </div>""", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("### 🗺️ خريطة التطور الكاملة")
        levels_list = list(LEVEL_PROGRESSION.keys())
        current_idx = levels_list.index(current_level)

        for i, (lvl_key, lvl_data) in enumerate(LEVEL_PROGRESSION.items()):
            done = i < current_idx
            current_mark = i == current_idx
            future = i > current_idx

            if current_mark:
                border = "3px solid #1f77b4"
                bg = "#e3f2fd"
                icon = "📍"
            elif done:
                border = "2px solid #28a745"
                bg = "#e8f5e9"
                icon = "✅"
            else:
                border = "1px solid #dee2e6"
                bg = "#f8f9fa"
                icon = "🔒"

            with st.expander(f"{icon} **{lvl_data['name_ar']}** — {lvl_data['target_competition']}",
                            expanded=current_mark):
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.markdown("**🦅 القفزات المطلوبة:**")
                    for j in lvl_data['required_jumps']:
                        if j in JUMPS:
                            bv = JUMPS[j]['bv']
                            st.write(f"• {j} — {JUMPS[j]['name_ar']} (BV: {bv})")
                        else:
                            st.write(f"• {j}")
                with c2:
                    st.markdown("**🌀 السبينات المطلوبة:**")
                    for sp in lvl_data['required_spins']:
                        if sp in SPINS:
                            st.write(f"• {sp} — {SPINS[sp]['name_ar']}")
                        else:
                            st.write(f"• {sp}")
                with c3:
                    st.markdown("**📚 المهارات الأساسية:**")
                    for skill in lvl_data['skills_ar']:
                        st.write(f"• {skill}")

        # Injury Prevention
        st.markdown("---")
        st.subheader("🩺 الوقاية من الإصابات")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**⚠️ الإصابات الشائعة في التزلج:**")
            for inj in INJURY_PREVENTION['common_injuries_ar']:
                st.markdown(f"""<div class="element-card" style="border-left-color:#ff9800;">⚠️ {inj}</div>""",
                           unsafe_allow_html=True)
        with c2:
            st.markdown("**✅ طرق الوقاية:**")
            for prev in INJURY_PREVENTION['prevention_ar']:
                st.markdown(f"""<div class="element-card" style="border-left-color:#28a745;">✓ {prev}</div>""",
                           unsafe_allow_html=True)

    # ── TAB 6: Performance Analysis ─────────────────────────────────
    with tab6:
        st.subheader("🔬 تحليل أداء اللاعبين من البيانات")

        members_df = get_data("SELECT * FROM members ORDER BY name")
        if len(members_df) == 0:
            st.info("لا يوجد أعضاء في النظام"); return

        sel_member = st.selectbox("اختر اللاعب", members_df['name'].tolist())
        if sel_member:
            member = members_df[members_df['name']==sel_member].iloc[0]
            mid = int(member['id'])

            att = get_data("SELECT * FROM attendance WHERE member_id=?", (mid,))
            mems = get_data("SELECT * FROM memberships WHERE member_id=?", (mid,))

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("📅 إجمالي الحضور", len(att))
            oi = len(att[att['session_type']=='on-ice']) if len(att) > 0 else 0
            ofi = len(att[att['session_type']=='off-ice']) if len(att) > 0 else 0
            c2.metric("🧊 On-Ice", oi)
            c3.metric("🏋️ Off-Ice", ofi)
            c4.metric("💰 المدفوع", f"{mems['amount'].sum():,.0f} ج" if len(mems) > 0 else "—")

            if len(att) > 0:
                att['date'] = pd.to_datetime(att['date'])

                # Consistency score
                if len(att) > 1:
                    date_range = (att['date'].max() - att['date'].min()).days + 1
                    consistency = min(100, (len(att) / max(date_range, 1)) * 7 * 100)
                    st.markdown("---")
                    col_m, col_g = st.columns([1, 2])
                    with col_m:
                        st.markdown("### 📊 مؤشر الانتظام")
                        st.metric("معدل الانتظام", f"{consistency:.0f}%")
                        if consistency >= 80:
                            st.success("🟢 ممتاز — انتظام عالٍ جداً")
                        elif consistency >= 60:
                            st.warning("🟡 جيد — يمكن تحسينه")
                        else:
                            st.error("🔴 يحتاج تحسين — الانتظام منخفض")
                    with col_g:
                        monthly = att.groupby(att['date'].dt.to_period('M').astype(str)).size().reset_index(name='count')
                        fig = px.bar(monthly, x='date', y='count', title=f'الحضور الشهري - {sel_member}',
                                    color='count', color_continuous_scale='teal')
                        st.plotly_chart(fig, use_container_width=True)

                # Recommendations
                st.markdown("---")
                st.subheader("💡 توصيات التدريب الشخصية")
                level = member.get('level', 'Alpha')
                on_ice_ratio = oi / max(len(att), 1)

                recs = []
                if len(att) < 10:
                    recs.append(("⚠️", "زيادة معدل الحضور — عدد الحصص الحالي منخفض جداً للتطور"))
                if on_ice_ratio < 0.5:
                    recs.append(("📌", "زيادة حصص On-Ice — النسبة الحالية منخفضة"))
                if ofi == 0:
                    recs.append(("🏋️", "إضافة تدريبات Off-Ice — ضرورية لبناء القوة والمرونة"))
                if level in ["Alpha", "Beta"]:
                    recs.append(("🎯", "التركيز على أساسيات الانزلاق والحافات قبل القفز"))
                elif level in ["Gamma", "Delta"]:
                    recs.append(("🦅", "تعميق تقنية القفزات المزدوجة والبدء بالثلاثية"))
                else:
                    recs.append(("🏆", "التحضير لبطولات دولية — تكثيف محاكاة المنافسة"))

                recs.append(("🧠", "إضافة التدريب الذهني (Visualization) قبل كل منافسة"))
                recs.append(("🩺", "متابعة الوقاية من الإصابات: إحماء 15 دقيقة + تمدد بعد التدريب"))

                for icon, rec in recs:
                    st.markdown(f"""<div class="element-card">{icon} {rec}</div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════
# 🎥 صفحة تحليل الفيديو
# ═══════════════════════════════════════════════════════════════════
def show_video_analysis_page():
    st.title("🎥 تحليل الفيديو الاحترافي")
    st.markdown("**أداة المدرّب — رفع الفيديو، تحديد العناصر، وتقييم GOE تلقائياً**")
    st.markdown("---")

    # ISU element values (simplified)
    JUMP_VALUES = {
        "1A (Axel مفرد)": 1.10, "2S (Salchow مزدوج)": 1.30, "2T (Toe Loop مزدوج)": 1.30,
        "2Lo (Loop مزدوج)": 1.70, "2F (Flip مزدوج)": 1.80, "2Lz (Lutz مزدوج)": 2.10,
        "2A (Axel مزدوج)": 3.30, "3S (Salchow ثلاثي)": 4.30, "3T (Toe Loop ثلاثي)": 4.20,
        "3Lo (Loop ثلاثي)": 5.10, "3F (Flip ثلاثي)": 5.30, "3Lz (Lutz ثلاثي)": 6.00,
        "3A (Axel ثلاثي)": 8.00, "4T (Toe Loop رباعي)": 9.50, "4S (Salchow رباعي)": 9.70,
        "4Lo (Loop رباعي)": 10.50, "4F (Flip رباعي)": 11.00, "4Lz (Lutz رباعي)": 11.50,
    }
    SPIN_VALUES = {
        "SSp (Sit Spin)": 1.70, "CSp (Camel Spin)": 1.80, "USp (Upright Spin)": 1.20,
        "LSp (Layback Spin)": 1.50, "CCoSp (Combo Spin)": 3.50, "FCCoSp (Combo Flying)": 3.50,
        "FCSp (Flying Camel)": 2.30, "FSSp (Flying Sit)": 2.30,
    }
    STEP_VALUES = {"StSq (Step Sequence)": 3.30, "ChSq (Choreographic Sequence)": 3.00}
    ALL_ELEMENTS = {**JUMP_VALUES, **SPIN_VALUES, **STEP_VALUES}

    # ── Tab layout ──────────────────────────────────────────────
    vtab1, vtab2, vtab3 = st.tabs(["📹 الفيديو والتشغيل", "✍️ تحليل العناصر", "📊 التقرير النهائي"])

    # ── TAB 1: Video upload & playback ─────────────────────────
    with vtab1:
        st.subheader("📹 رفع وتشغيل الفيديو")
        col_up, col_info = st.columns([2, 1])
        with col_up:
            uploaded = st.file_uploader(
                "ارفع فيديو البرنامج (MP4 / MOV / AVI)",
                type=["mp4", "mov", "avi", "mkv"],
                help="ارفع تسجيل برنامج قصير أو حر للاعب"
            )
            if uploaded:
                st.session_state['video_name'] = uploaded.name
                st.session_state['video_bytes'] = uploaded.read()
                st.success(f"✅ تم رفع: **{uploaded.name}**")

        with col_info:
            st.markdown("""
            **📋 كيفية الاستخدام:**
            1. ارفع الفيديو هنا
            2. شاهده في المشغّل أدناه
            3. انتقل لـ **"تحليل العناصر"**
            4. أضف القفزات والسبينات يدوياً
            5. شاهد **التقرير النهائي**
            """)

        if 'video_bytes' in st.session_state:
            st.markdown("### ▶️ مشغّل الفيديو")
            st.video(st.session_state['video_bytes'])
            st.info("💡 **نصيحة:** شاهد الفيديو وسجّل توقيت كل عنصر، ثم أدخله في قسم التحليل")
        else:
            st.info("👆 ارفع فيديو أعلاه لتشغيله")
            # Show demo video from YouTube
            st.markdown("### 🌐 مثال على البرنامج الاحترافي")
            import streamlit.components.v1 as comp_v
            import urllib.parse
            q = urllib.parse.quote_plus("figure skating free program ISU World Championship 2024")
            comp_v.html(
                f'<iframe width="100%" height="280" src="https://www.youtube.com/embed?listType=search&list={q}&autoplay=0" '
                f'frameborder="0" allowfullscreen style="border-radius:8px;"></iframe>',
                height=290
            )

    # ── TAB 2: Element annotation ───────────────────────────────
    with vtab2:
        st.subheader("✍️ إدخال عناصر البرنامج")
        st.info("أضف كل عنصر نفّذه اللاعب في الفيديو مع تقييم GOE")

        # Skater info
        with st.expander("👤 بيانات اللاعب والبرنامج", expanded=True):
            ci1, ci2, ci3 = st.columns(3)
            skater_name = ci1.text_input("اسم اللاعب")
            program_type = ci2.selectbox("نوع البرنامج", ["برنامج قصير (SP)", "برنامج حر (FS)"])
            skater_level = ci3.selectbox("المستوى", ["Junior", "Senior", "Novice", "Basic"])

        if 'elements' not in st.session_state:
            st.session_state['elements'] = []

        # Add element form
        st.markdown("### ➕ إضافة عنصر")
        with st.form("add_elem", clear_on_submit=True):
            fc1, fc2, fc3, fc4 = st.columns([3, 1, 1, 1])
            elem_name = fc1.selectbox("العنصر", list(ALL_ELEMENTS.keys()))
            goe_val = fc2.select_slider("GOE", options=[-5,-4,-3,-2,-1,0,1,2,3,4,5], value=0)
            second_half = fc3.checkbox("نصف ثاني")
            timing = fc4.text_input("التوقيت", placeholder="0:45")
            notes = st.text_input("ملاحظات (اختياري)", placeholder="مثال: هبوط صحيح، دوران ناقص...")
            if st.form_submit_button("➕ إضافة", type="primary"):
                bv = ALL_ELEMENTS[elem_name]
                if second_half:
                    bv = round(bv * 1.1, 2)
                goe_bonus = round(goe_val * (ALL_ELEMENTS[elem_name] * 0.1), 2)
                final_score = round(bv + goe_bonus, 2)
                st.session_state['elements'].append({
                    "timing": timing, "element": elem_name,
                    "bv": ALL_ELEMENTS[elem_name], "second_half": second_half,
                    "bv_adj": bv, "goe": goe_val, "goe_bonus": goe_bonus,
                    "final": final_score, "notes": notes
                })
                st.success(f"✅ أُضيف: **{elem_name}** — النقاط: {final_score:.2f}")

        # Display current elements
        if st.session_state['elements']:
            st.markdown("### 📋 العناصر المُدخلة")
            for i, el in enumerate(st.session_state['elements']):
                goe_color = "#27ae60" if el['goe'] > 0 else ("#e74c3c" if el['goe'] < 0 else "#95a5a6")
                sh_badge = ' <span style="background:#f39c12;color:white;padding:2px 6px;border-radius:10px;font-size:0.75em;">نصف ثاني</span>' if el['second_half'] else ''
                st.markdown(f"""
                <div style="background:white;border-radius:8px;padding:10px 16px;margin:5px 0;
                            border-left:4px solid {goe_color};box-shadow:0 1px 4px rgba(0,0,0,0.08);">
                  <b>{i+1}. {el['element']}</b>{sh_badge}
                  &nbsp;|&nbsp; ⏱ {el['timing'] or '—'}
                  &nbsp;|&nbsp; BV: <b>{el['bv']:.2f}</b>
                  &nbsp;|&nbsp; GOE: <b style="color:{goe_color}">{el['goe']:+d}</b>
                  &nbsp;|&nbsp; النقاط: <b>{el['final']:.2f}</b>
                  {'<br><small style="color:#666;">📝 ' + el['notes'] + '</small>' if el['notes'] else ''}
                </div>""", unsafe_allow_html=True)

            # Delete buttons
            col_del, col_clr = st.columns([3, 1])
            del_idx = col_del.number_input("احذف عنصر رقم", 1, len(st.session_state['elements']), 1)
            if col_del.button("🗑 حذف العنصر المحدد"):
                st.session_state['elements'].pop(del_idx - 1)
                st.rerun()
            if col_clr.button("🧹 مسح الكل", type="secondary"):
                st.session_state['elements'] = []
                st.rerun()
        else:
            st.info("لا توجد عناصر بعد — أضف العناصر من النموذج أعلاه")

    # ── TAB 3: Final Report ─────────────────────────────────────
    with vtab3:
        st.subheader("📊 التقرير النهائي — ISU Scoring")

        elements = st.session_state.get('elements', [])
        if not elements:
            st.warning("⚠️ أضف العناصر أولاً في قسم **تحليل العناصر**")
            return

        # Calculate TES
        tes = sum(e['final'] for e in elements)

        # PCS input
        st.markdown("### 🎭 مكوّنات الأداء (PCS)")
        pc1, pc2, pc3, pc4, pc5 = st.columns(5)
        sk  = pc1.slider("المهارة التزلجية", 0.0, 10.0, 7.0, 0.25)
        tr  = pc2.slider("الانتقالات", 0.0, 10.0, 6.5, 0.25)
        pe  = pc3.slider("الأداء", 0.0, 10.0, 7.0, 0.25)
        co  = pc4.slider("التكوين", 0.0, 10.0, 6.5, 0.25)
        in_ = pc5.slider("التفسير", 0.0, 10.0, 7.0, 0.25)

        pcs_factor = 2.0 if "حر" in program_type else 1.0
        pcs = round((sk + tr + pe + co + in_) / 5 * 10 * pcs_factor, 2)
        total = round(tes + pcs, 2)

        # Deductions
        st.markdown("### ⚠️ الخصومات")
        dc1, dc2, dc3 = st.columns(3)
        falls = dc1.number_input("عدد السقطات", 0, 10, 0)
        time_vio = dc2.number_input("خصم الوقت (ثواني)", 0, 30, 0)
        other_ded = dc3.number_input("خصومات أخرى", 0.0, 10.0, 0.0, 0.5)
        deductions = round(falls * 1.0 + (time_vio // 5) * 1.0 + other_ded, 2)
        final_score = round(total - deductions, 2)

        # Results dashboard
        st.markdown("---")
        st.markdown("### 🏆 النتيجة النهائية")
        r1, r2, r3, r4, r5 = st.columns(5)
        r1.metric("TES المجموع التقني", f"{tes:.2f}")
        r2.metric("PCS الأداء الفني", f"{pcs:.2f}")
        r3.metric("المجموع", f"{total:.2f}")
        r4.metric("الخصومات", f"-{deductions:.2f}")
        r5.metric("🏅 النقاط النهائية", f"{final_score:.2f}")

        # Score gauge
        max_possible = sum(ALL_ELEMENTS[e['element']] * 1.1 for e in elements) + 100
        pct = min(final_score / max(max_possible, 1) * 100, 100)
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=final_score,
            title={'text': "النقاط الإجمالية", 'font': {'size': 18}},
            gauge={
                'axis': {'range': [0, max(final_score * 1.5, 100)]},
                'bar': {'color': "#1f77b4"},
                'steps': [
                    {'range': [0, final_score * 0.5], 'color': "#ffeaa7"},
                    {'range': [final_score * 0.5, final_score * 0.8], 'color': "#81ecec"},
                    {'range': [final_score * 0.8, final_score * 1.5], 'color': "#55efc4"},
                ],
                'threshold': {'line': {'color': "gold", 'width': 4}, 'value': final_score}
            }
        ))
        fig_gauge.update_layout(height=280, margin=dict(t=40, b=10, l=20, r=20))
        st.plotly_chart(fig_gauge, use_container_width=True)

        # Element breakdown table
        st.markdown("### 📋 تفاصيل العناصر")
        rows = []
        for i, e in enumerate(elements, 1):
            goe_str = f"{e['goe']:+d}"
            rows.append({
                "#": i, "التوقيت": e['timing'] or "—",
                "العنصر": e['element'],
                "القيمة الأساسية": f"{e['bv']:.2f}",
                "نصف ثاني": "✅" if e['second_half'] else "",
                "GOE": goe_str,
                "النقاط": f"{e['final']:.2f}",
                "ملاحظات": e['notes'] or ""
            })
        df_report = pd.DataFrame(rows)
        st.dataframe(df_report, use_container_width=True, hide_index=True)

        # PCS breakdown
        st.markdown("### 🎭 تفاصيل PCS")
        pcs_df = pd.DataFrame({
            "المكوّن": ["المهارة التزلجية (SK)", "الانتقالات (TR)", "الأداء (PE)", "التكوين (CO)", "التفسير (IN)"],
            "التقييم": [sk, tr, pe, co, in_],
            "النقاط": [sk * 2 * pcs_factor, tr * 2 * pcs_factor, pe * 2 * pcs_factor, co * 2 * pcs_factor, in_ * 2 * pcs_factor]
        })
        fig_pcs = px.bar(pcs_df, x="المكوّن", y="التقييم", color="التقييم",
                         color_continuous_scale="Blues", title="تقييم مكوّنات PCS")
        fig_pcs.update_layout(height=300, showlegend=False)
        st.plotly_chart(fig_pcs, use_container_width=True)

        # GOE breakdown chart
        st.markdown("### ⚡ تحليل GOE لكل عنصر")
        goe_df = pd.DataFrame({
            "العنصر": [f"{i+1}. {e['element'][:15]}" for i, e in enumerate(elements)],
            "GOE": [e['goe'] for e in elements],
            "اللون": ["إيجابي" if e['goe'] > 0 else ("سلبي" if e['goe'] < 0 else "محايد") for e in elements]
        })
        fig_goe = px.bar(goe_df, x="العنصر", y="GOE", color="اللون",
                         color_discrete_map={"إيجابي": "#27ae60", "سلبي": "#e74c3c", "محايد": "#95a5a6"},
                         title="GOE لكل عنصر")
        fig_goe.add_hline(y=0, line_dash="dash", line_color="gray")
        fig_goe.update_layout(height=300)
        st.plotly_chart(fig_goe, use_container_width=True)

        # Export report button
        st.markdown("---")
        report_text = f"""تقرير تحليل الأداء - ISU Scoring
=================================
اللاعب: {skater_name or 'غير محدد'}
البرنامج: {program_type}
المستوى: {skater_level}
التاريخ: {datetime.now().strftime('%Y-%m-%d')}

المجموع التقني (TES): {tes:.2f}
مكوّنات الأداء (PCS): {pcs:.2f}
المجموع: {total:.2f}
الخصومات: -{deductions:.2f}
النقاط النهائية: {final_score:.2f}

تفاصيل العناصر:
"""
        for i, e in enumerate(elements, 1):
            report_text += f"  {i}. {e['element']} | BV:{e['bv']:.2f} | GOE:{e['goe']:+d} | النقاط:{e['final']:.2f}\n"

        st.download_button(
            "💾 تحميل التقرير كنص",
            data=report_text,
            file_name=f"تقرير_{skater_name or 'لاعب'}_{datetime.now().strftime('%Y%m%d')}.txt",
            mime="text/plain"
        )


def main():
    with st.sidebar:
        st.title("🎿 القائمة الرئيسية")
        st.markdown("---")
        page = st.radio("اختر الصفحة", [
            "🏠 الرئيسية",
            "🏆 التدريب الاحترافي",
            "🎥 تحليل الفيديو",
            "👥 إدارة الأعضاء",
            "📅 تسجيل الحضور",
            "🧑‍💼 ملفات الأعضاء",
            "📊 التقارير والإحصائيات",
        ])
        st.markdown("---")
        members_count = get_data("SELECT COUNT(*) as c FROM members")['c'].iloc[0]
        att_count = get_data("SELECT COUNT(*) as c FROM attendance")['c'].iloc[0]
        st.markdown("### 📊 إحصائيات سريعة")
        st.write(f"👥 الأعضاء: **{members_count}**")
        st.write(f"📅 الحضور: **{att_count}**")
        st.markdown("---")
        st.markdown("""
        <div style="background:#1a1a2e; color:gold; border-radius:8px; padding:10px; text-align:center; font-size:0.9em;">
            🥇 نظام صناعة البطل العالمي<br>
            <span style="color:#aaa; font-size:0.8em;">مبني على معايير ISU الرسمية</span>
        </div>""", unsafe_allow_html=True)

    if page == "🏠 الرئيسية":
        show_homepage()
    elif page == "🏆 التدريب الاحترافي":
        show_coaching_hub()
    elif page == "🎥 تحليل الفيديو":
        show_video_analysis_page()
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
