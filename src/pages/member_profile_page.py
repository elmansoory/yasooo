"""
صفحة ملف العضو الشامل
"""
import streamlit as st
from datetime import datetime, date, timedelta
import pandas as pd
from sqlalchemy import func
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.database.models import Skater, Attendance, Payment, Analysis


def show_member_profile_page(db_manager):
    """صفحة ملف العضو الشامل"""
    st.title("👤 ملف العضو الشامل")

    try:
        with db_manager.get_session() as session:
            # اختيار العضو
            members = session.query(Skater).filter(
                ~Skater.notes.like('%مدرب%')
            ).order_by(Skater.name).all()

            if not members:
                st.warning("⚠️ لا يوجد أعضاء في النظام")
                return

            # قائمة منسدلة لاختيار العضو
            member_options = {f"{m.name} ({m.level or 'N/A'})": m.id for m in members}
            selected_member = st.selectbox(
                "اختر العضو",
                options=list(member_options.keys()),
                key="member_profile_select"
            )

            member_id = member_options[selected_member]

            # جلب بيانات العضو
            member = session.query(Skater).filter(Skater.id == member_id).first()

            if not member:
                st.error("❌ العضو غير موجود")
                return

            # ==================== القسم 1: معلومات العضو ====================
            st.markdown("---")
            st.subheader("📋 المعلومات الأساسية")

            col_info1, col_info2, col_info3 = st.columns([1, 2, 2])

            with col_info1:
                # عرض الصورة إن وجدت
                if member.photo_path:
                    try:
                        st.image(member.photo_path, width=150)
                    except:
                        st.info("📷 لا توجد صورة")
                else:
                    st.info("📷 لا توجد صورة")

            with col_info2:
                st.write(f"**الاسم:** {member.name}")
                st.write(f"**المستوى:** {member.level or 'غير محدد'}")
                st.write(f"**الباقة:** {member.bundle or 'غير محدد'}")
                st.write(f"**تاريخ الميلاد:** {member.date_of_birth or 'غير محدد'}")

            with col_info3:
                st.write(f"**الجنسية:** {member.country or 'مصر'}")
                st.write(f"**المدرب:** {member.coach_name or 'غير محدد'}")
                st.write(f"**الحالة:** {member.membership_status or 'نشط'}")
                if member.email:
                    st.write(f"**البريد:** {member.email}")

            st.markdown("---")

            # ==================== القسم 2: إحصائيات سريعة ====================
            st.subheader("📊 إحصائيات سريعة")

            # حساب الإحصائيات
            total_attendance = session.query(Attendance).filter(
                Attendance.skater_id == member_id,
                Attendance.status == 'present'
            ).count()

            total_absent = session.query(Attendance).filter(
                Attendance.skater_id == member_id,
                Attendance.status == 'absent'
            ).count()

            total_payments = session.query(func.sum(Payment.amount)).filter(
                Payment.skater_id == member_id,
                Payment.status == 'completed'
            ).scalar() or 0

            total_analyses = session.query(Analysis).filter(
                Analysis.skater_id == member_id
            ).count()

            attendance_rate = (total_attendance / (total_attendance + total_absent) * 100) if (total_attendance + total_absent) > 0 else 0

            col1, col2, col3, col4, col5 = st.columns(5)

            with col1:
                st.metric("✅ حضور", total_attendance)

            with col2:
                st.metric("❌ غياب", total_absent)

            with col3:
                st.metric("📊 نسبة الحضور", f"{attendance_rate:.1f}%")

            with col4:
                st.metric("💰 إجمالي المدفوعات", f"{total_payments:,.0f} EGP")

            with col5:
                st.metric("📹 التحليلات", total_analyses)

            st.markdown("---")

            # ==================== القسم 3: حالة الاشتراك ====================
            st.subheader("💳 حالة الاشتراك")

            last_payment = session.query(Payment).filter(
                Payment.skater_id == member_id
            ).order_by(Payment.payment_date.desc()).first()

            if last_payment:
                col_sub1, col_sub2, col_sub3 = st.columns(3)

                with col_sub1:
                    st.write(f"**آخر دفعة:** {last_payment.amount:.2f} EGP")
                    st.write(f"**التاريخ:** {last_payment.payment_date.strftime('%Y-%m-%d')}")

                with col_sub2:
                    st.write(f"**الباقة:** {last_payment.bundle_type}")
                    st.write(f"**الطريقة:** {last_payment.payment_method}")

                with col_sub3:
                    if last_payment.period_end:
                        days_left = (last_payment.period_end - datetime.now()).days
                        if days_left > 0:
                            st.success(f"**ينتهي بعد:** {days_left} يوم")
                        else:
                            st.error(f"**منتهي منذ:** {abs(days_left)} يوم")

                        st.write(f"**تاريخ الانتهاء:** {last_payment.period_end.strftime('%Y-%m-%d')}")
            else:
                st.warning("⚠️ لا توجد مدفوعات مسجلة")

            st.markdown("---")

            # ==================== القسم 4: سجل الحضور ====================
            st.subheader("📅 سجل الحضور (آخر 30 يوم)")

            month_ago = date.today() - timedelta(days=30)
            attendance_records = session.query(Attendance).filter(
                Attendance.skater_id == member_id,
                Attendance.date >= month_ago
            ).order_by(Attendance.date.desc()).all()

            if attendance_records:
                data = []
                for record in attendance_records:
                    status_emoji = "✅" if record.status == "present" else "❌"
                    data.append({
                        'التاريخ': record.date.strftime('%Y-%m-%d'),
                        'الحالة': f"{status_emoji} {record.status}",
                        'نوع الحصة': record.session_type or 'غير محدد',
                        'ملاحظات': record.notes or '-'
                    })

                df = pd.DataFrame(data)
                st.dataframe(df, width='stretch', hide_index=True)
            else:
                st.info("لا توجد سجلات حضور للشهر الماضي")

            st.markdown("---")

            # ==================== القسم 5: سجل المدفوعات ====================
            st.subheader("💰 سجل المدفوعات")

            payment_records = session.query(Payment).filter(
                Payment.skater_id == member_id
            ).order_by(Payment.payment_date.desc()).all()

            if payment_records:
                data = []
                for payment in payment_records:
                    data.append({
                        'التاريخ': payment.payment_date.strftime('%Y-%m-%d'),
                        'المبلغ': f"{payment.amount:.2f} EGP",
                        'الباقة': payment.bundle_type,
                        'الطريقة': payment.payment_method,
                        'الفترة': f"{payment.period_start.strftime('%Y-%m-%d') if payment.period_start else '-'} إلى {payment.period_end.strftime('%Y-%m-%d') if payment.period_end else '-'}",
                        'الحالة': payment.status
                    })

                df_payments = pd.DataFrame(data)
                st.dataframe(df_payments, width='stretch', hide_index=True)

                st.info(f"💰 إجمالي المدفوعات: **{total_payments:,.2f} EGP**")
            else:
                st.info("لا توجد مدفوعات مسجلة")

            st.markdown("---")

            # ==================== القسم 6: التحليلات ====================
            st.subheader("📹 التحليلات السابقة")

            analyses = session.query(Analysis).filter(
                Analysis.skater_id == member_id
            ).order_by(Analysis.analysis_date.desc()).all()

            if analyses:
                for analysis in analyses[:5]:  # آخر 5 تحليلات
                    with st.expander(f"📹 تحليل {analysis.analysis_date.strftime('%Y-%m-%d %H:%M')}"):
                        col1, col2 = st.columns(2)

                        with col1:
                            st.write(f"**نوع البرنامج:** {analysis.program_type}")
                            st.write(f"**عدد العناصر:** {analysis.elements_count}")

                        with col2:
                            if analysis.total_score:
                                st.write(f"**النتيجة الإجمالية:** {analysis.total_score:.2f}")
                            if analysis.technical_score:
                                st.write(f"**النتيجة الفنية:** {analysis.technical_score:.2f}")

                        if analysis.notes:
                            st.info(f"📝 {analysis.notes}")
            else:
                st.info("لا توجد تحليلات مسجلة")

            st.markdown("---")

            # ==================== القسم 7: تصدير التقرير ====================
            st.subheader("📄 تصدير التقرير الشامل")

            col_export1, col_export2 = st.columns(2)

            with col_export1:
                if st.button("📥 تحميل تقرير شامل (TXT)", width='stretch'):
                    report = generate_member_report(
                        member, total_attendance, total_absent,
                        attendance_rate, total_payments, total_analyses,
                        last_payment, attendance_records, payment_records, analyses
                    )

                    st.download_button(
                        label="⬇️ تحميل الآن",
                        data=report,
                        file_name=f"member_report_{member.name}_{date.today()}.txt",
                        mime="text/plain"
                    )

            with col_export2:
                if st.button("📊 تحميل بيانات Excel", width='stretch'):
                    st.info("🚧 قيد التطوير...")

    except Exception as e:
        st.error(f"❌ خطأ: {e}")


