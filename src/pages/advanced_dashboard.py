"""
لوحة التحكم المتقدمة - Advanced Analytics Dashboard
لوحة تحكم شاملة مع تحليلات متقدمة وذكاء اصطناعي
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional

# Import analytics engines
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.analysis.advanced_analytics import (
    AdvancedAnalytics,
    PerformanceMetrics,
    create_performance_heatmap_data
)
from src.models.recommendation_engine import RecommendationEngine


def show_advanced_dashboard():
    """عرض لوحة التحكم المتقدمة"""
    st.title("🚀 لوحة التحكم المتقدمة")
    st.markdown("### تحليلات ذكية • توقعات AI • توصيات مخصصة")

    # Initialize engines
    analytics = AdvancedAnalytics()
    recommender = RecommendationEngine()

    # Load data from database
    data = load_dashboard_data()

    if not data['members']:
        st.warning("لا توجد بيانات للعرض")
        return

    # Sidebar - Player Selection
    with st.sidebar:
        st.header("⚙️ الإعدادات")

        player_names = [m['name'] for m in data['members']]
        selected_player = st.selectbox(
            "اختر اللاعب",
            options=["📊 عرض جميع اللاعبين"] + player_names
        )

        view_mode = st.radio(
            "وضع العرض",
            ["📈 نظرة عامة", "🔍 تحليل متعمق", "🤖 توصيات AI"]
        )

        date_range = st.date_input(
            "الفترة الزمنية",
            value=(datetime.now() - timedelta(days=90), datetime.now())
        )

    # Main content
    if selected_player == "📊 عرض جميع اللاعبين":
        show_overview_dashboard(data, analytics, recommender)
    else:
        player_data = next(m for m in data['members'] if m['name'] == selected_player)
        show_player_dashboard(
            player_data,
            data,
            analytics,
            recommender,
            view_mode
        )


def show_overview_dashboard(
    data: Dict,
    analytics: AdvancedAnalytics,
    recommender: RecommendationEngine
):
    """لوحة التحكم الشاملة لجميع اللاعبين"""

    st.header("📊 نظرة عامة على جميع اللاعبين")

    # Calculate metrics for all players
    all_metrics = []
    for member in data['members']:
        attendance_records = [
            a for a in data['attendance']
            if a.get('member_id') == member['id']
        ]
        score_records = [
            s for s in data['scores']
            if s.get('skater_id') == member['id']
        ]
        payment_records = [
            p for p in data['payments']
            if p.get('skater_id') == member['id']
        ]

        metrics = analytics.calculate_performance_metrics(
            player_id=member['id'],
            player_name=member['name'],
            attendance_records=attendance_records,
            score_records=score_records,
            payment_records=payment_records
        )
        all_metrics.append(metrics)

    # Top KPIs
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            "👥 إجمالي اللاعبين",
            len(all_metrics),
            delta=None
        )

    with col2:
        avg_attendance = np.mean([m.attendance_rate for m in all_metrics])
        st.metric(
            "📅 متوسط الحضور",
            f"{avg_attendance:.0%}",
            delta=None
        )

    with col3:
        avg_score = np.mean([m.average_score for m in all_metrics if m.average_score > 0])
        st.metric(
            "⭐ متوسط النقاط",
            f"{avg_score:.1f}",
            delta=None
        )

    with col4:
        high_engagement = sum(1 for m in all_metrics if m.engagement_score >= 0.7)
        st.metric(
            "🔥 مشاركة عالية",
            f"{high_engagement}",
            delta=f"{high_engagement/len(all_metrics):.0%}"
        )

    with col5:
        at_risk = sum(1 for m in all_metrics if m.risk_of_dropout >= 0.6)
        st.metric(
            "⚠️ في خطر",
            f"{at_risk}",
            delta=f"-{at_risk}" if at_risk > 0 else "0",
            delta_color="inverse"
        )

    st.markdown("---")

    # Performance Distribution
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 توزيع الأداء")

        # Create performance distribution chart
        scores = [m.average_score for m in all_metrics if m.average_score > 0]

        fig = go.Figure()
        fig.add_trace(go.Histogram(
            x=scores,
            nbinsx=20,
            marker_color='#1f77b4',
            opacity=0.7,
            name='عدد اللاعبين'
        ))

        fig.update_layout(
            title="توزيع متوسط النقاط",
            xaxis_title="النقاط",
            yaxis_title="عدد اللاعبين",
            showlegend=False,
            height=400
        )

        st.plotly_chart(fig, width='stretch')

    with col2:
        st.subheader("🎯 مستويات المشاركة")

        # Engagement levels pie chart
        engagement_levels = {
            'عالية': sum(1 for m in all_metrics if m.engagement_score >= 0.7),
            'متوسطة': sum(1 for m in all_metrics if 0.4 <= m.engagement_score < 0.7),
            'منخفضة': sum(1 for m in all_metrics if m.engagement_score < 0.4)
        }

        fig = go.Figure(data=[go.Pie(
            labels=list(engagement_levels.keys()),
            values=list(engagement_levels.values()),
            hole=0.4,
            marker_colors=['#2ecc71', '#f39c12', '#e74c3c']
        )])

        fig.update_layout(
            title="مستويات المشاركة",
            height=400
        )

        st.plotly_chart(fig, width='stretch')

    st.markdown("---")

    # Leaderboard
    st.subheader("🏆 لوحة المتصدرين")

    # Sort by average score
    top_players = sorted(all_metrics, key=lambda x: x.average_score, reverse=True)[:10]

    leaderboard_data = []
    for i, player in enumerate(top_players, 1):
        leaderboard_data.append({
            'المرتبة': f"🥇 {i}" if i == 1 else f"🥈 {i}" if i == 2 else f"🥉 {i}" if i == 3 else f"  {i}",
            'الاسم': player.player_name,
            'النقاط': f"{player.average_score:.1f}",
            'الحضور': f"{player.attendance_rate:.0%}",
            'التحسن': f"+{player.improvement_rate:.1f}" if player.improvement_rate > 0 else f"{player.improvement_rate:.1f}",
            'المشاركة': "🔥" * int(player.engagement_score * 5)
        })

    df_leaderboard = pd.DataFrame(leaderboard_data)
    st.dataframe(df_leaderboard, width='stretch', hide_index=True)

    st.markdown("---")

    # Risk Analysis
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("⚠️ لاعبون في خطر الانسحاب")

        at_risk_players = [m for m in all_metrics if m.risk_of_dropout >= 0.6]
        at_risk_players.sort(key=lambda x: x.risk_of_dropout, reverse=True)

        if at_risk_players:
            risk_data = []
            for player in at_risk_players[:5]:
                risk_data.append({
                    'الاسم': player.player_name,
                    'خطر الانسحاب': f"{player.risk_of_dropout:.0%}",
                    'الحضور الأخير': f"{player.attendance_rate:.0%}",
                    'الإجراء': '🚨 تدخل فوري'
                })

            df_risk = pd.DataFrame(risk_data)
            st.dataframe(df_risk, width='stretch', hide_index=True)
        else:
            st.success("✅ لا يوجد لاعبون في خطر حالياً")

    with col2:
        st.subheader("⭐ أفضل اللاعبين تحسناً")

        improving_players = [m for m in all_metrics if m.improvement_rate > 1.0]
        improving_players.sort(key=lambda x: x.improvement_rate, reverse=True)

        if improving_players:
            improve_data = []
            for player in improving_players[:5]:
                improve_data.append({
                    'الاسم': player.player_name,
                    'معدل التحسن': f"+{player.improvement_rate:.1f}/شهر",
                    'النقاط الحالية': f"{player.average_score:.1f}",
                    'الحالة': '🚀 ممتاز'
                })

            df_improve = pd.DataFrame(improve_data)
            st.dataframe(df_improve, width='stretch', hide_index=True)
        else:
            st.info("لا توجد بيانات كافية لتحديد التحسن")


def show_player_dashboard(
    player_data: Dict,
    all_data: Dict,
    analytics: AdvancedAnalytics,
    recommender: RecommendationEngine,
    view_mode: str
):
    """لوحة تحكم مفصلة للاعب واحد"""

    player_id = player_data['id']
    player_name = player_data['name']

    # Filter data for this player
    attendance_records = [
        a for a in all_data['attendance']
        if a.get('member_id') == player_id
    ]
    score_records = [
        s for s in all_data['scores']
        if s.get('skater_id') == player_id
    ]
    payment_records = [
        p for p in all_data['payments']
        if p.get('skater_id') == player_id
    ]

    # Calculate metrics
    metrics = analytics.calculate_performance_metrics(
        player_id=player_id,
        player_name=player_name,
        attendance_records=attendance_records,
        score_records=score_records,
        payment_records=payment_records
    )

    # Calculate all players metrics for comparison
    all_metrics = []
    for member in all_data['members']:
        att = [a for a in all_data['attendance'] if a.get('member_id') == member['id']]
        scr = [s for s in all_data['scores'] if s.get('skater_id') == member['id']]
        pay = [p for p in all_data['payments'] if p.get('skater_id') == member['id']]

        m = analytics.calculate_performance_metrics(
            player_id=member['id'],
            player_name=member['name'],
            attendance_records=att,
            score_records=scr,
            payment_records=pay
        )
        all_metrics.append(m)

    peer_comparison = analytics.calculate_peer_comparison(metrics, all_metrics)

    if view_mode == "📈 نظرة عامة":
        show_player_overview(metrics, peer_comparison, analytics)
    elif view_mode == "🔍 تحليل متعمق":
        show_deep_analysis(metrics, attendance_records, score_records, analytics)
    else:  # AI Recommendations
        show_ai_recommendations(metrics, recommender, peer_comparison)


def show_player_overview(
    metrics: PerformanceMetrics,
    peer_comparison: Dict,
    analytics: AdvancedAnalytics
):
    """نظرة عامة على اللاعب"""

    st.header(f"📊 {metrics.player_name}")

    # Key Metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "⭐ متوسط النقاط",
            f"{metrics.average_score:.1f}",
            delta=f"+{metrics.improvement_rate:.1f}/شهر" if metrics.improvement_rate > 0 else f"{metrics.improvement_rate:.1f}/شهر"
        )

    with col2:
        st.metric(
            "📅 معدل الحضور",
            f"{metrics.attendance_rate:.0%}",
            delta=f"سلسلة {metrics.attendance_streak} حصة"
        )

    with col3:
        st.metric(
            "🎯 المشاركة",
            f"{metrics.engagement_score:.0%}",
            delta=metrics.commitment_level.upper()
        )

    with col4:
        percentile = peer_comparison['percentile']
        st.metric(
            "🏆 التصنيف",
            f"أفضل {100-percentile}%",
            delta=f"#{peer_comparison['rank']} من {peer_comparison['total_players']}"
        )

    st.markdown("---")

    # Performance Score Card
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📈 تطور الأداء")

        # Create performance timeline (simulated data)
        dates = pd.date_range(end=datetime.now(), periods=12, freq='W')
        scores = np.random.normal(metrics.average_score, 5, 12)
        scores = np.clip(scores, 0, 100)

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=dates,
            y=scores,
            mode='lines+markers',
            name='النقاط',
            line=dict(color='#1f77b4', width=3),
            marker=dict(size=8)
        ))

        # Add trend line
        z = np.polyfit(range(len(scores)), scores, 1)
        p = np.poly1d(z)
        fig.add_trace(go.Scatter(
            x=dates,
            y=p(range(len(scores))),
            mode='lines',
            name='الاتجاه',
            line=dict(color='red', width=2, dash='dash')
        ))

        fig.update_layout(
            xaxis_title="التاريخ",
            yaxis_title="النقاط",
            hovermode='x unified',
            height=400
        )

        st.plotly_chart(fig, width='stretch')

    with col2:
        st.subheader("🎯 بطاقة الأداء")

        # Performance radar chart
        categories = ['الحضور', 'الأداء', 'التحسن', 'الانتظام', 'المشاركة']
        values = [
            metrics.attendance_rate * 100,
            metrics.skill_mastery * 100,
            min(100, max(0, 50 + metrics.improvement_rate * 10)),
            metrics.consistency_score * 100,
            metrics.engagement_score * 100
        ]

        fig = go.Figure()

        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            marker_color='#1f77b4'
        ))

        fig.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 100])
            ),
            showlegend=False,
            height=400
        )

        st.plotly_chart(fig, width='stretch')

    # Insights
    st.markdown("---")
    st.subheader("💡 رؤى ذكية")

    insights = analytics.generate_insights(metrics, peer_comparison)

    cols = st.columns(min(3, len(insights)))
    for i, insight in enumerate(insights):
        with cols[i % 3]:
            st.info(insight)


def show_deep_analysis(
    metrics: PerformanceMetrics,
    attendance_records: List[Dict],
    score_records: List[Dict],
    analytics: AdvancedAnalytics
):
    """تحليل متعمق"""

    st.header("🔍 تحليل متعمق")

    # Attendance Heatmap
    st.subheader("📅 خريطة الحضور الحرارية")

    if attendance_records:
        heatmap_data = create_performance_heatmap_data(attendance_records)

        # Create pivot table for heatmap
        df_attendance = pd.DataFrame(attendance_records)
        df_attendance['date'] = pd.to_datetime(df_attendance['date'])
        df_attendance['weekday'] = df_attendance['date'].dt.day_name()
        df_attendance['week'] = df_attendance['date'].dt.isocalendar().week

        pivot = df_attendance.groupby(['weekday', 'week']).size().unstack(fill_value=0)

        fig = go.Figure(data=go.Heatmap(
            z=pivot.values,
            x=pivot.columns,
            y=pivot.index,
            colorscale='Blues',
            text=pivot.values,
            texttemplate='%{text}',
            textfont={"size": 10}
        ))

        fig.update_layout(
            title="توزيع الحضور حسب اليوم والأسبوع",
            xaxis_title="الأسبوع",
            yaxis_title="اليوم",
            height=400
        )

        st.plotly_chart(fig, width='stretch')
    else:
        st.info("لا توجد بيانات حضور")

    # Performance Prediction
    st.markdown("---")
    st.subheader("🔮 التنبؤ بالأداء المستقبلي")

    if score_records:
        # Prepare score history
        score_history = [
            {
                'total_score': s.get('total_score', 0),
                'date': s.get('created_at', datetime.now().isoformat())
            }
            for s in score_records
        ]

        prediction = analytics.predict_future_performance(score_history, days_ahead=30)

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "النقاط الحالية",
                f"{prediction.current_value:.1f}",
                delta=None
            )

        with col2:
            st.metric(
                "التوقع (30 يوم)",
                f"{prediction.predicted_value:.1f}",
                delta=f"{prediction.predicted_value - prediction.current_value:+.1f}"
            )

        with col3:
            st.metric(
                "الثقة",
                f"{prediction.confidence:.0%}",
                delta=None
            )

        # Show prediction visualization
        days = np.arange(0, 31)
        current = prediction.current_value
        predicted = np.linspace(current, prediction.predicted_value, 31)

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=days,
            y=predicted,
            mode='lines',
            name='التوقع',
            line=dict(color='green', width=3)
        ))

        # Add confidence interval
        std_dev = (prediction.predicted_value - current) * 0.1
        upper = predicted + std_dev
        lower = predicted - std_dev

        fig.add_trace(go.Scatter(
            x=np.concatenate([days, days[::-1]]),
            y=np.concatenate([upper, lower[::-1]]),
            fill='toself',
            fillcolor='rgba(0,176,246,0.2)',
            line=dict(color='rgba(255,255,255,0)'),
            name='نطاق الثقة'
        ))

        fig.update_layout(
            title="توقع الأداء للـ 30 يوم القادمة",
            xaxis_title="اليوم",
            yaxis_title="النقاط المتوقعة",
            hovermode='x unified',
            height=400
        )

        st.plotly_chart(fig, width='stretch')
    else:
        st.info("لا توجد بيانات كافية للتنبؤ")


def show_ai_recommendations(
    metrics: PerformanceMetrics,
    recommender: RecommendationEngine,
    peer_comparison: Dict
):
    """عرض توصيات AI"""

    st.header("🤖 توصيات الذكاء الاصطناعي")

    # Generate recommendations
    recommendations = recommender.generate_recommendations(
        player_metrics=metrics,
        peer_comparison=peer_comparison
    )

    if not recommendations:
        st.success("✅ الأداء ممتاز! لا توجد توصيات حالياً")
        return

    # Display recommendations by priority
    high_priority = [r for r in recommendations if r.priority == 'high']
    medium_priority = [r for r in recommendations if r.priority == 'medium']
    low_priority = [r for r in recommendations if r.priority == 'low']

    if high_priority:
        st.subheader("🚨 توصيات عالية الأولوية")
        for rec in high_priority:
            with st.expander(f"{rec.title}", expanded=True):
                st.markdown(f"**📋 الوصف:** {rec.description}")
                st.markdown(f"**📊 التأثير المتوقع:** {rec.impact_score:.0%}")
                st.markdown(f"**🎯 الثقة:** {rec.confidence:.0%}")

                st.markdown("**✅ خطوات العمل:**")
                for i, action in enumerate(rec.action_items, 1):
                    st.markdown(f"{i}. {action}")

                st.success(f"**💡 الفائدة المتوقعة:** {rec.expected_benefit}")

    if medium_priority:
        st.markdown("---")
        st.subheader("⚡ توصيات متوسطة الأولوية")
        for rec in medium_priority:
            with st.expander(f"{rec.title}"):
                st.markdown(f"**📋 الوصف:** {rec.description}")
                st.markdown(f"**📊 التأثير المتوقع:** {rec.impact_score:.0%}")

                st.markdown("**✅ خطوات العمل:**")
                for i, action in enumerate(rec.action_items, 1):
                    st.markdown(f"{i}. {action}")

                st.info(f"**💡 الفائدة المتوقعة:** {rec.expected_benefit}")

    if low_priority:
        st.markdown("---")
        with st.expander(f"ℹ️ توصيات إضافية ({len(low_priority)})"):
            for rec in low_priority:
                st.markdown(f"**{rec.title}**")
                st.markdown(rec.description)
                st.markdown("---")

    # Generate Training Plan
    st.markdown("---")
    st.subheader("📅 خطة تدريب مخصصة")

    training_plan = recommender.generate_training_plan(metrics)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**مجالات التركيز:**")
        for area in training_plan['focus_areas']:
            st.markdown(f"- **{area['area']}** ({area['allocation']}) - أولوية: {area['priority']}")

    with col2:
        st.markdown("**الجدول الأسبوعي:**")
        schedule = training_plan['weekly_schedule']
        st.markdown(f"- عدد الحصص: **{schedule['recommended_sessions']}** حصة/أسبوع")
        st.markdown(f"- مدة الحصة: **{schedule['session_duration']}**")
        st.markdown(f"- الأيام المقترحة: **{', '.join(schedule['suggested_days'])}**")

    st.markdown("**🎯 الأهداف والإنجازات:**")
    milestones_data = []
    for milestone in training_plan['milestones']:
        milestones_data.append({
            'الأسبوع': milestone['week'],
            'الهدف': f"{milestone['target_score']:.1f} نقطة",
            'الوصف': milestone['description']
        })

    df_milestones = pd.DataFrame(milestones_data)
    st.dataframe(df_milestones, width='stretch', hide_index=True)


def load_dashboard_data() -> Dict:
    """تحميل البيانات من قاعدة البيانات — uses real skaters table"""
    import sqlite3

    conn = sqlite3.connect('skating_database.db')

    # Load skaters (was wrongly querying 'members' table)
    try:
        members_df = pd.read_sql_query(
            "SELECT id, name, level AS skill_level, coach_name, "
            "membership_status, gender FROM skaters", conn
        )
        members = members_df.to_dict('records')
    except Exception:
        members = []

    # Load attendance
    try:
        attendance_df = pd.read_sql_query("SELECT * FROM attendance", conn)
        attendance = attendance_df.to_dict('records')
    except Exception:
        attendance = []

    # Load payments
    try:
        payments_df = pd.read_sql_query("SELECT * FROM payments", conn)
        payments = payments_df.to_dict('records')
    except Exception:
        payments = []

    # Load real analysis scores
    scores = []
    try:
        scores_df = pd.read_sql_query(
            "SELECT player_name AS skater_name, total_score, analyzed_at AS created_at "
            "FROM analysis_results ORDER BY analyzed_at DESC LIMIT 200", conn
        )
        scores = scores_df.to_dict('records')
    except Exception:
        pass

    conn.close()

    return {
        'members': members,
        'attendance': attendance,
        'payments': payments,
        'scores': scores
    }


if __name__ == "__main__":
    show_advanced_dashboard()
