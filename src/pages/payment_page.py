"""
صفحة المدفوعات والاشتراكات
"""
import streamlit as st
from datetime import datetime, date, timedelta
import pandas as pd
from sqlalchemy import func
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.database.models import Payment, Skater


def show_payments_page(db_manager):
    """صفحة المدفوعات"""
    st.title("💰 نظام المدفوعات والاشتراكات")

    tabs = st.tabs([
        "💳 تسجيل دفعة جديدة",
        "📋 سجل المدفوعات",
        "⚠️ المتأخرات",
        "📊 إحصائيات مالية"
    ])

    with tabs[0]:
        show_new_payment(db_manager)

    with tabs[1]:
        show_payment_history(db_manager)

    with tabs[2]:
        show_overdue_payments(db_manager)

    with tabs[3]:
        show_financial_statistics(db_manager)


def show_new_payment(db_manager):
    """تسجيل دفعة جديدة"""
    st.subheader("💳 تسجيل دفعة جديدة")

    try:
        with db_manager.get_session() as session:
            # الحصول على قائمة الأعضاء
            members = session.query(Skater).filter(
                ~Skater.notes.like('%مدرب%')
            ).order_by(Skater.name).all()

            if not members:
                st.warning("⚠️ لا يوجد أعضاء في النظام")
                return

            # نموذج الدفع
            col1, col2 = st.columns(2)

            with col1:
                # اختيار العضو
                member_options = {f"{m.name} ({m.level or 'N/A'})": m.id for m in members}
                selected_member = st.selectbox(
                    "👤 اختر العضو",
                    options=list(member_options.keys())
                )
                member_id = member_options[selected_member]

                # المبلغ
                amount = st.number_input(
                    "💵 المبلغ (EGP)",
                    min_value=0.0,
                    step=100.0,
                    help="أدخل المبلغ المدفوع"
                )

                # نوع الباقة
                bundle_type = st.selectbox(
                    "📦 نوع الباقة",
                    [
                        "On-Ice Bronze",
                        "On-Ice Silver",
                        "On-Ice Gold",
                        "Off-Ice Bronze",
                        "Off-Ice Silver",
                        "Full Access",
                        "Private Session",
                        "أخرى"
                    ]
                )

            with col2:
                # تاريخ الدفع
                payment_date = st.date_input(
                    "📅 تاريخ الدفع",
                    value=date.today()
                )

                # طريقة الدفع
                payment_method = st.selectbox(
                    "💳 طريقة الدفع",
                    ["نقدي (Cash)", "InstaPay", "فودافون كاش", "تحويل بنكي", "بطاقة ائتمان"]
                )

                # فترة الاشتراك
                col_start, col_end = st.columns(2)
                with col_start:
                    period_start = st.date_input(
                        "بداية الاشتراك",
                        value=date.today()
                    )
                with col_end:
                    period_end = st.date_input(
                        "نهاية الاشتراك",
                        value=date.today() + timedelta(days=30)
                    )

            # خصم وملاحظات
            col1, col2 = st.columns(2)

            with col1:
                discount = st.number_input(
                    "🏷️ خصم (EGP)",
                    min_value=0.0,
                    value=0.0,
                    step=50.0
                )

            with col2:
                received_by = st.text_input(
                    "👨‍💼 المستلم",
                    value="الإدارة",
                    help="من استلم الدفعة"
                )

            notes = st.text_area(
                "📝 ملاحظات",
                help="أي ملاحظات إضافية"
            )

            # عرض المبلغ النهائي
            final_amount = amount - discount
            if discount > 0:
                st.info(f"💰 المبلغ النهائي بعد الخصم: **{final_amount:.2f} EGP**")
            else:
                st.info(f"💰 المبلغ الإجمالي: **{final_amount:.2f} EGP**")

            # زر الحفظ
            st.markdown("---")
            col1, col2, col3 = st.columns([1, 2, 1])

            with col2:
                if st.button("💾 حفظ الدفعة", use_container_width=True, type="primary"):
                    if amount <= 0:
                        st.error("❌ المبلغ يجب أن يكون أكبر من صفر")
                        return

                    try:
                        # إنشاء سجل الدفعة
                        payment = Payment(
                            skater_id=member_id,
                            amount=final_amount,
                            payment_date=datetime.combine(payment_date, datetime.min.time()),
                            payment_method=payment_method,
                            bundle_type=bundle_type,
                            period_start=datetime.combine(period_start, datetime.min.time()),
                            period_end=datetime.combine(period_end, datetime.min.time()),
                            status='completed',
                            discount=discount,
                            notes=notes,
                            received_by=received_by
                        )

                        session.add(payment)
                        session.commit()

                        st.success(f"✅ تم تسجيل الدفعة بنجاح! ({final_amount:.2f} EGP)")
                        st.balloons()

                    except Exception as e:
                        st.error(f"❌ خطأ في الحفظ: {e}")

    except Exception as e:
        st.error(f"❌ خطأ: {e}")


