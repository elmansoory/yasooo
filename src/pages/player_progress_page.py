"""
📈 صفحة تقدم اللاعب عبر الزمن
Player Progress Tracking Dashboard
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Dict
from datetime import datetime

try:
    from src.analysis.history_manager import (
        load_all_sessions, load_player_sessions,
        load_session_detail, get_player_names,
    )
    HISTORY_AVAILABLE = True
except ImportError:
    HISTORY_AVAILABLE = False


# ── helpers ──────────────────────────────────────────────────────────────────

def _demo_sessions(player_name: str) -> List[Dict]:
    import random, math
    random.seed(42)
    sessions = []
    dates = [
        '2026-01-05', '2026-01-12', '2026-01-19', '2026-01-26',
        '2026-02-02', '2026-02-09', '2026-02-16', '2026-02-23',
    ]
    for i, d in enumerate(dates):
        score = 14 + i * 0.7 + random.uniform(-0.3, 0.3)
        sessions.append({
            'session_id': i + 1,
            'session_date': d,
            'player_name': player_name,
            'total_score': round(score, 2),
            'total_jumps': random.randint(5, 7),
            'total_spins': random.randint(2, 3),
            'total_errors': max(0, 5 - i + random.randint(-1, 1)),
            'avg_goe': round(-1.5 + i * 0.25 + random.uniform(-0.1, 0.1), 2),
            'clean_jumps': max(0, i + random.randint(0, 2)),
            'video_duration': random.randint(90, 180),
        })
    return sessions


def _sessions_to_df(sessions: List[Dict]) -> pd.DataFrame:
    if not sessions:
        return pd.DataFrame()
    df = pd.DataFrame(sessions)
    df['session_date'] = pd.to_datetime(df['session_date'])
    df = df.sort_values('session_date')
    df['session_num'] = range(1, len(df) + 1)
    return df


def _improvement_pct(df: pd.DataFrame, col: str) -> str:
    if len(df) < 2:
        return "—"
    first, last = df[col].iloc[0], df[col].iloc[-1]
    if first == 0:
        return "—"
    pct = (last - first) / abs(first) * 100
    sign = "+" if pct >= 0 else ""
    return f"{sign}{pct:.1f}%"


PURPLE = '#667eea'
VIOLET = '#764ba2'


# ── main page ────────────────────────────────────────────────────────────────

def show_player_progress_page(lang: str = 'ar'):
    is_ar = lang == 'ar'

    st.markdown(
        f'<h1>{"📈 تقدم اللاعبين عبر الزمن" if is_ar else "📈 Player Progress Over Time"}</h1>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<p style="text-align:center;color:#64748b;font-size:1.1em">'
        f'{"تتبع التطور في كل جلسة تدريبية وقارن الأداء عبر الوقت"}'
        f'</p>',
        unsafe_allow_html=True,
    )
    st.markdown('---')

    # ── player selector ──────────────────────────────────────────────────────
    col_sel, col_demo = st.columns([4, 1])

    with col_demo:
        use_demo = st.button(
            '🎭 تجريبي' if is_ar else '🎭 Demo',
            use_container_width=True,
        )
        if use_demo:
            st.session_state['progress_demo_player'] = (
                'يوسف محمد' if is_ar else 'John Smith'
            )

    with col_sel:
        player_names = get_player_names() if HISTORY_AVAILABLE else []
        if st.session_state.get('progress_demo_player'):
            demo_name = st.session_state['progress_demo_player']
            if demo_name not in player_names:
                player_names = [demo_name] + player_names

        if not player_names:
            st.info(
                'لا توجد جلسات محفوظة بعد — حلّل فيديو أولاً أو استخدم العرض التجريبي'
                if is_ar else
                'No saved sessions yet — analyze a video first or use Demo mode'
            )
            return

        selected_player = st.selectbox(
            'اختر اللاعب' if is_ar else 'Select Player',
            player_names,
            label_visibility='collapsed',
        )

    # ── load sessions ────────────────────────────────────────────────────────
    if (HISTORY_AVAILABLE and
            selected_player != st.session_state.get('progress_demo_player')):
        raw_sessions = load_player_sessions(selected_player)
    else:
        raw_sessions = _demo_sessions(selected_player)

    if not raw_sessions:
        st.info(
            f'لا توجد جلسات محفوظة للاعب: {selected_player}'
            if is_ar else
            f'No saved sessions for player: {selected_player}'
        )
        return

    df = _sessions_to_df(raw_sessions)
    n_sessions = len(df)

    # ── KPI row ──────────────────────────────────────────────────────────────
    latest = df.iloc[-1]
    first = df.iloc[0]

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric(
            '🏋️ ' + ('جلسات' if is_ar else 'Sessions'), n_sessions
        )
    with col2:
        delta_score = round(latest['total_score'] - first['total_score'], 2)
        st.metric(
            '🏆 ' + ('آخر نتيجة' if is_ar else 'Last Score'),
            f"{latest['total_score']:.2f}",
            delta=f"{delta_score:+.2f}",
        )
    with col3:
        st.metric(
            '📈 ' + ('تحسن النتيجة' if is_ar else 'Score Growth'),
            _improvement_pct(df, 'total_score'),
        )
    with col4:
        delta_err = int(latest['total_errors'] - first['total_errors'])
        st.metric(
            '🛠️ ' + ('أخطاء آخر جلسة' if is_ar else 'Last Errors'),
            int(latest['total_errors']),
            delta=f"{delta_err:+d}",
            delta_color='inverse',
        )
    with col5:
        st.metric(
            '✅ ' + ('قفزات نظيفة' if is_ar else 'Clean Jumps'),
            int(latest['clean_jumps']),
        )

    st.markdown('---')

    # ── charts ───────────────────────────────────────────────────────────────
    tab_labels = (
        ['📊 الأداء', '🛠️ الأخطاء', '🦘 القفزات', '📋 الجلسات']
        if is_ar else
        ['📊 Performance', '🛠️ Errors', '🦘 Jumps', '📋 Sessions']
    )
    tab1, tab2, tab3, tab4 = st.tabs(tab_labels)

    with tab1:
        _chart_score_trend(df, is_ar)

    with tab2:
        _chart_errors_trend(df, is_ar)

    with tab3:
        _chart_jumps_trend(df, is_ar)

    with tab4:
        _sessions_table(df, raw_sessions, is_ar, lang)


# ── chart helpers ─────────────────────────────────────────────────────────────

def _chart_score_trend(df: pd.DataFrame, is_ar: bool):
    st.subheader('📊 ' + ('تطور النتيجة الكلية' if is_ar else 'Total Score Trend'))

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['session_date'], y=df['total_score'],
        mode='lines+markers+text',
        text=[f"{v:.2f}" for v in df['total_score']],
        textposition='top center',
        line=dict(color=PURPLE, width=3),
        marker=dict(size=9, color=VIOLET),
        fill='tozeroy',
        fillcolor='rgba(102,126,234,0.12)',
        name='Score',
    ))

    # Trend line
    if len(df) >= 3:
        import numpy as np
        x_num = (df['session_date'] - df['session_date'].min()).dt.days.values
        z = np.polyfit(x_num, df['total_score'].values, 1)
        trend_y = np.poly1d(z)(x_num)
        fig.add_trace(go.Scatter(
            x=df['session_date'], y=trend_y,
            mode='lines',
            line=dict(color='#f59e0b', width=2, dash='dash'),
            name='Trend',
        ))

    fig.update_layout(
        xaxis_title='',
        yaxis_title='Score',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        height=320,
        margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(orientation='h', y=1.1),
    )
    st.plotly_chart(fig, use_container_width=True)

    # GOE trend
    if 'avg_goe' in df.columns:
        fig2 = px.bar(
            df, x='session_date', y='avg_goe',
            title='متوسط GOE' if is_ar else 'Average GOE per Session',
            color='avg_goe',
            color_continuous_scale=['#dc2626', '#f59e0b', '#16a34a'],
            range_color=[-3, 3],
            text=[f"{v:+.2f}" for v in df['avg_goe']],
        )
        fig2.update_layout(
            coloraxis_showscale=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            height=260,
            margin=dict(l=0, r=0, t=40, b=0),
        )
        st.plotly_chart(fig2, use_container_width=True)


def _chart_errors_trend(df: pd.DataFrame, is_ar: bool):
    st.subheader('🛠️ ' + ('تطور الأخطاء' if is_ar else 'Error Reduction Trend'))

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['session_date'], y=df['total_errors'],
        mode='lines+markers',
        line=dict(color='#dc2626', width=3),
        marker=dict(size=9),
        fill='tozeroy',
        fillcolor='rgba(220,38,38,0.10)',
        name='Errors',
    ))
    fig.update_layout(
        xaxis_title='',
        yaxis_title='# Errors',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        height=300,
        margin=dict(l=0, r=0, t=10, b=0),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Clean jumps trend
    fig3 = px.area(
        df, x='session_date', y='clean_jumps',
        title='القفزات النظيفة' if is_ar else 'Clean Jumps per Session',
        color_discrete_sequence=['#16a34a'],
    )
    fig3.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        height=260,
        margin=dict(l=0, r=0, t=40, b=0),
    )
    st.plotly_chart(fig3, use_container_width=True)


def _chart_jumps_trend(df: pd.DataFrame, is_ar: bool):
    st.subheader('🦘 ' + ('تطور القفزات' if is_ar else 'Jump Progress'))

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df['session_date'], y=df['total_jumps'],
        name='Total Jumps',
        marker_color=PURPLE,
        opacity=0.7,
    ))
    fig.add_trace(go.Bar(
        x=df['session_date'], y=df['clean_jumps'],
        name='Clean Jumps',
        marker_color='#16a34a',
    ))
    fig.update_layout(
        barmode='overlay',
        xaxis_title='',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        height=320,
        margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(orientation='h', y=1.1),
    )
    st.plotly_chart(fig, use_container_width=True)


def _sessions_table(df: pd.DataFrame, raw: List[Dict], is_ar: bool, lang: str):
    st.subheader('📋 ' + ('سجل كامل الجلسات' if is_ar else 'Full Session History'))

    display = df[['session_date', 'total_score', 'total_jumps',
                  'clean_jumps', 'total_errors', 'avg_goe']].copy()
    display.columns = (
        ['التاريخ', 'النتيجة', 'القفزات', 'نظيفة', 'الأخطاء', 'GOE']
        if is_ar else
        ['Date', 'Score', 'Jumps', 'Clean', 'Errors', 'GOE']
    )
    display['النتيجة' if is_ar else 'Score'] = display[
        'النتيجة' if is_ar else 'Score'].round(2)
    display['GOE'] = display['GOE'].round(2)

    st.dataframe(display, use_container_width=True, hide_index=True)

    # Session detail expander
    if raw:
        st.markdown('---')
        st.markdown('**' + ('تفاصيل جلسة' if is_ar else 'Session Detail') + '**')
        options = {
            f"#{s['session_id']} — {s['session_date']} — Score: {s['total_score']:.2f}": s['session_id']
            for s in raw
        }
        chosen_label = st.selectbox(
            'اختر جلسة' if is_ar else 'Select session',
            list(options.keys()),
            label_visibility='collapsed',
        )
        chosen_id = options[chosen_label]
        detail = load_session_detail(chosen_id)
        if detail:
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"**{'القفزات' if is_ar else 'Jumps'}**")
                jumps = detail.get('jumps', [])
                if jumps:
                    jdf = pd.DataFrame([{
                        'Type': j.get('type', ''),
                        'Score': j.get('final_score', 0),
                        'GOE': j.get('goe', 0),
                        'Clean': '✅' if j.get('is_clean', True) else '⚠️',
                    } for j in jumps])
                    st.dataframe(jdf, hide_index=True)
                else:
                    st.info('—')
            with c2:
                st.markdown(f"**{'الأخطاء' if is_ar else 'Errors'}**")
                errors = detail.get('errors', [])
                if errors:
                    for e in errors:
                        title = e.get('title_ar' if is_ar else 'title_en', '')
                        sev = e.get('severity', '')
                        icon = {'CRITICAL': '🔴', 'HIGH': '🟠', 'MEDIUM': '🟡',
                                'LOW': '🟢', 'حرج': '🔴', 'عالي': '🟠',
                                'متوسط': '🟡', 'منخفض': '🟢'}.get(sev, '⚪')
                        st.markdown(f"{icon} {title}")
                else:
                    st.success('✅ ' + ('لا أخطاء' if is_ar else 'No errors'))
