"""
World Champions Dashboard Page
لوحة أبطال العالم - مستوحاة من dashboard.html
"""

import streamlit as st
import streamlit.components.v1 as components
import sqlite3
import pandas as pd
from datetime import date, timedelta


WORLD_CHAMPIONS = [
    {"rank": 1, "name": "Ilia Malinin",    "flag": "🇺🇸", "country": "USA",    "age": 21, "specialty": "Quad Axel",    "best_score": 333.69, "sp": 111.82, "fs": 221.87},
    {"rank": 2, "name": "Shoma Uno",       "flag": "🇯🇵", "country": "Japan",  "age": 28, "specialty": "Quad Flip",    "best_score": 301.14, "sp": 100.53, "fs": 200.61},
    {"rank": 3, "name": "Yuma Kagiyama",   "flag": "🇯🇵", "country": "Japan",  "age": 22, "specialty": "Quad Toe",     "best_score": 297.16, "sp": 100.40, "fs": 196.76},
    {"rank": 4, "name": "Jason Brown",     "flag": "🇺🇸", "country": "USA",    "age": 30, "specialty": "Triple Axel",  "best_score": 283.50, "sp": 94.50,  "fs": 189.00},
    {"rank": 5, "name": "Kao Miura",       "flag": "🇯🇵", "country": "Japan",  "age": 20, "specialty": "Quad Lutz",    "best_score": 282.11, "sp": 93.70,  "fs": 188.41},
]

INVENTED_DRILLS = [
    {
        "name_ar": "بروتوكول نحات الهواء",
        "name_en": "Air Sculptor Protocol",
        "desc_ar": "محاكاة وضعيات الهواء بربط المقاومة. يحوّل المتزلج إلى «نحات» يصنع وضعياته في الهواء.",
        "desc_en": "Simulate air positions using resistance bands. Trains perfect body position mid-jump.",
        "target_ar": "وضعية الهواء المثالية",
        "target_en": "perfect_air_position",
        "muscles": "core, shoulders",
        "duration": "15 min × 4 sets",
        "location_ar": "خارج الجليد",
        "location_en": "Off-Ice",
    },
    {
        "name_ar": "بروتوكول التدوير الظل",
        "name_en": "Shadow Spin Protocol",
        "desc_ar": "الدخول إلى التدوير بعيون مغلقة لتعزيز الإحساس الحركي والتوازن الداخلي.",
        "desc_en": "Enter spins with closed eyes to enhance proprioception and inner balance.",
        "target_ar": "التوازن الداخلي",
        "target_en": "proprioception",
        "muscles": "vestibular system",
        "duration": "10 min × 3 sets",
        "location_ar": "على الجليد",
        "location_en": "On-Ice",
    },
    {
        "name_ar": "سيمفونية حواف الموسيقى",
        "name_en": "Musical Edge Symphony",
        "desc_ar": "التزلج على حواف محددة متزامنة مع إيقاع الموسيقى. يجعل الحواف «تغني».",
        "desc_en": "Skate defined edges synchronized with music rhythm — edges that «sing».",
        "target_ar": "الموسيقالية",
        "target_en": "musicality",
        "muscles": "ankles, core",
        "duration": "15 min × 3 sets",
        "location_ar": "على الجليد",
        "location_en": "On-Ice",
    },
    {
        "name_ar": "تحدي الاسترداد السريع",
        "name_en": "Recovery Rush Challenge",
        "desc_ar": "قفزة + دوران + تتابع في 30 ثانية. يبني القدرة على التعافي السريع.",
        "desc_en": "Jump + spin + step sequence in 30s. Builds rapid recovery endurance.",
        "target_ar": "التحمل",
        "target_en": "endurance",
        "muscles": "full body",
        "duration": "30s bursts × 5",
        "location_ar": "على الجليد",
        "location_en": "On-Ice",
    },
    {
        "name_ar": "معجّل الدوران العصبي",
        "name_en": "Neuro-Rotation Accelerator",
        "desc_ar": "القفز مع تتبع هدف بصري أثناء الدوران لتعزيز التركيز وزيادة السرعة.",
        "desc_en": "Jump and track a visual target during rotation to enhance focus and speed.",
        "target_ar": "نقطة الارتكاز البصري",
        "target_en": "spotting",
        "muscles": "core, eyes",
        "duration": "12 min × 4 sets",
        "location_ar": "خارج الجليد",
        "location_en": "Off-Ice",
    },
]