def generate_member_report(member, total_attendance, total_absent, attendance_rate,
                           total_payments, total_analyses, last_payment,
                           attendance_records, payment_records, analyses):
    """إنشاء تقرير شامل للعضو"""

    report = f"""
{'='*80}
                        التقرير الشامل للعضو
{'='*80}

📅 تاريخ التقرير: {datetime.now().strftime('%Y-%m-%d %H:%M')}

{'='*80}
                        المعلومات الأساسية
{'='*80}

👤 الاسم:                  {member.name}
🎯 المستوى:                {member.level or 'غير محدد'}
📦 الباقة:                 {member.bundle or 'غير محدد'}
🎂 تاريخ الميلاد:          {member.date_of_birth or 'غير محدد'}
🌍 الجنسية:                {member.country or 'مصر'}
👨‍🏫 المدرب:                 {member.coach_name or 'غير محدد'}
📧 البريد:                 {member.email or 'غير محدد'}
✅ الحالة:                 {member.membership_status or 'نشط'}

{'='*80}
                        الإحصائيات العامة
{'='*80}

✅ إجمالي الحضور:         {total_attendance}
❌ إجمالي الغياب:          {total_absent}
📊 نسبة الحضور:            {attendance_rate:.1f}%
💰 إجمالي المدفوعات:       {total_payments:,.2f} EGP
📹 عدد التحليلات:          {total_analyses}

{'='*80}
                        حالة الاشتراك
{'='*80}

"""

    if last_payment:
        days_left = (last_payment.period_end - datetime.now()).days if last_payment.period_end else 0
        report += f"""
💳 آخر دفعة:              {last_payment.amount:.2f} EGP
📅 تاريخ الدفع:           {last_payment.payment_date.strftime('%Y-%m-%d')}
📦 نوع الباقة:            {last_payment.bundle_type}
💳 طريقة الدفع:           {last_payment.payment_method}
⏰ تاريخ الانتهاء:        {last_payment.period_end.strftime('%Y-%m-%d') if last_payment.period_end else 'غير محدد'}
⏳ الأيام المتبقية:       {days_left} يوم
"""
    else:
        report += "⚠️ لا توجد مدفوعات مسجلة\n"

    report += f"\n{'='*80}\n"
    report += "                    سجل الحضور (آخر 30 يوم)\n"
    report += f"{'='*80}\n\n"

    if attendance_records:
        for record in attendance_records:
            status = "✅ حاضر" if record.status == "present" else "❌ غائب"
            report += f"{record.date.strftime('%Y-%m-%d'):12} | {status:10} | {record.session_type or 'غير محدد':15}\n"
    else:
        report += "لا توجد سجلات حضور\n"

    report += f"\n{'='*80}\n"
    report += "                    سجل المدفوعات\n"
    report += f"{'='*80}\n\n"

    if payment_records:
        for payment in payment_records:
            report += f"""
التاريخ:      {payment.payment_date.strftime('%Y-%m-%d')}
المبلغ:       {payment.amount:.2f} EGP
الباقة:       {payment.bundle_type}
الطريقة:      {payment.payment_method}
الحالة:       {payment.status}
{'-'*80}
"""
    else:
        report += "لا توجد مدفوعات مسجلة\n"

    report += f"\n{'='*80}\n"
    report += "                    التحليلات السابقة\n"
    report += f"{'='*80}\n\n"

    if analyses:
        for analysis in analyses:
            report += f"""
التاريخ:      {analysis.analysis_date.strftime('%Y-%m-%d %H:%M')}
البرنامج:     {analysis.program_type}
العناصر:      {analysis.elements_count}
النتيجة:      {analysis.total_score:.2f if analysis.total_score else 'غير محدد'}
{'-'*80}
"""
    else:
        report += "لا توجد تحليلات مسجلة\n"

    report += f"\n{'='*80}\n"
    report += "                    نهاية التقرير\n"
    report += f"{'='*80}\n"

    return report
