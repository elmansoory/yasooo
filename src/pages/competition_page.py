"""
صفحة إدارة البطولات - Competition Management Page
نظام تتبع وإدارة البطولات والنتائج للتزلج الفني
"""
import streamlit as st
import sqlite3
import pandas as pd
import io
import sys
from pathlib import Path
from datetime import date

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

DB_PATH = "skating_database.db"


def _get_conn():
    return sqlite3.connect(DB_PATH)


def _init_db():
    """إنشاء جداول البطولات إن لم تكن موجودة"""
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.executescript("""
            CREATE TABLE IF NOT EXISTS competitions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                location TEXT,
                comp_date TEXT,
                comp_type TEXT,
                level TEXT,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS competition_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                competition_id INTEGER REFERENCES competitions(id),
                skater_name TEXT,
                category TEXT,
                event TEXT,
                coach TEXT,
                registration_status TEXT DEFAULT 'registered',
                notes TEXT
            );

            CREATE TABLE IF NOT EXISTS competition_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                competition_id INTEGER REFERENCES competitions(id),
                skater_name TEXT,
                category TEXT,
                rank INTEGER,
                sp_score REAL,
                fs_score REAL,
                total_score REAL,
                medal TEXT,
                notes TEXT
            );
        """)
        conn.commit()
    finally:
        conn.close()


def _get_skaters():
    """جلب أسماء المتزلجين من جدول skaters"""
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT name FROM skaters ORDER BY name")
        rows = cur.fetchall()
        return [r[0] for r in rows] if rows else []
    except Exception:
        return []
    finally:
        conn.close()


def _get_competitions():
    """جلب قائمة البطولات"""
    conn = _get_conn()
    try:
        df = pd.read_sql_query(
            "SELECT * FROM competitions ORDER BY comp_date DESC", conn
        )
        return df
    except Exception:
        return pd.DataFrame()
    finally:
        conn.close()


