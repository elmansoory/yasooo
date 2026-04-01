"""
صفحة جدول التدريبات
"""
import streamlit as st
from datetime import datetime, time
import pandas as pd
from sqlalchemy import func
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.database.models import Schedule, Skater


def show_schedule_page(db_manager):
    """صفحة جدول التدريبات"""
    st.title("📆 جدول التدريبات")

    tabs = st.tabs([
        "📅 الجدول الأسبوعي",
        "➕ إضافة حصة",
        "✏️ إدارة الحصص"
    ])

    with tabs[0]:
        show_weekly_schedule(db_manager)

    with tabs[1]:
        show_add_session(db_manager)

    with tabs[2]:
        show_manage_sessions(db_manager)


def show_weekly_schedule(db_manager):
    """عرض الجدول الأسبوعي"""
    st.subheader("📅 الجدول الأسبوعي")

    try:
        with db_manager.get_session() as session:
            # جلب جميع الحصص النشطة
            schedules = session.query(Schedule).filter(
                Schedule.is_active == True
            ).order_by(Schedule.day_of_week, Schedule.start_time).all()

            if not schedules:
                st.info("📝 لا توجد حصص مجدولة. قم بإضافة حصص من تبويب 'إضافة حصة'")
                return

            # أسماء الأيام
            days_arabic = {
                0: "الإثنين",
                1: "الثلاثاء",
                2: "الأربعاء",
                3: "الخميس",
                4: "الجمعة",
                5: "السبت",
                6: "الأحد"
            }

            # تنظيم الحصص حسب اليوم
            schedule_by_day = {}
            for schedule in schedules:
                day = schedule.day_of_week
                if day not in schedule_by_day:
                    schedule_by_day[day] = []
                schedule_by_day[day].append(schedule)

            # عرض الجدول
            for day_num in range(7):
                if day_num in schedule_by_day:
                    st.markdown(f"### 📅 {days_arabic[day_num]}")

                    for schedule in schedule_by_day[day_num]:
                        # الحصول على اسم المدرب
                        coach_name = "غير محدد"
                        if schedule.coach_id:
                            coach = session.query(Skater).filter(
                                Skater.id == schedule.coach_id
                            ).first()
                            if coach:
                                coach_name = coach.name

                        # عرض الحصة
                        with st.container():
                            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

                            with col1:
                                st.write(f"⏰ **{schedule.start_time} - {schedule.end_time}**")

                            with col2:
                                session_type_emoji = "🧊" if schedule.session_type == "on-ice" else "🏃"
                                st.write(f"{session_type_emoji} {schedule.session_type}")

                            with col3:
                                st.write(f"🎯 {schedule.level or 'الكل'}")

                            with col4:
                                st.write(f"👨‍🏫 {coach_name}")

                            if schedule.notes:
                                st.caption(f"📝 {schedule.notes}")

                            st.markdown("---")

    except Exception as e:
        st.error(f"❌ خطأ: {e}")


def show_add_session(db_manager):
    """إضافة حصة جديدة"""
    st.subheader("➕ إضافة حصة تدريب")

    try:
        with db_manager.get_session() as session:
            # الحصول على المدربين
            coaches = session.query(Skater).filter(
                Skater.notes.like('%مدرب%')
            ).all()

            col1, col2 = st.columns(2)

            with col1:
                # اليوم
                days_arabic = {
                    "الإثنين": 0,
                    "الثلاثاء": 1,
                    "الأربعاء": 2,
                    "الخميس": 3,
                    "الجمعة": 4,
                    "السبت": 5,
                    "الأحد": 6
                }

                selected_day = st.selectbox(
                    "📅 اليوم",
                    options=list(days_arabic.keys())
                )
                day_of_week = days_arabic[selected_day]

                # وقت البداية
                start_time = st.time_input(
                    "⏰ وقت البداية",
                    value=time(9, 0)
                )

                # وقت النهاية
                end_time = st.time_input(
                    "⏰ وقت النهاية",
                    value=time(10, 0)
                )

            with col2:
                # نوع الحصة
                session_type = st.selectbox(
                    "نوع الحصة",
                    ["on-ice", "off-ice"]
                )

                # المستوى
                level = st.selectbox(
                    "🎯 المستوى",
                    ["الكل", "Alpha", "Beta", "Gamma", "Delta", "Epsilon"]
                )

                # المدرب
                if coaches:
                    coach_options = {c.name: c.id for c in coaches}
                    coach_options["غير محدد"] = None

                    selected_coach = st.selectbox(
                        "👨‍🏫 المدرب",
                        options=list(coach_options.keys())
                    )
                    coach_id = coach_options[selected_coach]
                else:
                    st.info("⚠️ لا يوجد مدربين في النظام")
                    coach_id = None

            # الحد الأقصى
            max_capacity = st.number_input(
                "👥 الحد الأقصى للعدد",
                min_value=1,
                max_value=50,
                value=15,
                help="عدد الأعضاء المسموح به في الحصة"
            )

            # ملاحظات
            notes = st.text_area(
                "📝 ملاحظات",
                help="أي ملاحظات إضافية عن الحصة"
            )

            # زر الحفظ
            st.markdown("---")
            col1, col2, col3 = st.columns([1, 2, 1])

            with col2:
                if st.button("💾 إضافة الحصة", width='stretch', type="primary"):
                    try:
                        # التحقق من الأوقات
                        if start_time >= end_time:
                            st.error("❌ وقت البداية يجب أن يكون قبل وقت النهاية")
                            return

                        # إنشاء الحصة
                        schedule = Schedule(
                            day_of_week=day_of_week,
                            start_time=start_time.strftime('%H:%M'),
                            end_time=end_time.strftime('%H:%M'),
                            session_type=session_type,
                            level=level if level != "الكل" else None,
                            coach_id=coach_id,
                            max_capacity=max_capacity,
                            is_active=True,
                            notes=notes
                        )

                        session.add(schedule)
                        session.commit()

                        st.success("✅ تمت إضافة الحصة بنجاح!")
                        st.balloons()

                    except Exception as e:
                        st.error(f"❌ خطأ في الحفظ: {e}")

    except Exception as e:
        st.error(f"❌ خطأ: {e}")


