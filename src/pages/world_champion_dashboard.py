"""
صفحة مساعد البطولة العالمية - لوحة تدريب متكاملة بالذكاء الاصطناعي.
تضمّن ملف HTML التفاعلي مباشرةً داخل Streamlit.
"""
import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path

_HTML_PATH = Path(__file__).parent.parent.parent / "attached_assets" / "dashboard_1783877143069.html"


def show_world_champion_dashboard(get_data, execute_query, get_connection, clear_cache):
    st.title("🤖 مساعد البطولة العالمية")
    st.caption("نظام تدريب ذكي مبني على معايير ISU — تحليل الأداء، خطط التدريب، ومقارنة أبطال العالم")

    if not _HTML_PATH.exists():
        st.error(f"ملف لوحة التحكم غير موجود: {_HTML_PATH}")
        return

    html_content = _HTML_PATH.read_text(encoding="utf-8")
    components.html(html_content, height=820, scrolling=True)