PROGRESS_ROADMAP = [
    {"stage": 1, "title_ar": "التأسيس",    "title_en": "Foundation",   "months": 3,  "target": 220, "elements_ar": "قفزات مزدوجة، دورانات مستوى 3، تتابعات خطوات", "elements_en": "Clean doubles, Spins Level 3, Step sequences",   "done": True},
    {"stage": 2, "title_ar": "التطوير",    "title_en": "Development",  "months": 6,  "target": 260, "elements_ar": "Triple Axel، تتابعات ثلاثية، دورانات طائرة",     "elements_en": "Triple Axel, Triple combos, Flying spins",       "done": True},
    {"stage": 3, "title_ar": "التميز",     "title_en": "Excellence",   "months": 6,  "target": 280, "elements_ar": "Quad Toe، Quad Salchow، مكونات فنية 8.5+",       "elements_en": "Quad Toe, Quad Salchow, PCS 8.5+",               "done": False, "current": True},
    {"stage": 4, "title_ar": "المستوى العالمي","title_en": "World Class","months": 12,"target": 300, "elements_ar": "Quad Axel، Quad Lutz، نتيجة إجمالية 300+",      "elements_en": "Quad Axel, Quad Lutz, Total Score 300+",         "done": False},
]

ISU_RULES = [
    {"rule": "قاعدة Zayak",        "desc": "لا يمكن تكرار نفس نوع القفزة أكثر من مرتين في البرنامج الحر"},
    {"rule": "Edge Call",           "desc": "الحافة الخاطئة = خصم + علامة 'e' — تُخصم النقاط تلقائياً"},
    {"rule": "Under-rotation",      "desc": "نقص ≥90° = خصم كبير في GOE"},
    {"rule": "Fall",                "desc": "−5 GOE + خصم 1.00 نقطة إضافية"},
    {"rule": "وقت البرنامج الحر",  "desc": "Senior: 4:30 ± 10 ثانية | Junior: 4:00 ± 10 ثانية"},
    {"rule": "البرنامج القصير",     "desc": "Senior: 2:50 ± 10 ثانية | يحتوي على 8 عناصر محددة"},
    {"rule": "Zayak + Combo",       "desc": "الشوت بروجرام: 3 قفزات فقط، إحداها تتابع"},
    {"rule": "أعلى قيمة Quad Axel","desc": "12.50 BV — أعلى قفزة مُدرجة في قوائم ISU 2024"},
]


def _get_db():
    try:
        return sqlite3.connect('skating_database.db')
    except Exception:
        return None