def show_manage_sessions(db_manager):
    """إدارة الحصص"""
    st.subheader("✏️ إدارة الحصص المجدولة")

    try:
        with db_manager.get_session() as session:
            # جلب جميع الحصص
            schedules = session.query(Schedule).order_by(
                Schedule.day_of_week, Schedule.start_time
            ).all()

            if not schedules:
                st.info("📝 لا توجد حصص مجدولة")
                return

            # أسماء الأيام
            days_arabic = {
                0: "الإثنين",
                1: "الثلاثاء",
                2: "الأربعاء",
                3: "الخميس",
                4: "الجمعة",
                5: "السبت",
                6: "الأحد"
            }

            st.markdown(f"### 📊 إجمالي الحصص: {len(schedules)}")
            st.markdown("---")

            # عرض الحصص
            for schedule in schedules:
                # الحصول على اسم المدرب
                coach_name = "غير محدد"
                if schedule.coach_id:
                    coach = session.query(Skater).filter(
                        Skater.id == schedule.coach_id
                    ).first()
                    if coach:
                        coach_name = coach.name

                # عرض الحصة
                with st.expander(
                    f"{'🟢' if schedule.is_active else '🔴'} {days_arabic[schedule.day_of_week]} - "
                    f"{schedule.start_time} إلى {schedule.end_time} - "
                    f"{schedule.level or 'الكل'}"
                ):
                    col1, col2 = st.columns(2)

                    with col1:
                        st.write(f"**اليوم:** {days_arabic[schedule.day_of_week]}")
                        st.write(f"**الوقت:** {schedule.start_time} - {schedule.end_time}")
                        st.write(f"**النوع:** {'🧊 On-Ice' if schedule.session_type == 'on-ice' else '🏃 Off-Ice'}")

                    with col2:
                        st.write(f"**المستوى:** {schedule.level or 'الكل'}")
                        st.write(f"**المدرب:** {coach_name}")
                        st.write(f"**الحد الأقصى:** {schedule.max_capacity} شخص")
                        st.write(f"**الحالة:** {'✅ نشط' if schedule.is_active else '❌ غير نشط'}")

                    if schedule.notes:
                        st.info(f"📝 **ملاحظات:** {schedule.notes}")

                    # أزرار التحكم
                    st.markdown("---")
                    col_btn1, col_btn2, col_btn3 = st.columns(3)

                    with col_btn1:
                        # تبديل الحالة
                        new_status = not schedule.is_active
                        status_label = "🔴 تعطيل" if schedule.is_active else "🟢 تفعيل"

                        if st.button(status_label, key=f"toggle_{schedule.id}"):
                            schedule.is_active = new_status
                            session.commit()
                            st.success(f"✅ تم {'تعطيل' if not new_status else 'تفعيل'} الحصة")
                            st.rerun()

                    with col_btn2:
                        if st.button("✏️ تعديل", key=f"edit_{schedule.id}"):
                            st.info("🚧 ميزة التعديل قيد التطوير...")

                    with col_btn3:
                        if st.button("🗑️ حذف", key=f"delete_{schedule.id}"):
                            if st.session_state.get(f'confirm_delete_schedule_{schedule.id}', False):
                                session.delete(schedule)
                                session.commit()
                                st.success("✅ تم حذف الحصة")
                                st.rerun()
                            else:
                                st.session_state[f'confirm_delete_schedule_{schedule.id}'] = True
                                st.warning("⚠️ اضغط مرة أخرى للتأكيد")

    except Exception as e:
        st.error(f"❌ خطأ: {e}")
