"""
🏆 مختبر معايير الاختبار — Test Standards Lab
يسمح للمدرب بإدخال معايير مرجعية (من فيديوهات أو كتب تدريب) وتقييم أداء لاعب مُحلَّل
مقابلها آلياً — لمعرفة هل اجتاز الاختبار أم لا.
"""
import streamlit as st

from src.analysis.test_standards import (
    list_standards, save_standard, delete_standard, evaluate,
    CATEGORY_JUMP, CATEGORY_SPIN, CATEGORY_POSITION, CATEGORY_SEQUENCE,
)

_CAT_LABELS = {
    CATEGORY_JUMP: '🦘 قفزة', CATEGORY_SPIN: '🌀 دوران',
    CATEGORY_POSITION: '🧍 وضعية', CATEGORY_SEQUENCE: '👣 تسلسل خطوات',
}
_STATUS_STYLE = {
    'pass':   ('✅', '#16a34a', '#f0fdf4', '#bbf7d0'),
    'warn':   ('⚠️', '#b45309', '#fffbeb', '#fde68a'),
    'fail':   ('❌', '#dc2626', '#fef2f2', '#fecaca'),
    'manual': ('🖊️', '#475569', '#f8fafc', '#e2e8f0'),
}


def show_test_standards_page(lang: str = 'ar'):
    try:
        from src.utils.ysoo_theme import inject_theme_css
        st.markdown(inject_theme_css(), unsafe_allow_html=True)
    except Exception:
        pass

    st.markdown("""
    <div style="text-align:center;padding:20px 0 10px">
      <h1 style="font-size:2.2em;background:linear-gradient(135deg,#1e3a5f,#2d6a9f,#4a9fd4);
                 -webkit-background-clip:text;-webkit-text-fill-color:transparent;margin:0">
        🏆 مختبر معايير الاختبار
      </h1>
      <p style="color:#64748b;font-size:1.05em;margin-top:6px">
        أدخل معايير اختبار مرجعية (فيديو أو كتاب) وقارن أداء أي لاعب مُحلَّل بها لمعرفة النجاح من عدمه
      </p>
    </div>
    """, unsafe_allow_html=True)

    tabs = st.tabs(["🎯 تقييم لاعب", "📚 المعايير المرجعية", "➕ إضافة معيار جديد"])

    with tabs[0]:
        _tab_evaluate()
    with tabs[1]:
        _tab_standards_library()
    with tabs[2]:
        _tab_add_standard()


# ============================================================================
# TAB: EVALUATE
# ============================================================================

def _tab_evaluate():
    results = st.session_state.get('analysis_results')
    if not results:
        st.info(
            "لا يوجد تحليل فيديو محمَّل حالياً — اذهب لصفحة 🧪 مختبر تحليل الفيديو وارفع/حلّل "
            "فيديو أولاً (أو استخدم العرض التجريبي)، ثم عد هنا للتقييم."
        )
        return

    standards = list_standards()
    if not standards:
        st.warning("لا توجد معايير مرجعية بعد — أضف واحداً من تبويب «➕ إضافة معيار جديد».")
        return

    names = {f"{s['name_ar']} ({len(s['elements'])} عناصر)": s for s in standards}
    chosen_label = st.selectbox("اختر المعيار المرجعي للمقارنة:", list(names.keys()))
    standard = names[chosen_label]

    st.caption(f"📎 المصدر: {standard.get('source_note', '—')}")

    with st.expander("📋 عناصر هذا المعيار ومعاييرها"):
        for el in standard['elements']:
            st.markdown(f"**{_CAT_LABELS.get(el['category'], '')} {el['name_ar']}**")
            for note in el.get('criteria_notes_ar', []):
                st.caption(f"• {note}")

    st.markdown("---")

    # Manual overrides for element categories with no automatic detector
    manual_overrides = {}
    manual_elements = [el for el in standard['elements'] if el['category'] == CATEGORY_POSITION]
    if manual_elements:
        st.markdown("**عناصر تحتاج تقييماً يدوياً من المدرب (لا يوجد كاشف آلي لها بعد):**")
        for el in manual_elements:
            choice = st.radio(
                el['name_ar'], ['لم يُقيَّم بعد', 'نجح ✅', 'لم ينجح ❌'],
                horizontal=True, key=f"manual_{el['key']}"
            )
            if choice != 'لم يُقيَّم بعد':
                manual_overrides[el['key']] = (choice == 'نجح ✅')

    if st.button("🚀 قيّم الأداء مقابل هذا المعيار", type="primary", use_container_width=True):
        report = evaluate(results, standard, manual_overrides)
        st.session_state['last_standard_report'] = report

    report = st.session_state.get('last_standard_report')
    if report and report['standard_name_ar'] == standard['name_ar']:
        _render_report(report)


