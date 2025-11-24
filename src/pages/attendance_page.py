"""
صفحة الحضور والغياب
"""
import streamlit as st
from datetime import datetime, date, timedelta
import pandas as pd
from sqlalchemy import func
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.database.models import Attendance, Skater


def show_attendance_page(db_manager):
    """صفحة الحضور والغياب"""
    st.title("📅 نظام الحضور والغياب")

    tabs = st.tabs([
        "📝 تسجيل حضور",
        "📊 تقارير الحضور",
        "📈 إحصائيات",
        "📥 استيراد بيانات"
    ])

    with tabs[0]:
        show_attendance_recording(db_manager)

    with tabs[1]:
        show_attendance_reports(db_manager)

    with tabs[2]:
        show_attendance_statistics(db_manager)

    with tabs[3]:
        show_attendance_import(db_manager)


def show_attendance_recording(db_manager):
    """تسجيل الحضور"""
    st.subheader("📝 تسجيل حضور اليوم")

    col1, col2 = st.columns([2, 1])

    with col1:
        selected_date = st.date_input(
            "📅 التاريخ",
            value=date.today(),
            help="اختر تاريخ الحصة"
        )

    with col2:
        session_type = st.selectbox(
            "نوع الحصة",
            ["On-Ice", "Off-Ice", "Competition"]
        )

    st.markdown("---")

    # قائمة الأعضاء
    try:
        with db_manager.get_session() as session:
            # الحصول على جميع الأعضاء
            members = session.query(Skater).filter(
                ~Skater.notes.like('%مدرب%')
            ).order_by(Skater.name).all()

            if not members:
                st.warning("⚠️ لا يوجد أعضاء لتسجيل حضورهم")
                return

            st.info(f"👥 عدد الأعضاء: {len(members)}")

            # عرض الأعضاء مع checkboxes
            st.markdown("### ✅ تحديد الحاضرين")

            # تقسيم لثلاثة أعمدة
            cols = st.columns(3)

            attendance_data = []

            for idx, member in enumerate(members):
                col = cols[idx % 3]

                with col:
                    # التحقق من الحضور السابق لهذا اليوم
                    existing = session.query(Attendance).filter(
                        Attendance.skater_id == member.id,
                        func.date(Attendance.date) == selected_date
                    ).first()

                    default_value = existing.status == 'present' if existing else False

                    is_present = st.checkbox(
                        f"{member.name}",
                        value=default_value,
                        key=f"member_{member.id}"
                    )

                    attendance_data.append({
                        'id': member.id,
                        'name': member.name,
                        'status': 'present' if is_present else 'absent'
                    })

            st.markdown("---")

            # زر الحفظ
            col1, col2, col3 = st.columns([1, 2, 1])

            with col2:
                if st.button("💾 حفظ الحضور", use_container_width=True, type="primary"):
                    try:
                        saved_count = 0
                        updated_count = 0

                        for data in attendance_data:
                            # البحث عن سجل موجود
                            existing = session.query(Attendance).filter(
                                Attendance.skater_id == data['id'],
                                func.date(Attendance.date) == selected_date
                            ).first()

                            if existing:
                                # تحديث
                                existing.status = data['status']
                                existing.session_type = session_type
                                updated_count += 1
                            else:
                                # إضافة جديد
                                attendance = Attendance(
                                    skater_id=data['id'],
                                    date=datetime.combine(selected_date, datetime.min.time()),
                                    status=data['status'],
                                    session_type=session_type,
                                    recorded_by="النظام"
                                )
                                session.add(attendance)
                                saved_count += 1

                        st.success(f"✅ تم حفظ الحضور! ({saved_count} جديد، {updated_count} محدث)")
                        st.balloons()

                    except Exception as e:
                        st.error(f"❌ خطأ في الحفظ: {e}")

    except Exception as e:
        st.error(f"❌ خطأ: {e}")


