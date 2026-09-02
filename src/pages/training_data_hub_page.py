"""
🤖 مركز تدريب النموذج — Training Data Hub
يجمع كل ما أُدخل عبر مختبرات ISI وISU (المعايير المرجعية، الفيديوهات المرفوعة،
وسجل التقييمات) في مكان واحد — أساس أي تدريب مستقبلي لنماذج الذكاء الاصطناعي.

ملاحظة صريحة: هذه الصفحة تُصدِّر البيانات المُجمَّعة (JSON) ولا تُعيد تدريب
نماذج AI فعلياً هنا — إعادة التدريب الفعلي (LSTM / MovementClassifier) تتم
من صفحة "🤖 تدريب النموذج" الموجودة أصلاً في القائمة الرئيسية.
"""
import json

import streamlit as st

from src.analysis.test_standards import (
    list_standards, list_evaluations, list_reference_uploads,
    export_training_dataset, FEDERATION_ISI, FEDERATION_ISU,
)


def show_training_data_hub_page(lang: str = 'ar'):
    try:
        from src.utils.ysoo_theme import inject_theme_css, kpi_row_html
        st.markdown(inject_theme_css(), unsafe_allow_html=True)
        THEME_OK = True
    except Exception:
        THEME_OK = False

    st.markdown("""
    <div style="text-align:center;padding:20px 0 10px">
      <h1 style="font-size:2.2em;background:linear-gradient(135deg,#1e3a5f,#2d6a9f,#4a9fd4);
                 -webkit-background-clip:text;-webkit-text-fill-color:transparent;margin:0">
        🤖 مركز تدريب النموذج
      </h1>
      <p style="color:#64748b;font-size:1.05em;margin-top:6px">
        كل المعايير والفيديوهات المرجعية وتقييمات اللاعبين من مختبرَي ISI وISU — مُجمَّعة هنا
        كأساس لأي تدريب مستقبلي للنماذج
      </p>
    </div>
    """, unsafe_allow_html=True)

    isi_standards = list_standards(FEDERATION_ISI)
    isu_standards = list_standards(FEDERATION_ISU)
    isi_uploads = list_reference_uploads(FEDERATION_ISI)
    isu_uploads = list_reference_uploads(FEDERATION_ISU)
    isi_evals = list_evaluations(FEDERATION_ISI)
    isu_evals = list_evaluations(FEDERATION_ISU)

    total_elements = sum(len(s['elements']) for s in isi_standards + isu_standards)

    if THEME_OK:
        st.markdown(kpi_row_html([
            ('📚', 'معايير ISI', str(len(isi_standards))),
            ('📚', 'معايير ISU', str(len(isu_standards))),
            ('🧩', 'إجمالي العناصر', str(total_elements)),
            ('🎬', 'فيديوهات مرجعية', str(len(isi_uploads) + len(isu_uploads))),
            ('🎯', 'تقييمات مسجَّلة', str(len(isi_evals) + len(isu_evals))),
        ]), unsafe_allow_html=True)
    else:
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("📚 معايير ISI", len(isi_standards))
        c2.metric("📚 معايير ISU", len(isu_standards))
        c3.metric("🧩 إجمالي العناصر", total_elements)
        c4.metric("🎬 فيديوهات مرجعية", len(isi_uploads) + len(isu_uploads))
        c5.metric("🎯 تقييمات مسجَّلة", len(isi_evals) + len(isu_evals))

    st.markdown("---")

    tabs = st.tabs(["📊 سجل التقييمات", "📥 تصدير حزمة البيانات", "ℹ️ عن هذا المركز"])

    with tabs[0]:
        _tab_evaluation_log(isi_evals, isu_evals)
    with tabs[1]:
        _tab_export()
    with tabs[2]:
        _tab_about()


def _tab_evaluation_log(isi_evals, isu_evals):
    fed_choice = st.radio("الاتحاد:", ["ISI", "ISU", "كلاهما"], horizontal=True, key="training_hub_fed")
    if fed_choice == "ISI":
        rows = isi_evals
    elif fed_choice == "ISU":
        rows = isu_evals
    else:
        rows = sorted(isi_evals + isu_evals, key=lambda r: r['created_at'], reverse=True)

    if not rows:
        st.info("لا توجد تقييمات مسجَّلة بعد — قيّم أي لاعب من مختبر ISI أو ISU ليظهر هنا تلقائياً.")
        return

    for r in rows:
        icon = "✅" if r['passed'] else "❌"
        player = r['player_name'] or "لاعب غير مسمّى"
        with st.expander(f"{icon} {r['standard_name']} — {player} — {r['created_at']}"):
            st.caption(f"الاتحاد: {r['federation']} · معرّف المعيار: {r['standard_key']}")
            for el in r['report'].get('elements', []):
                st.markdown(f"- **{el['name_ar']}**: {el['status']}")


def _tab_export():
    st.markdown(
        "يجمع هذا التصدير كل المعايير المرجعية (ISI + ISU)، الفيديوهات المرجعية المسجَّلة، "
        "وسجل تقييمات اللاعبين — بصيغة JSON واحدة، جاهزة لاستخدامها لاحقاً في تدريب أو ضبط "
        "أي نموذج ذكاء اصطناعي."
    )
    dataset = export_training_dataset()
    payload = json.dumps(dataset, ensure_ascii=False, indent=2)
    st.download_button(
        "📥 تنزيل حزمة بيانات التدريب (JSON)",
        data=payload.encode('utf-8'),
        file_name=f"yasooo_training_dataset_{dataset['exported_at'].replace(' ', '_').replace(':', '-')}.json",
        mime="application/json",
        use_container_width=True,
    )
    with st.expander("👁️ معاينة سريعة للحزمة"):
        st.json(dataset)


def _tab_about():
    st.markdown("""
    **ماذا يفعل هذا المركز فعلياً؟**

    يجمع البيانات من ثلاثة مصادر:
    1. المعايير المرجعية المُدخلة يدوياً أو المستخرجة من فيديوهات ISI/ISU
    2. الفيديوهات المرجعية الأصلية المرفوعة عبر تبويب «رفع فيديو مرجعي»
    3. سجل كل عملية تقييم لاعب تمت عبر مختبرَي ISI أو ISU

    **ما لا يفعله:** هذه الصفحة لا تُعيد تدريب نماذج الذكاء الاصطناعي (LSTM أو
    MovementClassifier) تلقائياً — فقط تُصدِّر البيانات المُجمَّعة كحزمة جاهزة.
    إعادة التدريب الفعلي للنماذج تتم من صفحة **"🤖 تدريب النموذج"** الموجودة في
    القائمة الرئيسية، والتي تعمل على بيانات حركة مُصنَّفة يدوياً.

    كلما ازداد عدد الفيديوهات والمعايير والتقييمات هنا، زادت جودة أي عملية تدريب
    مستقبلية تعتمد على هذه الحزمة.
    """)