def _to_excel(df: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    try:
        with pd.ExcelWriter(buf, engine='openpyxl') as w:
            df.to_excel(w, index=False)
        return buf.getvalue()
    except Exception:
        return df.to_csv(index=False).encode('utf-8-sig')


# ---------------------------------------------------------------------------
# Tab 1 — البطولات
# ---------------------------------------------------------------------------

def _tab_competitions():
    st.subheader("🏆 قائمة البطولات")

    conn = _get_conn()
    try:
        df_comps = pd.read_sql_query(
            "SELECT id, name, location, comp_date, comp_type, level, notes FROM competitions ORDER BY comp_date DESC",
            conn
        )
    except Exception as e:
        st.error(f"خطأ في قراءة البيانات: {e}")
        conn.close()
        return
    finally:
        conn.close()

    if df_comps.empty:
        st.info("لا توجد بطولات مسجلة حتى الآن.")
    else:
        col_names = {
            "id": "الرقم", "name": "اسم البطولة", "location": "الموقع",
            "comp_date": "التاريخ", "comp_type": "النوع", "level": "المستوى", "notes": "ملاحظات"
        }
        st.dataframe(df_comps.rename(columns=col_names), use_container_width=True)

        excel_data = _to_excel(df_comps)
        st.download_button(
            label="📥 تصدير إلى Excel",
            data=excel_data,
            file_name="competitions.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    st.markdown("---")
    st.subheader("➕ إضافة بطولة جديدة")

    with st.form("add_competition_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("اسم البطولة *")
            location = st.text_input("الموقع")
            comp_date = st.date_input("تاريخ البطولة", value=date.today())
        with col2:
            comp_type = st.selectbox(
                "نوع البطولة",
                ["ISU", "National", "Regional", "Local", "Friendly"]
            )
            level = st.selectbox(
                "المستوى",
                ["Beginner", "Intermediate", "Advanced", "Elite"]
            )
            notes = st.text_area("ملاحظات", height=80)

        submitted = st.form_submit_button("💾 حفظ البطولة")
        if submitted:
            if not name.strip():
                st.error("يرجى إدخال اسم البطولة.")
            else:
                try:
                    conn = _get_conn()
                    cur = conn.cursor()
                    cur.execute(
                        "INSERT INTO competitions (name, location, comp_date, comp_type, level, notes) VALUES (?,?,?,?,?,?)",
                        (name.strip(), location.strip(), str(comp_date), comp_type, level, notes.strip())
                    )
                    conn.commit()
                    conn.close()
                    st.success(f"✅ تم إضافة البطولة '{name}' بنجاح!")
                    st.rerun()
                except Exception as e:
                    st.error(f"خطأ في الحفظ: {e}")

    # حذف بطولة
    if not df_comps.empty:
        st.markdown("---")
        st.subheader("🗑️ حذف بطولة")
        comp_options = {f"{row['name']} ({row['comp_date']})": row['id'] for _, row in df_comps.iterrows()}
        to_delete = st.selectbox("اختر البطولة للحذف", list(comp_options.keys()), key="del_comp")
        if st.button("🗑️ حذف البطولة المحددة", type="secondary"):
            try:
                conn = _get_conn()
                cur = conn.cursor()
                cid = comp_options[to_delete]
                cur.execute("DELETE FROM competition_results WHERE competition_id=?", (cid,))
                cur.execute("DELETE FROM competition_entries WHERE competition_id=?", (cid,))
                cur.execute("DELETE FROM competitions WHERE id=?", (cid,))
                conn.commit()
                conn.close()
                st.success("✅ تم حذف البطولة وجميع بياناتها.")
                st.rerun()
            except Exception as e:
                st.error(f"خطأ في الحذف: {e}")


# ---------------------------------------------------------------------------
# Tab 2 — التسجيل
# ---------------------------------------------------------------------------

def _tab_entries():
    st.subheader("📋 تسجيل المتزلجين في البطولات")

    df_comps = _get_competitions()
    if df_comps.empty:
        st.warning("لا توجد بطولات. أضف بطولة أولاً من تبويب البطولات.")
        return

    comp_options = {f"{row['name']} ({row['comp_date']})": row['id'] for _, row in df_comps.iterrows()}
    selected_comp_label = st.selectbox("اختر البطولة", list(comp_options.keys()), key="entry_comp")
    selected_comp_id = comp_options[selected_comp_label]

    conn = _get_conn()
    try:
        df_entries = pd.read_sql_query(
            "SELECT id, skater_name, category, event, coach, registration_status, notes FROM competition_entries WHERE competition_id=?",
            conn,
            params=(selected_comp_id,)
        )
    except Exception as e:
        st.error(f"خطأ: {e}")
        conn.close()
        return
    finally:
        conn.close()

    st.markdown(f"**عدد المسجلين:** {len(df_entries)}")

    if not df_entries.empty:
        col_names = {
            "id": "الرقم", "skater_name": "اسم المتزلج", "category": "الفئة",
            "event": "النوع", "coach": "المدرب", "registration_status": "الحالة", "notes": "ملاحظات"
        }
        st.dataframe(df_entries.rename(columns=col_names), use_container_width=True)

        excel_data = _to_excel(df_entries)
        st.download_button(
            label="📥 تصدير إلى Excel",
            data=excel_data,
            file_name=f"entries_{selected_comp_id}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="dl_entries"
        )
    else:
        st.info("لا يوجد مسجلون في هذه البطولة حتى الآن.")

    st.markdown("---")
    st.subheader("➕ تسجيل متزلج جديد")

    skaters = _get_skaters()
    if not skaters:
        skaters = []

    with st.form("add_entry_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            if skaters:
                skater_name = st.selectbox("اسم المتزلج *", skaters)
            else:
                skater_name = st.text_input("اسم المتزلج *")
            category = st.selectbox("الفئة", ["Juvenile", "Novice", "Junior", "Senior", "Adult"])
        with col2:
            event = st.selectbox("نوع المنافسة", ["Singles", "Pairs", "Ice Dance"])
            coach = st.text_input("المدرب")
            status = st.selectbox("حالة التسجيل", ["registered", "confirmed", "withdrawn"])
        entry_notes = st.text_input("ملاحظات")

        submitted = st.form_submit_button("💾 تسجيل")
        if submitted:
            sname = skater_name if isinstance(skater_name, str) else str(skater_name)
            if not sname.strip():
                st.error("يرجى إدخال اسم المتزلج.")
            else:
                try:
                    conn = _get_conn()
                    cur = conn.cursor()
                    cur.execute(
                        "INSERT INTO competition_entries (competition_id, skater_name, category, event, coach, registration_status, notes) VALUES (?,?,?,?,?,?,?)",
                        (selected_comp_id, sname.strip(), category, event, coach.strip(), status, entry_notes.strip())
                    )
                    conn.commit()
                    conn.close()
                    st.success(f"✅ تم تسجيل '{sname}' في البطولة!")
                    st.rerun()
                except Exception as e:
                    st.error(f"خطأ في الحفظ: {e}")


# ---------------------------------------------------------------------------
# Tab 3 — النتائج
# ---------------------------------------------------------------------------

def _tab_results():
    st.subheader("🏅 نتائج البطولات")

    df_comps = _get_competitions()
    if df_comps.empty:
        st.warning("لا توجد بطولات مسجلة.")
        return

    comp_options = {f"{row['name']} ({row['comp_date']})": row['id'] for _, row in df_comps.iterrows()}
    selected_comp_label = st.selectbox("اختر البطولة", list(comp_options.keys()), key="result_comp")
    selected_comp_id = comp_options[selected_comp_label]

    conn = _get_conn()
    try:
        df_results = pd.read_sql_query(
            "SELECT id, skater_name, category, rank, sp_score, fs_score, total_score, medal, notes FROM competition_results WHERE competition_id=? ORDER BY rank",
            conn,
            params=(selected_comp_id,)
        )
    except Exception as e:
        st.error(f"خطأ: {e}")
        conn.close()
        return
    finally:
        conn.close()

    if not df_results.empty:
        # إضافة رموز الميداليات
        def medal_icon(m):
            mapping = {"Gold": "🥇", "Silver": "🥈", "Bronze": "🥉"}
            return mapping.get(m, "—")

        df_display = df_results.copy()
        df_display["medal"] = df_display["medal"].apply(medal_icon)
        col_names = {
            "id": "الرقم", "skater_name": "المتزلج", "category": "الفئة",
            "rank": "المركز", "sp_score": "نقاط البرنامج القصير",
            "fs_score": "نقاط البرنامج الحر", "total_score": "المجموع",
            "medal": "الميدالية", "notes": "ملاحظات"
        }
        st.dataframe(df_display.rename(columns=col_names), use_container_width=True)

        excel_data = _to_excel(df_results)
        st.download_button(
            label="📥 تصدير إلى Excel",
            data=excel_data,
            file_name=f"results_{selected_comp_id}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="dl_results"
        )
    else:
        st.info("لا توجد نتائج لهذه البطولة بعد.")

    st.markdown("---")
    st.subheader("➕ إدخال نتيجة")

    skaters = _get_skaters()

    with st.form("add_result_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            if skaters:
                skater_name = st.selectbox("اسم المتزلج *", skaters, key="res_skater")
            else:
                skater_name = st.text_input("اسم المتزلج *", key="res_skater_txt")
            category = st.selectbox("الفئة", ["Juvenile", "Novice", "Junior", "Senior", "Adult"], key="res_cat")
            rank = st.number_input("المركز", min_value=1, step=1, value=1)
        with col2:
            sp_score = st.number_input("نقاط البرنامج القصير", min_value=0.0, step=0.01, format="%.2f")
            fs_score = st.number_input("نقاط البرنامج الحر", min_value=0.0, step=0.01, format="%.2f")
            total_score = st.number_input("المجموع", min_value=0.0, step=0.01, format="%.2f")
            medal = st.selectbox("الميدالية", ["None", "Gold", "Silver", "Bronze"])
        res_notes = st.text_input("ملاحظات", key="res_notes")

        submitted = st.form_submit_button("💾 حفظ النتيجة")
        if submitted:
            sname = skater_name if isinstance(skater_name, str) else str(skater_name)
            if not sname.strip():
                st.error("يرجى إدخال اسم المتزلج.")
            else:
                try:
                    conn = _get_conn()
                    cur = conn.cursor()
                    cur.execute(
                        "INSERT INTO competition_results (competition_id, skater_name, category, rank, sp_score, fs_score, total_score, medal, notes) VALUES (?,?,?,?,?,?,?,?,?)",
                        (selected_comp_id, sname.strip(), category, int(rank), sp_score, fs_score, total_score, medal, res_notes.strip())
                    )
                    conn.commit()
                    conn.close()
                    st.success(f"✅ تم حفظ نتيجة '{sname}'!")
                    st.rerun()
                except Exception as e:
                    st.error(f"خطأ في الحفظ: {e}")


# ---------------------------------------------------------------------------
# Tab 4 — الإحصائيات
# ---------------------------------------------------------------------------

def _tab_statistics():
    import plotly.express as px

    st.subheader("📊 إحصائيات البطولات")

    conn = _get_conn()
    try:
        df_results = pd.read_sql_query(
            "SELECT * FROM competition_results", conn
        )
        df_comps = pd.read_sql_query(
            "SELECT * FROM competitions", conn
        )
    except Exception as e:
        st.error(f"خطأ في قراءة البيانات: {e}")
        conn.close()
        return
    finally:
        conn.close()

    if df_results.empty and df_comps.empty:
        st.info("لا توجد بيانات كافية للإحصائيات. أضف بطولات ونتائج أولاً.")
        return

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("إجمالي البطولات", len(df_comps))
    with col2:
        total_entries_conn = _get_conn()
        try:
            total_entries = pd.read_sql_query("SELECT COUNT(*) as c FROM competition_entries", total_entries_conn).iloc[0]['c']
        except Exception:
            total_entries = 0
        finally:
            total_entries_conn.close()
        st.metric("إجمالي التسجيلات", int(total_entries))
    with col3:
        st.metric("إجمالي النتائج المسجلة", len(df_results))

    st.markdown("---")

    # مخطط الميداليات لكل متزلج
    if not df_results.empty:
        medals_df = df_results[df_results['medal'].isin(['Gold', 'Silver', 'Bronze'])]
        if not medals_df.empty:
            medal_counts = medals_df.groupby(['skater_name', 'medal']).size().reset_index(name='count')
            medal_order = {"Gold": 1, "Silver": 2, "Bronze": 3}
            medal_colors = {"Gold": "#FFD700", "Silver": "#C0C0C0", "Bronze": "#CD7F32"}
            fig_medals = px.bar(
                medal_counts,
                x='skater_name',
                y='count',
                color='medal',
                title='🏅 الميداليات لكل متزلج',
                labels={'skater_name': 'المتزلج', 'count': 'عدد الميداليات', 'medal': 'الميدالية'},
                color_discrete_map=medal_colors
            )
            fig_medals.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_medals, use_container_width=True)

        # أعلى المتزلجين بالنقاط
        st.subheader("🌟 أعلى المتزلجين بالنقاط")
        top_scorers = (
            df_results.groupby('skater_name')['total_score']
            .max()
            .reset_index()
            .sort_values('total_score', ascending=False)
            .head(10)
        )
        top_scorers.columns = ['المتزلج', 'أعلى نقاط']
        fig_top = px.bar(
            top_scorers,
            x='المتزلج',
            y='أعلى نقاط',
            title='🏆 أعلى 10 متزلجين بالنقاط',
            color='أعلى نقاط',
            color_continuous_scale='viridis'
        )
        fig_top.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_top, use_container_width=True)

    # مخطط توزيع البطولات حسب النوع
    if not df_comps.empty and 'comp_type' in df_comps.columns:
        type_counts = df_comps['comp_type'].value_counts().reset_index()
        type_counts.columns = ['نوع البطولة', 'العدد']
        fig_types = px.pie(
            type_counts,
            values='العدد',
            names='نوع البطولة',
            title='📊 توزيع البطولات حسب النوع'
        )
        st.plotly_chart(fig_types, use_container_width=True)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def show_competition_page(lang='ar'):
    """الدالة الرئيسية لصفحة البطولات"""
    ar = lang == 'ar'

    # تهيئة قاعدة البيانات
    try:
        _init_db()
    except Exception as e:
        st.error(f"خطأ في تهيئة قاعدة البيانات: {e}")
        return

    st.title("🏆 إدارة البطولات")
    st.markdown("إدارة شاملة للبطولات والتسجيلات والنتائج" if ar else "Competition Management")

    tabs = st.tabs([
        "🏆 البطولات",
        "📋 التسجيل",
        "🏅 النتائج",
        "📊 الإحصائيات"
    ])

    with tabs[0]:
        try:
            _tab_competitions()
        except Exception as e:
            st.error(f"خطأ في تبويب البطولات: {e}")

    with tabs[1]:
        try:
            _tab_entries()
        except Exception as e:
            st.error(f"خطأ في تبويب التسجيل: {e}")

    with tabs[2]:
        try:
            _tab_results()
        except Exception as e:
            st.error(f"خطأ في تبويب النتائج: {e}")

    with tabs[3]:
        try:
            _tab_statistics()
        except Exception as e:
            st.error(f"خطأ في تبويب الإحصائيات: {e}")


# ---------------------------------------------------------------------------
# Standalone run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    show_competition_page()