def show_payment_history(db_manager):
    """سجل المدفوعات"""
    st.subheader("📋 سجل المدفوعات")

    col1, col2, col3 = st.columns(3)

    with col1:
        start_date = st.date_input("من تاريخ", value=date.today() - timedelta(days=90))

    with col2:
        end_date = st.date_input("إلى تاريخ", value=date.today())

    with col3:
        filter_status = st.selectbox(
            "حالة الدفع",
            ["الكل", "مكتملة", "معلقة", "مرتجعة"]
        )

    if st.button("🔍 عرض السجلات", use_container_width=True):
        try:
            with db_manager.get_session() as session:
                # بناء الاستعلام
                query = session.query(
                    Payment,
                    Skater.name
                ).join(Skater).filter(
                    Payment.payment_date >= datetime.combine(start_date, datetime.min.time()),
                    Payment.payment_date <= datetime.combine(end_date, datetime.max.time())
                )

                # تصفية حسب الحالة
                status_map = {
                    "مكتملة": "completed",
                    "معلقة": "pending",
                    "مرتجعة": "refunded"
                }
                if filter_status != "الكل":
                    query = query.filter(Payment.status == status_map[filter_status])

                payments = query.order_by(Payment.payment_date.desc()).all()

                if not payments:
                    st.warning("⚠️ لا توجد مدفوعات في هذه الفترة")
                    return

                # تحويل لـ DataFrame
                data = []
                total_amount = 0

                for payment, name in payments:
                    data.append({
                        'الاسم': name,
                        'التاريخ': payment.payment_date.strftime('%Y-%m-%d'),
                        'المبلغ': f"{payment.amount:.2f} EGP",
                        'الطريقة': payment.payment_method,
                        'الباقة': payment.bundle_type,
                        'من': payment.period_start.strftime('%Y-%m-%d') if payment.period_start else '-',
                        'إلى': payment.period_end.strftime('%Y-%m-%d') if payment.period_end else '-',
                        'الخصم': f"{payment.discount:.2f}" if payment.discount else "0",
                        'المستلم': payment.received_by or '-',
                        'الحالة': '✅ مكتملة' if payment.status == 'completed' else '⏳ معلقة'
                    })
                    total_amount += payment.amount

                df = pd.DataFrame(data)

                # إحصائيات سريعة
                st.markdown(f"### 💰 إجمالي المدفوعات: **{total_amount:.2f} EGP**")
                st.markdown(f"📊 عدد المعاملات: **{len(df)}**")

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
                        file_name=f"payments_{start_date}_{end_date}.csv",
                        mime="text/csv"
                    )

                with col_export2:
                    # تقرير مالي منسق
                    report_text = generate_payment_report(df, start_date, end_date, total_amount)
                    st.download_button(
                        label="📄 تقرير مالي (TXT)",
                        data=report_text,
                        file_name=f"financial_report_{start_date}_{end_date}.txt",
                        mime="text/plain"
                    )

        except Exception as e:
            st.error(f"❌ خطأ: {e}")


def show_overdue_payments(db_manager):
    """المتأخرات والاشتراكات المنتهية"""
    st.subheader("⚠️ المتأخرات والاشتراكات المنتهية")

    try:
        with db_manager.get_session() as session:
            today = datetime.now()

            # الأعضاء الذين انتهت اشتراكاتهم
            overdue_query = session.query(
                Skater.name,
                Skater.level,
                Skater.bundle,
                func.max(Payment.period_end).label('last_expiry')
            ).join(Payment).group_by(Skater.id).having(
                func.max(Payment.period_end) < today
            ).all()

            if overdue_query:
                st.markdown("### 🔴 اشتراكات منتهية")

                for name, level, bundle, last_expiry in overdue_query:
                    days_overdue = (today - last_expiry).days

                    with st.expander(f"⚠️ {name} ({level or 'N/A'})"):
                        col1, col2, col3 = st.columns(3)

                        with col1:
                            st.write(f"**آخر باقة:** {bundle or 'N/A'}")
                        with col2:
                            st.write(f"**انتهى في:** {last_expiry.strftime('%Y-%m-%d')}")
                        with col3:
                            st.write(f"**متأخر:** {days_overdue} يوم")

                st.markdown("---")
                st.info(f"📊 إجمالي الاشتراكات المنتهية: **{len(overdue_query)}**")
            else:
                st.success("✅ لا توجد اشتراكات منتهية")

            # الأعضاء بدون أي مدفوعات
            st.markdown("---")
            st.markdown("### 🔴 أعضاء بدون اشتراكات")

            members_without_payments = session.query(Skater).filter(
                ~Skater.notes.like('%مدرب%'),
                ~Skater.id.in_(
                    session.query(Payment.skater_id).distinct()
                )
            ).all()

            if members_without_payments:
                for member in members_without_payments:
                    st.warning(f"⚠️ {member.name} ({member.level or 'N/A'}) - لم يتم تسجيل أي دفعات")

                st.info(f"📊 عدد الأعضاء بدون اشتراكات: **{len(members_without_payments)}**")
            else:
                st.success("✅ جميع الأعضاء لديهم اشتراكات")

    except Exception as e:
        st.error(f"❌ خطأ: {e}")


