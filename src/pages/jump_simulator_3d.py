"""
صفحة محاكي القفزات ثلاثي الأبعاد - Three.js jump physics simulator.
تضمّن ملف HTML التفاعلي مباشرةً داخل Streamlit.
"""
import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path

_HTML_PATH = Path(__file__).parent.parent.parent / "attached_assets" / "3d_simulator_1783877143069.html"


def show_jump_simulator(get_data, execute_query, get_connection, clear_cache):
    st.title("🎮 محاكي القفزات ثلاثي الأبعاد")
    st.caption("اختر نوع القفزة وعدد الدورات واضبط المعلمات الفيزيائية — يحسب النتيجة وفق معايير ISU 2026-2027 تلقائياً")

    if not _HTML_PATH.exists():
        st.error(f"ملف المحاكي غير موجود: {_HTML_PATH}")
        return

    html_content = _HTML_PATH.read_text(encoding="utf-8")
    components.html(html_content, height=750, scrolling=False)