def show_attendance_reports(db_manager):
    """تقارير الحضور"""
    st.subheader("📊 تقارير الحضور")

    col1, col2 = st.columns(2)

    with col1:
        start_date = st.date_input("من تاريخ", value=date.today() - timedelta(days=30))

    with col2:
        end_date = st.date_input("إلى تاريخ", value=date.today())

    if st.button("🔍 عرض التقرير", use_container_width=True):
        try:
            with db_manager.get_session() as session:
                # جلب بيانات الحضور
                attendance_records = session.query(
                    Attendance,
                    Skater.name
                ).join(Skater).filter(
                    Attendance.date >= datetime.combine(start_date, datetime.min.time()),
                    Attendance.date <= datetime.combine(end_date, datetime.max.time())
                ).all()

                if not attendance_records:
                    st.warning("⚠️ لا توجد سجلات حضور في هذه الفترة")
                    return

                # تحويل لـ DataFrame
                data = []
                for record, name in attendance_records:
                    data.append({
                        'الاسم': name,
                        'التاريخ': record.date.strftime('%Y-%m-%d'),
                        'الحالة': '✅ حاضر' if record.status == 'present' else '❌ غائب',
                        'نوع الحصة': record.session_type
                    })

                df = pd.DataFrame(data)

                st.markdown(f"### 📊 إجمالي السجلات: {len(df)}")

                # إحصائيات سريعة
                col1, col2, col3 = st.columns(3)

                with col1:
                    present_count = len(df[df['الحالة'] == '✅ حاضر'])
                    st.metric("✅ الحضور", present_count)

                with col2:
                    absent_count = len(df[df['الحالة'] == '❌ غائب'])
                    st.metric("❌ الغياب", absent_count)

                with col3:
                    attendance_rate = (present_count / len(df) * 100) if len(df) > 0 else 0
                    st.metric("📊 نسبة الحضور", f"{attendance_rate:.1f}%")

                st.markdown("---")

                # عرض الجدول
                st.dataframe(df, use_container_width=True, hide_index=True)

                # أزرار التصدير
                col_export1, col_export2 = st.columns(2)

                with col_export1:
                    csv = df.to_csv(index=False, encoding='utf-8-sig')
                    st.download_button(
                        label="📥 تصدير Excel (CSV)",
                        data=csv,
                        file_name=f"attendance_report_{start_date}_{end_date}.csv",
                        mime="text/csv"
                    )

                with col_export2:
                    # تقرير منسق
                    report_text = generate_attendance_report(df, start_date, end_date, present_count, absent_count, attendance_rate)
                    st.download_button(
                        label="📄 تقرير منسق (TXT)",
                        data=report_text,
                        file_name=f"attendance_report_{start_date}_{end_date}.txt",
                        mime="text/plain"
                    )

        except Exception as e:
            st.error(f"❌ خطأ: {e}")


def show_attendance_statistics(db_manager):
    """إحصائيات الحضور"""
    st.subheader("📈 إحصائيات الحضور")

    try:
        with db_manager.get_session() as session:
            # أكثر الأعضاء حضوراً
            top_attendees = session.query(
                Skater.name,
                func.count(Attendance.id).label('attendance_count')
            ).join(Attendance).filter(
                Attendance.status == 'present'
            ).group_by(Skater.id).order_by(
                func.count(Attendance.id).desc()
            ).limit(10).all()

            if top_attendees:
                st.markdown("### 🏆 أكثر 10 أعضاء حضوراً")

                for idx, (name, count) in enumerate(top_attendees, 1):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"{idx}. {name}")
                    with col2:
                        st.write(f"✅ {count} حصة")

            # إحصائيات الشهر الحالي
            st.markdown("---")
            st.markdown("### 📅 إحصائيات الشهر الحالي")

            first_day = date.today().replace(day=1)
            total_present = session.query(func.count(Attendance.id)).filter(
                Attendance.status == 'present',
                Attendance.date >= first_day
            ).scalar()

            total_absent = session.query(func.count(Attendance.id)).filter(
                Attendance.status == 'absent',
                Attendance.date >= first_day
            ).scalar()

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("✅ إجمالي الحضور", total_present or 0)

            with col2:
                st.metric("❌ إجمالي الغياب", total_absent or 0)

            with col3:
                total = (total_present or 0) + (total_absent or 0)
                rate = ((total_present or 0) / total * 100) if total > 0 else 0
                st.metric("📊 نسبة الحضور", f"{rate:.1f}%")

    except Exception as e:
        st.error(f"❌ خطأ: {e}")


def show_attendance_import(db_manager):
    """استيراد بيانات الحضور"""
    st.subheader("📥 استيراد بيانات الحضور")

    st.info("""
    💡 **تعليمات الاستيراد:**

    يمكنك استيراد ملف Excel يحتوي على:
    - عمود "الاسم" أو "Name"
    - عمود "التاريخ" أو "Date"
    - عمود "الحالة" أو "Status" (حاضر/غائب)
    """)

    uploaded_file = st.file_uploader(
        "اختر ملف Excel",
        type=['xlsx', 'xls'],
        help="ارفع ملف Excel يحتوي على بيانات الحضور"
    )

    if uploaded_file and st.button("🚀 بدء الاستيراد", type="primary"):
        st.info("🚧 ميزة الاستيراد قيد التطوير...")


def generate_attendance_report(df, start_date, end_date, present_count, absent_count, attendance_rate):
    """إنشاء تقرير حضور منسق"""
    report = f"""
{'='*70}
                    تقرير الحضور والغياب
{'='*70}

📅 الفترة: من {start_date} إلى {end_date}
📊 تاريخ التقرير: {datetime.now().strftime('%Y-%m-%d %H:%M')}

{'='*70}
                        الإحصائيات العامة
{'='*70}

✅ إجمالي الحضور:        {present_count}
❌ إجمالي الغياب:         {absent_count}
📊 نسبة الحضور:           {attendance_rate:.1f}%
📈 إجمالي السجلات:        {len(df)}

{'='*70}
                        تفاصيل الحضور
{'='*70}

"""
    # إضافة تفاصيل الحضور
    for idx, row in df.iterrows():
        report += f"{row['الاسم']:30} | {row['التاريخ']:12} | {row['الحالة']:10} | {row['نوع الحصة']}\n"

    report += f"\n{'='*70}\n"
    report += "                    نهاية التقرير\n"
    report += f"{'='*70}\n"

    return report