def show_world_champions():
    ar = st.session_state.get('language', 'ar') == 'ar'

    st.markdown(
        f"<h2 style='text-align:center;color:#1a73e8'>"
        f"{'🏆 لوحة أبطال العالم والتدريب الاحترافي' if ar else '🏆 World Champions & Pro Training Dashboard'}"
        f"</h2>",
        unsafe_allow_html=True
    )

    tabs = st.tabs([
        "🏆 أبطال العالم" if ar else "🏆 World Champions",
        "📊 مقارنة الأداء" if ar else "📊 Performance Gap",
        "🔥 تدريبات مبتكرة" if ar else "🔥 Invented Drills",
        "⚖️ قواعد ISU" if ar else "⚖️ ISU Rules",
        "🛤️ مسار التقدم" if ar else "🛤️ Progress Roadmap",
    ])

    # ── Tab 1: Champions ──────────────────────────────────────────────────────
    with tabs[0]:
        st.subheader("🥇 " + ("أفضل المتزلجين في العالم — 2024" if ar else "World's Best Skaters — 2024"))

        for ch in WORLD_CHAMPIONS:
            medal = ["🥇","🥈","🥉","4️⃣","5️⃣"][ch['rank']-1]
            score_color = "#00c853" if ch['rank'] == 1 else "#1a73e8" if ch['rank'] <= 3 else "#c9d1d9"
            st.markdown(f"""
            <div style="background:#161b22;border:1px solid #30363d;border-radius:14px;
                        padding:16px 20px;margin-bottom:12px;display:flex;align-items:center;gap:16px">
                <div style="font-size:2em;min-width:45px;text-align:center">{medal}</div>
                <div style="flex:1">
                    <div style="font-size:18px;font-weight:700;color:#fff">{ch['flag']} {ch['name']}</div>
                    <div style="color:#8b949e;font-size:13px">{ch['country']} · {ch['age']} سنة · {ch['specialty']}</div>
                    <div style="margin-top:6px">
                        <span style="background:#1a73e833;color:#1a73e8;padding:3px 10px;border-radius:20px;font-size:12px">SP: {ch['sp']}</span>
                        <span style="background:#00c85333;color:#00c853;padding:3px 10px;border-radius:20px;font-size:12px;margin-right:6px">FS: {ch['fs']}</span>
                    </div>
                </div>
                <div style="text-align:center">
                    <div style="font-size:30px;font-weight:800;color:{score_color}">{ch['best_score']}</div>
                    <div style="font-size:11px;color:#8b949e">{'أفضل نتيجة' if ar else 'Best Score'}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Real skater from DB
        try:
            conn = _get_db()
            if conn:
                best_analysis = conn.execute(
                    "SELECT player_name, MAX(total_score) as score FROM analysis_results GROUP BY player_name ORDER BY score DESC LIMIT 1"
                ).fetchone()
                conn.close()
                if best_analysis and best_analysis[1]:
                    gap = WORLD_CHAMPIONS[0]['best_score'] - best_analysis[1]
                    st.markdown(f"""
                    <div style="background:#161b22;border:2px solid #1a73e8;border-radius:14px;
                                padding:16px 20px;margin-top:6px;display:flex;align-items:center;gap:16px">
                        <div style="font-size:2em;min-width:45px;text-align:center">⛸️</div>
                        <div style="flex:1">
                            <div style="font-size:18px;font-weight:700;color:#fff">🎯 {best_analysis[0]}</div>
                            <div style="color:#8b949e;font-size:13px">{'أفضل نتيجة مُحللة' if ar else 'Best Analyzed Score'}</div>
                        </div>
                        <div style="text-align:center">
                            <div style="font-size:30px;font-weight:800;color:#1a73e8">{best_analysis[1]:.1f}</div>
                            <div style="font-size:11px;color:#ff6d00">{'فجوة مع Malinin: −' if ar else 'Gap to Malinin: −'}{gap:.1f}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        except Exception:
            pass

    # ── Tab 2: Performance Gap ────────────────────────────────────────────────
    with tabs[1]:
        st.subheader("📊 " + ("تحليل الفجوة مع البطل العالمي" if ar else "Gap Analysis vs World Champion"))

        leader = WORLD_CHAMPIONS[0]

        try:
            import plotly.graph_objects as go
            import plotly.express as px

            conn = _get_db()
            user_score = 0.0
            if conn:
                row = conn.execute("SELECT MAX(total_score) FROM analysis_results").fetchone()
                if row and row[0]:
                    user_score = float(row[0])
                conn.close()

            categories_ar = ['النتيجة الكلية', 'ارتفاع القفزة', 'سرعة الدوران', 'المكونات الفنية', 'دقة الحواف']
            categories_en = ['Total Score', 'Jump Height', 'Rotation Speed', 'Components', 'Edge Quality']
            cats = categories_ar if ar else categories_en

            world_vals  = [333.69/3.33, 0.72/0.0072, 4.0/0.04,  9.5/0.095,  9.2/0.092]  # normalized to 100
            user_vals   = [user_score/3.33 if user_score else 73, 0.52/0.0072, 3.2/0.04, 7.0/0.095, 7.5/0.092]

            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(r=[min(v,100) for v in world_vals], theta=cats, fill='toself',
                                           name='Ilia Malinin', line_color='#00c853', opacity=0.5))
            fig.add_trace(go.Scatterpolar(r=[min(v,100) for v in user_vals], theta=cats, fill='toself',
                                           name='أنت / You', line_color='#1a73e8', opacity=0.6))
            fig.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                showlegend=True, height=400,
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#c9d1d9')
            )
            st.plotly_chart(fig, use_container_width=True)
        except Exception:
            pass

        gaps = [
            {"icon": "💪", "title_ar": "زيادة قوة الإقلاع",    "title_en": "Improve Takeoff Power",   "current": "0.52m", "target": "0.72m", "diff": "-0.20m",  "level": "🔴"},
            {"icon": "🔄", "title_ar": "تسريع الدوران",         "title_en": "Increase Rotation Speed",  "current": "3.2 rps","target": "4.0 rps","diff": "-0.8",   "level": "🔴"},
            {"icon": "⛸️", "title_ar": "تحسين جودة الحواف",     "title_en": "Edge Quality Improvement", "current": "7.5",   "target": "9.0",   "diff": "-1.5",   "level": "🟡"},
            {"icon": "🎭", "title_ar": "المكونات الفنية (PCS)", "title_en": "Program Components (PCS)", "current": "7.0",   "target": "9.5",   "diff": "-2.5",   "level": "🔴"},
        ]
        for g in gaps:
            title = g['title_ar'] if ar else g['title_en']
            st.markdown(f"""
            <div style="background:#161b22;border:1px solid #30363d;border-radius:10px;
                        padding:14px 18px;margin-bottom:10px;display:flex;align-items:center;gap:14px">
                <div style="font-size:1.5em">{g['icon']}</div>
                <div style="flex:1">
                    <div style="font-weight:600;color:#fff">{title}</div>
                    <div style="color:#8b949e;font-size:12px;margin-top:3px">
                        {'الحالي: ' if ar else 'Current: '}{g['current']} → {'الهدف: ' if ar else 'Target: '}{g['target']}
                    </div>
                </div>
                <div style="text-align:center;font-size:18px;font-weight:700;color:#ff1744">{g['diff']}</div>
                <div style="font-size:1.4em">{g['level']}</div>
            </div>
            """, unsafe_allow_html=True)

    # ── Tab 3: Invented Drills ────────────────────────────────────────────────
    with tabs[2]:
        st.subheader("🔥 " + ("التدريبات المبتكرة — مولدة بالذكاء الاصطناعي" if ar else "Invented Drills — AI Generated"))
        st.info(
            "هذه التدريبات مولدة بالذكاء الاصطناعي بناءً على تحليل أداء أبطال العالم. فهي مقترحة ومميزة بلون برتقالي." if ar else
            "These drills are AI-generated based on world champion performance analysis. They are suggested (orange) and not official ISU drills."
        )

        for d in INVENTED_DRILLS:
            name = d['name_ar'] if ar else d['name_en']
            desc = d['desc_ar'] if ar else d['desc_en']
            loc  = d['location_ar'] if ar else d['location_en']
            tgt  = d['target_ar'] if ar else d['target_en']

            st.markdown(f"""
            <div style="background:rgba(255,109,0,0.07);border:1px solid rgba(255,109,0,0.4);border-right:4px solid #ff6d00;
                        border-radius:10px;padding:16px 18px;margin-bottom:12px">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
                    <div style="font-size:16px;font-weight:700;color:#fff">{name}</div>
                    <span style="background:rgba(255,109,0,0.2);color:#ff6d00;padding:3px 12px;border-radius:20px;font-size:12px;font-weight:600">مبتكر 🔥</span>
                </div>
                <div style="color:#8b949e;font-size:13px;margin-bottom:10px">{desc}</div>
                <div style="display:flex;gap:16px;flex-wrap:wrap;font-size:12px;color:#8b949e">
                    <span>⏱️ {d['duration']}</span>
                    <span>📍 {loc}</span>
                    <span>🎯 {tgt}</span>
                    <span>💪 {d['muscles']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # ── Tab 4: ISU Rules ──────────────────────────────────────────────────────
    with tabs[3]:
        st.subheader("⚖️ " + ("القواعد الأساسية — ISU Communication 2788" if ar else "Core Rules — ISU Communication 2788"))

        for r in ISU_RULES:
            st.markdown(f"""
            <div style="background:#161b22;border:1px solid #30363d;border-radius:8px;
                        padding:12px 16px;margin-bottom:8px;display:flex;align-items:flex-start;gap:12px">
                <div style="background:#1a73e833;color:#1a73e8;padding:4px 10px;border-radius:6px;font-size:12px;
                            font-weight:700;white-space:nowrap;min-width:120px;text-align:center">{r['rule']}</div>
                <div style="color:#c9d1d9;font-size:14px">{r['desc']}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("📋 " + ("قيم القفزات الأساسية ISU 2024" if ar else "ISU 2024 Jump Base Values"))
        bv_data = {
            "القفزة": ["4A (Quad Axel)","4Lz (Quad Lutz)","4F (Quad Flip)","4Lo (Quad Loop)","4S (Quad Salchow)","4T (Quad Toe)","3A (Triple Axel)","3Lz (Triple Lutz)","3F (Triple Flip)","3Lo (Triple Loop)"],
            "BV": [12.50, 11.50, 11.00, 10.50, 9.70, 9.50, 8.00, 5.90, 5.30, 5.10],
            "الحافة": ["لا ينطبق","Lutz خارجية","Flip داخلية","لا ينطبق","لا ينطبق","لا ينطبق","لا ينطبق","Lutz خارجية","Flip داخلية","لا ينطبق"],
        }
        st.dataframe(pd.DataFrame(bv_data), use_container_width=True, hide_index=True)

    # ── Tab 5: Progress Roadmap ───────────────────────────────────────────────
    with tabs[4]:
        st.subheader("🛤️ " + ("مسار التقدم إلى المستوى العالمي" if ar else "Roadmap to World-Class Level"))

        for stage in PROGRESS_ROADMAP:
            title = stage['title_ar'] if ar else stage['title_en']
            elements = stage['elements_ar'] if ar else stage['elements_en']
            is_cur = stage.get('current', False)
            is_done = stage['done']

            if is_done:
                icon, border, bg = "✅", "#00c853", "rgba(0,200,83,0.06)"
            elif is_cur:
                icon, border, bg = "🎯", "#1a73e8", "rgba(26,115,232,0.1)"
            else:
                icon, border, bg = "🏆", "#ff6d00", "rgba(255,109,0,0.05)"

            label = ("الحالي" if ar else "Current") if is_cur else ("مكتمل" if ar else "Done") if is_done else ("قادم" if ar else "Ahead")

            st.markdown(f"""
            <div style="background:{bg};border:2px solid {border};border-radius:14px;
                        padding:16px 20px;margin-bottom:14px">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
                    <div style="display:flex;align-items:center;gap:12px">
                        <div style="background:{border}33;color:{border};width:36px;height:36px;border-radius:50%;
                                    display:flex;align-items:center;justify-content:center;font-weight:800;font-size:16px">{stage['stage']}</div>
                        <div>
                            <div style="font-size:17px;font-weight:700;color:#fff">{title}</div>
                            <div style="font-size:12px;color:#8b949e">{'المدة: ' if ar else 'Duration: '}{stage['months']} {'شهر' if ar else 'months'} · {'الهدف: ' if ar else 'Target: '}{stage['target']} {'نقطة' if ar else 'pts'}</div>
                        </div>
                    </div>
                    <div style="display:flex;align-items:center;gap:8px">
                        <span style="background:{border}22;color:{border};padding:4px 12px;border-radius:20px;font-size:12px">{label}</span>
                        <div style="font-size:1.5em">{icon}</div>
                    </div>
                </div>
                <div style="color:#8b949e;font-size:13px;border-top:1px solid #30363d;padding-top:8px">{elements}</div>
            </div>
            """, unsafe_allow_html=True)

        # Progress meter
        st.markdown("---")
        completed = sum(1 for s in PROGRESS_ROADMAP if s['done'])
        total = len(PROGRESS_ROADMAP)
        pct = completed / total
        st.metric(
            "📈 " + ("إجمالي التقدم" if ar else "Overall Progress"),
            f"{completed}/{total} " + ("مراحل مكتملة" if ar else "stages completed")
        )
        st.progress(pct)