def show_financial_statistics(db_manager):
    """إحصائيات مالية"""
    st.subheader("📊 إحصائيات مالية")

    try:
        with db_manager.get_session() as session:
            # إحصائيات الشهر الحالي
            first_day = date.today().replace(day=1)

            monthly_total = session.query(
                func.sum(Payment.amount)
            ).filter(
                Payment.payment_date >= first_day,
                Payment.status == 'completed'
            ).scalar() or 0

            monthly_count = session.query(
                func.count(Payment.id)
            ).filter(
                Payment.payment_date >= first_day
            ).scalar() or 0

            # إحصائيات السنة
            year_start = date.today().replace(month=1, day=1)

            yearly_total = session.query(
                func.sum(Payment.amount)
            ).filter(
                Payment.payment_date >= year_start,
                Payment.status == 'completed'
            ).scalar() or 0

            # عرض الإحصائيات
            st.markdown("### 📅 الشهر الحالي")
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("💰 إجمالي الإيرادات", f"{monthly_total:.2f} EGP")

            with col2:
                st.metric("📊 عدد المعاملات", monthly_count)

            with col3:
                avg = monthly_total / monthly_count if monthly_count > 0 else 0
                st.metric("📈 متوسط الدفعة", f"{avg:.2f} EGP")

            st.markdown("---")
            st.markdown("### 📅 السنة الحالية")

            col1, col2 = st.columns(2)

            with col1:
                st.metric("💰 إجمالي الإيرادات", f"{yearly_total:.2f} EGP")

            with col2:
                months_passed = date.today().month
                monthly_avg = yearly_total / months_passed if months_passed > 0 else 0
                st.metric("📊 متوسط شهري", f"{monthly_avg:.2f} EGP")

            # أكثر الباقات مبيعاً
            st.markdown("---")
            st.markdown("### 📦 أكثر الباقات مبيعاً")

            top_bundles = session.query(
                Payment.bundle_type,
                func.count(Payment.id).label('count'),
                func.sum(Payment.amount).label('total')
            ).filter(
                Payment.status == 'completed'
            ).group_by(Payment.bundle_type).order_by(
                func.count(Payment.id).desc()
            ).limit(5).all()

            if top_bundles:
                for bundle, count, total in top_bundles:
                    col1, col2, col3 = st.columns([2, 1, 1])
                    with col1:
                        st.write(f"**{bundle or 'غير محدد'}**")
                    with col2:
                        st.write(f"📊 {count} اشتراك")
                    with col3:
                        st.write(f"💰 {total:.2f} EGP")

    except Exception as e:
        st.error(f"❌ خطأ: {e}")


def generate_payment_report(df, start_date, end_date, total_amount):
    """إنشاء تقرير مالي منسق"""
    report = f"""
{'='*70}
                        التقرير المالي
{'='*70}

📅 الفترة: من {start_date} إلى {end_date}
📊 تاريخ التقرير: {datetime.now().strftime('%Y-%m-%d %H:%M')}

{'='*70}
                        ملخص مالي
{'='*70}

💰 إجمالي الإيرادات:      {total_amount:.2f} EGP
📊 عدد المعاملات:         {len(df)}
📈 متوسط الدفعة:          {(total_amount / len(df) if len(df) > 0 else 0):.2f} EGP

{'='*70}
                        تفاصيل المدفوعات
{'='*70}

"""
    # إضافة تفاصيل المدفوعات
    for idx, row in df.iterrows():
        report += f"""
العضو:      {row['الاسم']}
التاريخ:    {row['التاريخ']}
المبلغ:     {row['المبلغ']}
الطريقة:    {row['الطريقة']}
الباقة:     {row['الباقة']}
الفترة:     من {row['من']} إلى {row['إلى']}
الخصم:      {row['الخصم']} EGP
المستلم:    {row['المستلم']}
الحالة:     {row['الحالة']}
{'-'*70}
"""

    report += f"\n{'='*70}\n"
    report += f"💰 الإجمالي النهائي: {total_amount:.2f} EGP\n"
    report += f"{'='*70}\n"
    report += "                    نهاية التقرير\n"
    report += f"{'='*70}\n"

    return report
