"""
صفحة استيراد بيانات من إكسل - رفع ملف شهري (حضور/عضويات) ومعاينته قبل الحفظ.
Excel import page: upload → parse → preview/diff → explicit confirm → commit.
"""
import hashlib

import pandas as pd
import streamlit as st

from src.importer.parser import parse_workbook
from src.importer.service import build_preview, commit_import

_SHEET_TYPE_ICON = {
    'roster': '👥', 'payments': '💳',
    'attendance_grid_3col': '📅', 'attendance_grid_1col': '📅',
    'monthly_report': 'ℹ️', 'empty': '⚪', 'unknown': '⚠️',
}


def show_import_page(get_data, execute_query, get_connection, clear_cache):
    st.title("📥 استيراد بيانات من إكسل")
    st.caption("ارفع ملف الحضور أو العضويات الشهري بنفس الشكل المعتاد، وسيقوم النظام بمعاينة البيانات قبل حفظها.")

    conn = get_connection()

    uploaded = st.file_uploader("اختر ملف إكسل (.xlsx)", type=["xlsx"])
    if uploaded is None:
        st.info("لم يتم اختيار ملف بعد. بعد رفع الملف ستظهر لك معاينة كاملة قبل حفظ أي بيانات.")
        return

    file_bytes = uploaded.getvalue()
    file_hash = hashlib.sha256(file_bytes).hexdigest()

    if st.session_state.get("import_file_hash") != file_hash:
        with st.spinner("جاري تحليل الملف..."):
            try:
                parsed = parse_workbook(file_bytes)
            except Exception as exc:
                st.error(f"⚠️ تعذّر قراءة الملف: {exc}")
                return
        st.session_state["import_file_hash"] = file_hash
        st.session_state["import_parsed"] = parsed
        st.session_state["import_committed"] = False

    parsed = st.session_state["import_parsed"]

    st.markdown("### 📋 ما تم التعرف عليه في الملف")
    for note in parsed["sheet_notes"]:
        icon = _SHEET_TYPE_ICON.get(note["type"], "⚠️")
        st.write(f"{icon} **{note['sheet']}** — {note['message']}")

    unknown_sheets = [n for n in parsed["sheet_notes"] if n["type"] == "unknown"]
    if unknown_sheets:
        st.warning(
            "بعض الأوراق لم يتم التعرف على شكلها تلقائياً ولن يتم استيراد أي بيانات منها "
            "(هذا متوقع لأوراق الأسعار/المرجعية، لكن تأكد أنها ليست ورقة بيانات مهمة)."
        )

    if not any(parsed[k] for k in ("roster_rows", "payment_rows", "attendance_rows")):
        st.info("لا توجد بيانات قابلة للاستيراد في هذا الملف.")
        return

    with st.spinner("جاري مقارنة البيانات بقاعدة البيانات الحالية..."):
        preview = build_preview(conn, parsed)
    st.session_state["import_preview"] = preview

    st.markdown("---")
    st.markdown("### 🔍 معاينة قبل الحفظ")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("👤 أعضاء جدد", len(preview["new_members"]))
    c2.metric("✏️ تحديثات بيانات أعضاء", len(preview["matched_updates"]))
    c3.metric("💳 دفعات جديدة", len(preview["payments_new"]))
    c4.metric("📅 سجلات حضور جديدة", len(preview["attendance_new"]))

    d1, d2, d3 = st.columns(3)
    d1.metric("⏭️ دفعات مكررة (لن تُضاف)", len(preview["payments_dup"]))
    d2.metric("⏭️ حضور مكرر (لن يُضاف)", len(preview["attendance_dup"]))
    unmatched_total = sum(c for _, c in preview["attendance_unmatched"])
    d3.metric("❓ حضور بأسماء غير معروفة", unmatched_total)

    tabs = st.tabs(["👤 أعضاء جدد", "✏️ تحديثات", "💳 الدفعات", "📅 الحضور", "❓ أسماء غير معروفة"])

    with tabs[0]:
        if preview["new_members"]:
            st.dataframe(pd.DataFrame(preview["new_members"]), use_container_width=True, hide_index=True)
            st.caption("سيتم إنشاء هؤلاء الأعضاء تلقائياً عند التأكيد.")
        else:
            st.write("لا يوجد أعضاء جدد.")

    with tabs[1]:
        if preview["matched_updates"]:
            rows = []
            for u in preview["matched_updates"]:
                for field, val in u["changes"].items():
                    rows.append({"العضو": u["name"], "الحقل": field, "القيمة الجديدة": val})
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            st.caption("سيتم ملء الحقول الفارغة فقط، ولن يتم استبدال أي بيانات موجودة بالفعل.")
        else:
            st.write("لا توجد تحديثات على بيانات أعضاء حاليين.")

    with tabs[2]:
        if preview["payments_new"]:
            st.write(f"**{len(preview['payments_new'])} دفعة جديدة ستتم إضافتها:**")
            st.dataframe(pd.DataFrame(preview["payments_new"])[["name", "bundle", "amount", "discount", "payment_date"]],
                         use_container_width=True, hide_index=True)
        else:
            st.write("لا توجد دفعات جديدة.")
        if preview["payments_dup"]:
            with st.expander(f"⏭️ {len(preview['payments_dup'])} دفعة مكررة (موجودة بالفعل، لن تُضاف)"):
                st.dataframe(pd.DataFrame(preview["payments_dup"])[["name", "bundle", "amount", "payment_date"]],
                             use_container_width=True, hide_index=True)

    with tabs[3]:
        if preview["attendance_new"]:
            st.write(f"**{len(preview['attendance_new'])} سجل حضور جديد سيتم إضافته:**")
            sample_df = pd.DataFrame(preview["attendance_new"])[["name", "date", "session_type", "coach"]]
            st.dataframe(sample_df.head(200), use_container_width=True, hide_index=True)
            if len(sample_df) > 200:
                st.caption(f"عرض أول 200 سجل فقط من إجمالي {len(sample_df)}.")
        else:
            st.write("لا توجد سجلات حضور جديدة.")

    with tabs[4]:
        if preview["attendance_unmatched"]:
            st.warning("هذه الأسماء ظهرت في جدول الحضور ولكن لم يتم العثور عليها كأعضاء، ولن يتم تسجيل حضورهم:")
            st.dataframe(
                pd.DataFrame(preview["attendance_unmatched"], columns=["الاسم", "عدد المرات"]),
                use_container_width=True, hide_index=True,
            )
            st.caption("تأكد من أن هذه الأسماء صحيحة (وليست أسماء مدربين أو أخطاء إملائية)، ثم أضفهم كأعضاء وأعد رفع الملف إذا لزم الأمر.")
        else:
            st.write("لا توجد أسماء غير معروفة.")

    st.markdown("---")
    nothing_to_commit = not any([
        preview["new_members"], preview["matched_updates"],
        preview["payments_new"], preview["attendance_new"],
    ])

    if st.session_state.get("import_committed"):
        st.success("✅ تم استيراد هذا الملف بالفعل. ارفع ملفاً آخر لاستيراد بيانات جديدة.")
        return

    if nothing_to_commit:
        st.info("لا توجد بيانات جديدة لحفظها (كل شيء في هذا الملف موجود بالفعل في قاعدة البيانات).")
        return

    confirm = st.checkbox("لقد راجعت المعاينة أعلاه وأريد حفظ هذه البيانات في قاعدة البيانات.")
    if st.button("✅ تأكيد الاستيراد", type="primary", disabled=not confirm):
        with st.spinner("جاري حفظ البيانات..."):
            result = commit_import(conn, preview)
        clear_cache()
        st.session_state["import_committed"] = True
        st.success(
            f"✅ تم الاستيراد بنجاح: {result['added_members']} عضو جديد، "
            f"{result['updated_members']} تحديث بيانات، "
            f"{result['added_payments']} دفعة جديدة، "
            f"{result['added_attendance']} سجل حضور جديد."
        )
        st.rerun()
