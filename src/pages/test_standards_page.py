"""
🏅 مختبر معايير الاختبار — Test Standards Lab (ISI / ISU)
يسمح للمدرب بإدخال معايير مرجعية (من فيديوهات أو كتب تدريب) وتقييم أداء لاعب مُحلَّل
مقابلها آلياً — لمعرفة هل اجتاز الاختبار أم لا. يدعم اتحادين منفصلين: ISI وISU.
"""
import os
import tempfile

import streamlit as st

from src.analysis.test_standards import (
    list_standards, save_standard, delete_standard, evaluate,
    save_reference_upload, list_reference_uploads,
    save_evaluation, list_evaluations,
    CATEGORY_JUMP, CATEGORY_SPIN, CATEGORY_POSITION, CATEGORY_SEQUENCE,
    FEDERATION_ISI, FEDERATION_ISU,
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

_SEEDED_KEYS = (
    'isi_pre_alpha', 'isi_alpha', 'isi_beta', 'isi_gamma', 'isi_delta', 'isi_freestyle_4',
    'isu_jump_basics',
)

_UPLOAD_DIR = 'data/reference_videos'


def show_federation_exams_page(federation: str, lang: str = 'ar'):
    """federation: FEDERATION_ISI or FEDERATION_ISU"""
    try:
        from src.utils.ysoo_theme import inject_theme_css
        st.markdown(inject_theme_css(), unsafe_allow_html=True)
    except Exception:
        pass

    title = "🏅 امتحانات ISI" if federation == FEDERATION_ISI else "🏅 امتحانات ISU"
    subtitle = (
        "المكتبة الرسمية لمستويات ISI (Pre-Alpha وحتى Freestyle) — رفع الفيديو المرجعي المعتمد "
        "لبناء المكتبة، أو رفع فيديو لاعب لتقييمه مقابل أي مستوى"
        if federation == FEDERATION_ISI else
        "معايير عناصر ISU الفنية — رفع فيديو مرجعي أو كتاب لبناء المكتبة، أو رفع فيديو لاعب "
        "وتقييم أدائه مقابل المعايير الرسمية"
    )

    st.markdown(f"""
    <div style="text-align:center;padding:20px 0 10px">
      <h1 style="font-size:2.2em;background:linear-gradient(135deg,#1e3a5f,#2d6a9f,#4a9fd4);
                 -webkit-background-clip:text;-webkit-text-fill-color:transparent;margin:0">
        {title}
      </h1>
      <p style="color:#64748b;font-size:1.05em;margin-top:6px">{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)

    tabs = st.tabs([
        "📤 رفع فيديو مرجعي معتمد", "🎯 تقييم لاعب", "📚 المكتبة المرجعية", "➕ إضافة معيار يدوياً",
    ])

    with tabs[0]:
        _tab_upload_reference(federation)
    with tabs[1]:
        _tab_evaluate(federation)
    with tabs[2]:
        _tab_standards_library(federation)
    with tabs[3]:
        _tab_add_standard(federation)


# Backward-compatible entry point (existing nav wiring calls this for ISI)
def show_test_standards_page(lang: str = 'ar'):
    show_federation_exams_page(FEDERATION_ISI, lang)


# ============================================================================
# TAB: UPLOAD OFFICIAL REFERENCE VIDEO
# ============================================================================

def _tab_upload_reference(federation: str):
    st.markdown(
        "ارفع هنا الفيديو **الأصلي المعتمد** لأي مستوى أو اختبار لم تُتح فرصة تحليله بعد — "
        "لبناء أكبر مكتبة معايير ممكنة. يُحفظ الفيديو، ثم يمكن استخراج معاييره وإدخالها "
        "في تبويب «➕ إضافة معيار يدوياً» بالرجوع إليه."
    )

    with st.form(f"upload_ref_{federation}"):
        level_name = st.text_input("اسم المستوى/الاختبار", placeholder="مثال: Freestyle 5")
        note = st.text_area("ملاحظات (اختياري)", placeholder="أي سياق إضافي عن هذا الفيديو")
        uploaded = st.file_uploader("ملف الفيديو المرجعي", type=['mp4', 'avi', 'mov', 'mkv'])
        submitted = st.form_submit_button("💾 حفظ الفيديو المرجعي", type="primary", use_container_width=True)

    if submitted:
        if not uploaded or not level_name:
            st.error("أدخل اسم المستوى وارفع ملف الفيديو أولاً")
        else:
            os.makedirs(_UPLOAD_DIR, exist_ok=True)
            suffix = os.path.splitext(uploaded.name)[1] or '.mp4'
            safe_name = f"{federation}_{level_name}_{int(__import__('time').time())}{suffix}"
            dest = os.path.join(_UPLOAD_DIR, safe_name)
            with open(dest, 'wb') as f:
                f.write(uploaded.read())
            save_reference_upload(federation, level_name, note, dest)
            st.success(f"✅ تم حفظ فيديو «{level_name}» — أضف معاييره الآن من تبويب «إضافة معيار يدوياً»")
            st.balloons()

    st.markdown("---")
    uploads = list_reference_uploads(federation)
    if uploads:
        st.markdown(f"**الفيديوهات المرجعية المحفوظة ({len(uploads)}):**")
        for u in uploads:
            linked = "✅ رُبط بمعيار" if u['linked_standard_key'] else "⏳ بانتظار إدخال المعايير"
            with st.expander(f"🎬 {u['level_name']} — {u['uploaded_at']} — {linked}"):
                if u.get('note'):
                    st.caption(u['note'])
                if os.path.exists(u['file_path']):
                    st.video(u['file_path'])
                else:
                    st.warning("الملف غير موجود على القرص حالياً")
    else:
        st.info("لا توجد فيديوهات مرجعية محفوظة بعد لهذا الاتحاد.")


# ============================================================================
# TAB: EVALUATE A PLAYER
# ============================================================================

def _inline_player_upload(federation: str):
    """رفع فيديو لاعب وتحليله بمحرك التحليل الحقيقي مباشرة من هذا التبويب —
    بدون الحاجة للانتقال إلى صفحة مختبر تحليل الفيديو أولاً."""
    uploaded = st.file_uploader(
        "فيديو اللاعب", type=['mp4', 'avi', 'mov', 'mkv'], key=f"player_upload_{federation}",
        help="الحجم الأقصى: 200MB | مدة مثالية: 10-120 ثانية"
    )
    if not uploaded:
        return

    player_name = st.text_input("👤 اسم اللاعب", placeholder="اختياري", key=f"player_name_upl_{federation}")

    if st.button("🚀 حلّل هذا الفيديو الآن", type="primary", use_container_width=True,
                 key=f"analyze_btn_{federation}"):
        try:
            from src.pages.video_analysis_page import SkatingVideoAnalyzer
        except Exception as e:
            st.error(f"تعذّر تحميل محرك التحليل: {e}")
            return

        import tempfile
        from pathlib import Path

        suffix = Path(uploaded.name).suffix or '.mp4'
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded.read())
            tmp_path = tmp.name

        try:
            prog_bar = st.progress(0, text="جارٍ تحليل الفيديو...")

            def update_progress(frac: float, frame: int):
                prog_bar.progress(min(frac, 1.0), text=f"تحليل الإطار {frame} ...")

            analyzer = SkatingVideoAnalyzer()
            results = analyzer.analyze(tmp_path, progress_cb=update_progress)
            prog_bar.progress(1.0, text="✅ اكتمل التحليل")

            if 'error' in results:
                st.error(f"خطأ: {results['error']}")
            else:
                results['player_name'] = player_name
                st.session_state['analysis_results'] = results
                st.success("✅ اكتمل التحليل — اختر معياراً أدناه وقيّم الأداء")
                st.rerun()
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass


def _tab_evaluate(federation: str):
    results = st.session_state.get('analysis_results')
    if not results:
        st.info(
            "ارفع فيديو اللاعب مباشرة هنا لتحليله ثم تقييمه، أو حلّله أولاً من صفحة "
            "🧪 مختبر تحليل الفيديو وعُد لهذا التبويب."
        )
        _inline_player_upload(federation)
        return

    with st.expander("🔄 رفع فيديو لاعب آخر / إعادة التحليل"):
        _inline_player_upload(federation)

    standards = list_standards(federation)
    if not standards:
        st.warning("لا توجد معايير مرجعية لهذا الاتحاد بعد — أضف واحداً من تبويب «➕ إضافة معيار يدوياً».")
        return

    names = {f"{s['name_ar']} ({len(s['elements'])} عناصر)": s for s in standards}
    chosen_label = st.selectbox("اختر المعيار المرجعي للمقارنة:", list(names.keys()))
    standard = names[chosen_label]
    player_name = st.text_input("اسم اللاعب (اختياري، لتسجيله في سجل التقييمات)", key=f"pname_{federation}")

    st.caption(f"📎 المصدر: {standard.get('source_note', '—')}")

    with st.expander("📋 عناصر هذا المعيار ومعاييرها"):
        for el in standard['elements']:
            st.markdown(f"**{_CAT_LABELS.get(el['category'], '')} {el['name_ar']}**")
            for note in el.get('criteria_notes_ar', []):
                st.caption(f"• {note}")

    st.markdown("---")

    manual_overrides = {}
    manual_elements = [el for el in standard['elements'] if el['category'] == CATEGORY_POSITION]
    if manual_elements:
        st.markdown("**عناصر تحتاج تقييماً يدوياً من المدرب (لا يوجد كاشف آلي لها بعد):**")
        for el in manual_elements:
            choice = st.radio(
                el['name_ar'], ['لم يُقيَّم بعد', 'نجح ✅', 'لم ينجح ❌'],
                horizontal=True, key=f"manual_{federation}_{el['key']}"
            )
            if choice != 'لم يُقيَّم بعد':
                manual_overrides[el['key']] = (choice == 'نجح ✅')

    if st.button("🚀 قيّم الأداء مقابل هذا المعيار", type="primary", use_container_width=True, key=f"eval_btn_{federation}"):
        report = evaluate(results, standard, manual_overrides)
        st.session_state[f'last_standard_report_{federation}'] = report
        save_evaluation(federation, standard, report, player_name=player_name)

    report = st.session_state.get(f'last_standard_report_{federation}')
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
        "نهائياً. العناصر المعلَّمة «يتطلب مراجعة يدوية» يجب أن يقررها المدرب بنفسه. تم حفظ "
        "هذا التقييم في سجل بيانات التدريب."
    )


# ============================================================================
# TAB: STANDARDS LIBRARY
# ============================================================================

def _tab_standards_library(federation: str):
    standards = list_standards(federation)
    if not standards:
        st.info("لا توجد معايير محفوظة بعد لهذا الاتحاد.")
        return

    for s in standards:
        with st.expander(f"📚 {s['name_ar']} ({s['name_en']}) — {len(s['elements'])} عناصر"):
            st.caption(f"المصدر: {s.get('source_note', '—')} · أُضيف في: {s.get('created_at', '—')}")
            for el in s['elements']:
                st.markdown(f"**{_CAT_LABELS.get(el['category'], '')} {el['name_ar']}**")
                for note in el.get('criteria_notes_ar', []):
                    st.caption(f"  • {note}")
            if s['key'] not in _SEEDED_KEYS:  # keep seeded references protected
                if st.button("🗑️ حذف هذا المعيار", key=f"del_{federation}_{s['id']}"):
                    delete_standard(s['id'])
                    st.rerun()


# ============================================================================
# TAB: ADD NEW STANDARD (MANUALLY)
# ============================================================================

def _tab_add_standard(federation: str):
    st.markdown(
        "أدخل هنا معطيات معيار اختبار جديد (من فيديو مرجعي رفعته، كتاب تدريب، أو منهج اتحاد "
        "معين). أضف عناصره واحداً تلو الآخر، ثم احفظ المعيار بالكامل."
    )

    key_prefix = f"newstd_{federation}"
    if key_prefix not in st.session_state:
        st.session_state[key_prefix] = []

    c1, c2 = st.columns(2)
    with c1:
        std_name_ar = st.text_input("اسم المعيار (عربي)", key=f"{key_prefix}_name_ar",
                                     placeholder="مثال: اختبار ISI فريستايل 5")
    with c2:
        std_name_en = st.text_input("Standard name (English)", key=f"{key_prefix}_name_en",
                                     placeholder="e.g. ISI Freestyle 5")
    source_note = st.text_input("المصدر", key=f"{key_prefix}_source",
                                 placeholder="مثال: فيديو مرجعي رفعته / كتاب X صفحة Y")

    st.markdown("---")
    st.markdown("**➕ إضافة عنصر للمعيار:**")

    ec1, ec2, ec3 = st.columns(3)
    with ec1:
        el_name_ar = st.text_input("اسم العنصر", key=f"{key_prefix}_el_name_ar", placeholder="مثال: قفزة Axel")
    with ec2:
        el_category = st.selectbox(
            "النوع", [CATEGORY_JUMP, CATEGORY_SPIN, CATEGORY_POSITION, CATEGORY_SEQUENCE],
            format_func=lambda c: _CAT_LABELS.get(c, c), key=f"{key_prefix}_el_category"
        )
    with ec3:
        el_codes = st.text_input("أكواد للمطابقة (مفصولة بفاصلة)", key=f"{key_prefix}_el_codes",
                                  placeholder="1A,2A,Axel")

    el_min_rot = el_min_rev = el_min_dur = None
    el_position = ''
    if el_category == CATEGORY_JUMP:
        el_min_rot = st.number_input("عدد الدورات المطلوب كحد أدنى", min_value=0.0, max_value=5.0,
                                      value=1.0, step=0.5, key=f"{key_prefix}_el_min_rot")
    elif el_category == CATEGORY_SPIN:
        c4, c5 = st.columns(2)
        with c4:
            el_min_rev = st.number_input("عدد الدورات كحد أدنى", min_value=0, max_value=20, value=6,
                                          key=f"{key_prefix}_el_min_rev")
        with c5:
            el_position = st.selectbox("الوضعية المطلوبة", ['', 'sit', 'camel', 'upright', 'layback'],
                                        key=f"{key_prefix}_el_position")
    elif el_category == CATEGORY_SEQUENCE:
        el_min_dur = st.number_input("المدة الدنيا (ثانية)", min_value=0.0, max_value=60.0, value=8.0,
                                      key=f"{key_prefix}_el_min_dur")

    el_notes = st.text_area(
        "معايير الحكم (سطر لكل معيار)", key=f"{key_prefix}_el_notes",
        placeholder="الإقلاع: حافة خارجية أمامية\nدورتان ونصف\nالهبوط: القدم المقابلة"
    )

    if st.button("➕ أضف هذا العنصر للقائمة", key=f"{key_prefix}_addbtn"):
        if not el_name_ar:
            st.error("أدخل اسم العنصر أولاً")
        else:
            el = {
                'key': f"custom_{len(st.session_state[key_prefix])}_{el_name_ar}",
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
            st.session_state[key_prefix].append(el)
            st.success(f"تمت إضافة «{el_name_ar}» — أضف عناصر أخرى أو احفظ المعيار كاملاً أدناه")

    if st.session_state[key_prefix]:
        st.markdown("---")
        st.markdown(f"**العناصر المضافة حتى الآن ({len(st.session_state[key_prefix])}):**")
        for i, el in enumerate(st.session_state[key_prefix], 1):
            col_a, col_b = st.columns([5, 1])
            col_a.markdown(f"{i}. {_CAT_LABELS.get(el['category'], '')} **{el['name_ar']}**")
            if col_b.button("🗑️", key=f"{key_prefix}_rm_{i}"):
                st.session_state[key_prefix].pop(i - 1)
                st.rerun()

        st.markdown("---")
        if st.button("💾 احفظ المعيار كاملاً", type="primary", use_container_width=True, key=f"{key_prefix}_savebtn"):
            if not std_name_ar:
                st.error("أدخل اسم المعيار أولاً")
            else:
                save_standard(std_name_ar, std_name_en or std_name_ar, source_note,
                               st.session_state[key_prefix], federation=federation)
                st.session_state[key_prefix] = []
                st.success(f"✅ تم حفظ معيار «{std_name_ar}» بنجاح — متاح الآن في تبويب التقييم")
                st.balloons()