def _render_report(report):
    st.markdown("---")
    if report['passed']:
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#166534,#16a34a);border-radius:16px;
                    padding:24px;text-align:center;color:white;margin-bottom:20px">
          <div style="font-size:2em;font-weight:900">✅ PASSED — {report['standard_name_ar']}</div>
          <div style="opacity:.85;margin-top:4px">تم استيفاء جميع عناصر هذا المعيار</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#7f1d1d,#dc2626);border-radius:16px;
                    padding:24px;text-align:center;color:white;margin-bottom:20px">
          <div style="font-size:2em;font-weight:900">❌ NOT YET — {report['standard_name_ar']}</div>
          <div style="opacity:.85;margin-top:4px">عنصر واحد أو أكثر لم يستوفِ المعيار المطلوب — راجع التفاصيل أدناه</div>
        </div>
        """, unsafe_allow_html=True)

    for el in report['elements']:
        icon, color, bg, border = _STATUS_STYLE.get(el['status'], _STATUS_STYLE['manual'])
        match_note = f" — تم مطابقته بـ: {el['matched_type']}" if el.get('matched_type') else ''
        st.markdown(f"""
        <div style="border:1px solid {border};background:{bg};border-radius:12px;
                    padding:14px 18px;margin-bottom:6px">
          <div style="font-weight:800;color:{color};font-size:1.05em">
            {icon} {_CAT_LABELS.get(el['category'], '')} {el['name_ar']}{match_note}
          </div>
        </div>
        """, unsafe_allow_html=True)
        for c in el['checks']:
            mark = '✅' if c['ok'] is True else ('❌' if c['ok'] is False else '➖')
            st.markdown(f"&nbsp;&nbsp;&nbsp;{mark} {c['label_ar']}")
        st.markdown("")

    st.caption(
        "⚠️ هذا التقييم استدلالي مبني على بيانات الحركة المستخرجة فعلياً من الفيديو بنسب ثقة "
        "متفاوتة (راجع لوحة «دقة التحليل وحدود اللقطة» في صفحة التحليل) — وليس حكماً رسمياً "
        "نهائياً. العناصر المعلَّمة «يتطلب مراجعة يدوية» يجب أن يقررها المدرب بنفسه."
    )


# ============================================================================
# TAB: STANDARDS LIBRARY
# ============================================================================

def _tab_standards_library():
    standards = list_standards()
    if not standards:
        st.info("لا توجد معايير محفوظة بعد.")
        return

    for s in standards:
        with st.expander(f"📚 {s['name_ar']} ({s['name_en']}) — {len(s['elements'])} عناصر"):
            st.caption(f"المصدر: {s.get('source_note', '—')} · أُضيف في: {s.get('created_at', '—')}")
            for el in s['elements']:
                st.markdown(f"**{_CAT_LABELS.get(el['category'], '')} {el['name_ar']}**")
                for note in el.get('criteria_notes_ar', []):
                    st.caption(f"  • {note}")
            _SEEDED_KEYS = ('isi_pre_alpha', 'isi_alpha', 'isi_beta', 'isi_gamma', 'isi_delta', 'isi_freestyle_4')
            if s['key'] not in _SEEDED_KEYS:  # keep seeded references protected
                if st.button("🗑️ حذف هذا المعيار", key=f"del_{s['id']}"):
                    delete_standard(s['id'])
                    st.rerun()


# ============================================================================
# TAB: ADD NEW STANDARD
# ============================================================================

def _tab_add_standard():
    st.markdown(
        "أدخل هنا معطيات معيار اختبار جديد (من فيديو مرجعي، كتاب تدريب، أو منهج اتحاد معين). "
        "أضف عناصره واحداً تلو الآخر، ثم احفظ المعيار بالكامل."
    )

    if 'new_std_elements' not in st.session_state:
        st.session_state['new_std_elements'] = []

    c1, c2 = st.columns(2)
    with c1:
        std_name_ar = st.text_input("اسم المعيار (عربي)", placeholder="مثال: اختبار ISI فريستايل 5")
    with c2:
        std_name_en = st.text_input("Standard name (English)", placeholder="e.g. ISI Freestyle 5")
    source_note = st.text_input("المصدر", placeholder="مثال: فيديو ISI الرسمي / كتاب X صفحة Y")

    st.markdown("---")
    st.markdown("**➕ إضافة عنصر للمعيار:**")

    ec1, ec2, ec3 = st.columns(3)
    with ec1:
        el_name_ar = st.text_input("اسم العنصر", key="el_name_ar", placeholder="مثال: قفزة Axel")
    with ec2:
        el_category = st.selectbox(
            "النوع", [CATEGORY_JUMP, CATEGORY_SPIN, CATEGORY_POSITION, CATEGORY_SEQUENCE],
            format_func=lambda c: _CAT_LABELS.get(c, c), key="el_category"
        )
    with ec3:
        el_codes = st.text_input("أكواد للمطابقة (مفصولة بفاصلة)", key="el_codes", placeholder="1A,2A,Axel")

    el_min_rot = el_min_rev = el_min_dur = None
    el_position = ''
    if el_category == CATEGORY_JUMP:
        el_min_rot = st.number_input("عدد الدورات المطلوب كحد أدنى", min_value=0.0, max_value=5.0,
                                      value=1.0, step=0.5, key="el_min_rot")
    elif el_category == CATEGORY_SPIN:
        c4, c5 = st.columns(2)
        with c4:
            el_min_rev = st.number_input("عدد الدورات كحد أدنى", min_value=0, max_value=20, value=6, key="el_min_rev")
        with c5:
            el_position = st.selectbox("الوضعية المطلوبة", ['', 'sit', 'camel', 'upright', 'layback'], key="el_position")
    elif el_category == CATEGORY_SEQUENCE:
        el_min_dur = st.number_input("المدة الدنيا (ثانية)", min_value=0.0, max_value=60.0, value=8.0, key="el_min_dur")

    el_notes = st.text_area(
        "معايير الحكم (سطر لكل معيار)", key="el_notes",
        placeholder="الإقلاع: حافة خارجية أمامية\nدورتان ونصف\nالهبوط: القدم المقابلة"
    )

    if st.button("➕ أضف هذا العنصر للقائمة"):
        if not el_name_ar:
            st.error("أدخل اسم العنصر أولاً")
        else:
            el = {
                'key': f"custom_{len(st.session_state['new_std_elements'])}_{el_name_ar}",
                'name_ar': el_name_ar, 'name_en': el_name_ar,
                'category': el_category,
                'match_codes': [c.strip() for c in el_codes.split(',') if c.strip()],
                'criteria_notes_ar': [ln.strip() for ln in el_notes.split('\n') if ln.strip()],
            }
            if el_category == CATEGORY_JUMP:
                el['min_rotations'] = el_min_rot
            elif el_category == CATEGORY_SPIN:
                el['min_revolutions'] = el_min_rev
                if el_position:
                    el['position'] = el_position
            elif el_category == CATEGORY_SEQUENCE:
                el['min_duration'] = el_min_dur
            st.session_state['new_std_elements'].append(el)
            st.success(f"تمت إضافة «{el_name_ar}» — أضف عناصر أخرى أو احفظ المعيار كاملاً أدناه")

    if st.session_state['new_std_elements']:
        st.markdown("---")
        st.markdown(f"**العناصر المضافة حتى الآن ({len(st.session_state['new_std_elements'])}):**")
        for i, el in enumerate(st.session_state['new_std_elements'], 1):
            col_a, col_b = st.columns([5, 1])
            col_a.markdown(f"{i}. {_CAT_LABELS.get(el['category'], '')} **{el['name_ar']}**")
            if col_b.button("🗑️", key=f"rm_new_{i}"):
                st.session_state['new_std_elements'].pop(i - 1)
                st.rerun()

        st.markdown("---")
        if st.button("💾 احفظ المعيار كاملاً", type="primary", use_container_width=True):
            if not std_name_ar:
                st.error("أدخل اسم المعيار أولاً")
            else:
                save_standard(std_name_ar, std_name_en or std_name_ar, source_note,
                               st.session_state['new_std_elements'])
                st.session_state['new_std_elements'] = []
                st.success(f"✅ تم حفظ معيار «{std_name_ar}» بنجاح — متاح الآن في تبويب التقييم")
                st.balloons()
