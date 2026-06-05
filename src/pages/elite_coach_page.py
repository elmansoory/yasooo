"""
صفحة المدرب النخبة - Elite Coach Page
نظام تدريب متكامل للوصول إلى مستوى البطولة العالمية
"""
import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

DB_PATH = "skating_database.db"


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def _get_conn():
    return sqlite3.connect(DB_PATH)


def _load_skaters():
    try:
        conn = _get_conn()
        df = pd.read_sql_query(
            "SELECT id, name FROM skaters ORDER BY name", conn
        )
        conn.close()
        return df
    except Exception:
        return pd.DataFrame(columns=["id", "name"])


def _load_analysis_results(skater_id):
    try:
        conn = _get_conn()
        df = pd.read_sql_query(
            "SELECT * FROM analysis_results WHERE skater_id = ? ORDER BY created_at DESC LIMIT 5",
            conn,
            params=(skater_id,),
        )
        conn.close()
        return df
    except Exception:
        return pd.DataFrame()


def _load_drills_db():
    try:
        db_path = Path(__file__).parent.parent.parent / "data" / "drills_database.json"
        with open(db_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"drills": []}


# ---------------------------------------------------------------------------
# Tab 1: Performance Analysis
# ---------------------------------------------------------------------------

def _tab_performance_analysis(ar):
    title = "تحليل الأداء" if ar else "Performance Analysis"
    st.header(f"🧠 {title}")

    skaters_df = _load_skaters()

    if skaters_df.empty:
        msg = "لا توجد بيانات متزلجين في قاعدة البيانات." if ar else "No skaters found in the database."
        st.info(msg)
        skater_name = st.text_input("اسم المتزلج / Skater Name", value="متزلج تجريبي / Demo Skater")
        skater_id = None
    else:
        options = skaters_df["name"].tolist()
        selected = st.selectbox("اختر المتزلج / Select Skater", options)
        skater_id = int(skaters_df.loc[skaters_df["name"] == selected, "id"].values[0])
        skater_name = selected

    st.subheader(f"📊 {'لوحة الأداء' if ar else 'Performance Dashboard'}: {skater_name}")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown(f"### {'أدخل درجات الأداء' if ar else 'Enter Performance Scores'}")
        jump_technique = st.slider("🏒 " + ("تقنية القفز / Jump Technique" if ar else "Jump Technique"), 0, 100, 62)
        spin_quality = st.slider("🌀 " + ("جودة الدوران / Spin Quality" if ar else "Spin Quality"), 0, 100, 70)
        step_sequences = st.slider("👣 " + ("تسلسل الخطوات / Step Sequences" if ar else "Step Sequences"), 0, 100, 55)
        pcs_artistry = st.slider("🎭 " + ("الفنية / PCS Artistry" if ar else "PCS Artistry"), 0, 100, 65)
        edge_quality = st.slider("⚡ " + ("جودة الحافة / Edge Quality" if ar else "Edge Quality"), 0, 100, 60)
        comp_readiness = st.slider("🏆 " + ("الجاهزية للمنافسة / Competition Readiness" if ar else "Competition Readiness"), 0, 100, 50)

    scores = {
        "Jump Technique": jump_technique,
        "Spin Quality": spin_quality,
        "Step Sequences": step_sequences,
        "PCS Artistry": pcs_artistry,
        "Edge Quality": edge_quality,
        "Competition Readiness": comp_readiness,
    }

    world_class = {
        "Jump Technique": 92,
        "Spin Quality": 90,
        "Step Sequences": 88,
        "PCS Artistry": 91,
        "Edge Quality": 93,
        "Competition Readiness": 95,
    }

    with col2:
        categories = list(scores.keys())
        skater_vals = list(scores.values())
        wc_vals = list(world_class.values())

        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=skater_vals + [skater_vals[0]],
            theta=categories + [categories[0]],
            fill="toself",
            name=skater_name,
            line_color="#00b4d8",
            fillcolor="rgba(0,180,216,0.2)",
        ))
        fig.add_trace(go.Scatterpolar(
            r=wc_vals + [wc_vals[0]],
            theta=categories + [categories[0]],
            fill="toself",
            name="World Class Benchmark",
            line_color="#ffd60a",
            fillcolor="rgba(255,214,10,0.1)",
        ))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            showlegend=True,
            title="Performance Radar vs World Class",
            height=400,
            paper_bgcolor="#0e1117",
            plot_bgcolor="#0e1117",
            font_color="white",
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("📈 " + ("العناصر الحالية مقابل المعايير العالمية" if ar else "Current Scores vs World-Class Benchmarks"))

    bench_rows = []
    for cat, val in scores.items():
        wc = world_class[cat]
        gap = wc - val
        bench_rows.append({
            "العنصر / Element": cat,
            "الدرجة الحالية / Current": val,
            "المعيار العالمي / World Class": wc,
            "الفجوة / Gap": gap,
        })

    bench_df = pd.DataFrame(bench_rows)
    st.dataframe(bench_df, use_container_width=True)

    # Top 3 weaknesses
    sorted_scores = sorted(scores.items(), key=lambda x: x[1])
    top3_weak = sorted_scores[:3]

    st.markdown("---")
    st.subheader("⚠️ " + ("أكبر 3 نقاط ضعف" if ar else "Top 3 Weaknesses"))
    w_col1, w_col2, w_col3 = st.columns(3)
    for idx, (wcol, (elem, val)) in enumerate(zip([w_col1, w_col2, w_col3], top3_weak)):
        with wcol:
            delta = val - world_class[elem]
            st.metric(
                label=f"#{idx+1} {elem}",
                value=f"{val}/100",
                delta=f"{delta} vs World Class",
                delta_color="inverse",
            )

    # Competition Readiness Score
    st.markdown("---")
    avg_score = sum(scores.values()) / len(scores)
    st.subheader("🏆 " + ("درجة الجاهزية للمنافسة" if ar else "Competition Readiness Score"))

    if avg_score >= 85:
        color = "green"
        label = "جاهز للبطولة / World Championship Ready" if ar else "World Championship Ready"
    elif avg_score >= 70:
        color = "orange"
        label = "جاهز للمنافسات الإقليمية / Regional Competition Ready" if ar else "Regional Competition Ready"
    elif avg_score >= 55:
        color = "blue"
        label = "مستوى ناشئين / Developing Level" if ar else "Developing Level"
    else:
        color = "red"
        label = "مرحلة التأسيس / Foundation Stage" if ar else "Foundation Stage"

    st.markdown(
        f"""
        <div style="background-color:{color};padding:20px;border-radius:10px;text-align:center;">
            <h2 style="color:white;margin:0;">{avg_score:.1f} / 100</h2>
            <p style="color:white;margin:5px 0;">{label}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Tab 2: On-Ice Training Program
# ---------------------------------------------------------------------------

def _tab_on_ice_training(ar):
    title = "برنامج التدريب على الجليد" if ar else "On-Ice Training Program"
    st.header(f"🏒 {title}")

    col1, col2, col3 = st.columns(3)
    with col1:
        level_options = ["Pre-Juvenile / ما قبل الناشئين", "Juvenile / الناشئين", "Novice / المتقدمين", "Junior / الجونيور", "Senior / الكبار"]
        level = st.selectbox("المستوى / Level", level_options)
    with col2:
        weak_options = ["Triple Axel", "Triple Lutz", "Triple Flip", "Triple Loop", "Spins Centering", "Step Sequences", "PCS Quality"]
        weak_elements = st.multiselect("العناصر الضعيفة / Weak Elements", weak_options, default=["Triple Lutz", "Spins Centering"])
    with col3:
        ice_hours = st.slider("وقت الجليد الأسبوعي / Weekly Ice Time (hrs)", 5, 30, 15)

    if st.button("🗓️ " + ("إنشاء برنامج التدريب الأسبوعي" if ar else "Generate Weekly Training Plan"), type="primary"):
        st.success("✅ " + ("تم إنشاء برنامج التدريب!" if ar else "Training program generated!"))
        _render_weekly_schedule(ar, level, weak_elements, ice_hours)
    else:
        _render_weekly_schedule(ar, level, weak_elements if weak_elements else ["Triple Lutz"], ice_hours)


def _render_weekly_schedule(ar, level, weak_elements, ice_hours):
    daily_hours = round(ice_hours / 6, 1)

    schedule = {
        "Monday / الاثنين": {
            "focus": "Jump Focus — " + (weak_elements[0] if weak_elements else "Axel"),
            "warmup": "15 min — Forward/backward crossovers, spiral sequence, edge warm-up circles",
            "main_block": [
                {"drill": "Pre-Jump Glide", "duration": "10 min", "reps": "8 reps", "cue": "Controlled entry speed, deep approach edge"},
                {"drill": "Three-Turn Entry Drill", "duration": "15 min", "reps": "5×8", "cue": "Edge first — hold back inside edge 2 counts before pick"},
                {"drill": "Repeated Takeoff Drill", "duration": "10 min", "reps": "4×12", "cue": "Explosive upward drive — toe pick behind the body"},
                {"drill": "One-Foot Landing Hold", "duration": "12 min", "reps": "15 reps", "cue": "Hold landing 3 seconds — outside edge, bent knee"},
                {"drill": "Full Jumps — " + (weak_elements[0] if weak_elements else "Triple"), "duration": "15 min", "reps": "8 attempts", "cue": "Quality over quantity — rest between each"},
            ],
            "cooldown": "10 min — Backward power pulls, easy stroking, stretching",
        },
        "Tuesday / الثلاثاء": {
            "focus": "Spin Program + PCS Elements",
            "warmup": "15 min — Easy stroking, back crossovers, forward edges",
            "main_block": [
                {"drill": "One-Foot Balance Circles", "duration": "8 min", "reps": "10 circles each foot", "cue": "Find the sweet spot — ball of the foot, not toe pick"},
                {"drill": "Scratch Spin Entry Variations", "duration": "12 min", "reps": "12 spins", "cue": "Count rotations — aim for 8+ per spin"},
                {"drill": "Back Scratch Position Hold", "duration": "10 min", "reps": "15 back spins", "cue": "Back inside edge — cross free foot for maximum RPM"},
                {"drill": "Flying Camel Approach", "duration": "12 min", "reps": "10 attempts", "cue": "Jump forward — camel position BEFORE landing"},
                {"drill": "Full Combination Spin", "duration": "15 min", "reps": "8 combos", "cue": "4 positions, no deceleration between positions"},
            ],
            "cooldown": "8 min — Camel position holds, layback stretching",
        },
        "Wednesday / الأربعاء": {
            "focus": "Edge Work + Step Sequence",
            "warmup": "15 min — Power pulls down the rink, consecutive edges",
            "main_block": [
                {"drill": "Power Pull Exercise", "duration": "10 min", "reps": "8 lengths", "cue": "Accelerate using only edge pressure — no stroking"},
                {"drill": "Consecutive Outside Edges", "duration": "12 min", "reps": "4 sets each edge type", "cue": "Equal size lobes — trace is the judge"},
                {"drill": "Three-Turn Series", "duration": "10 min", "reps": "6 series", "cue": "Sharp point in the ice — not a scrape"},
                {"drill": "Mohawk-Choctaw Sequences", "duration": "12 min", "reps": "8 sequences", "cue": "Light quick steps — maintain ice coverage"},
                {"drill": "Step Sequence Run-Through", "duration": "15 min", "reps": "6 run-throughs", "cue": "Enter slow, exit FASTER — generate speed through steps"},
            ],
            "cooldown": "8 min — Easy stroking, crossovers, stretching",
        },
        "Thursday / الخميس": {
            "focus": "Program Run-Throughs",
            "warmup": "15 min — Full body warm-up with jumps and spins isolated",
            "main_block": [
                {"drill": "Short Program Run-Through (no music)", "duration": "10 min", "reps": "2 run-throughs", "cue": "Focus on connection between elements — transitions"},
                {"drill": "Short Program Run-Through (with music)", "duration": "15 min", "reps": "3 run-throughs", "cue": "Performance quality — eyes up, expression"},
                {"drill": "Problem Element Isolation", "duration": "15 min", "reps": "Targeted practice", "cue": "Whatever went wrong in run-throughs — fix it here"},
                {"drill": "Free Skate Excerpt (2nd half)", "duration": "10 min", "reps": "2 run-throughs", "cue": "Second half jump bonus — maintain quality when tired"},
            ],
            "cooldown": "10 min — Cool down stroking, artistic flow practice",
        },
        "Friday / الجمعة": {
            "focus": "Jump Refinement + Combinations",
            "warmup": "15 min — Off-ice warm-up followed by on-ice edge warm-up",
            "main_block": [
                {"drill": "Wall Jump Drill (off-ice)", "duration": "8 min", "reps": "3×10", "cue": "Check-out position — free leg back and held"},
                {"drill": "Jump Combinations on Ice", "duration": "20 min", "reps": "10 combo attempts", "cue": "Second jump must be as strong as the first"},
                {"drill": "Back Outside Edge Circle (Axel prep)", "duration": "8 min", "reps": "6 circles each direction", "cue": "Consistent arc — do not let the circle shrink"},
                {"drill": "Second Half Program Jumps", "duration": "12 min", "reps": "All second-half jumps", "cue": "Simulate the fatigue of a real program — go through combinations"},
            ],
            "cooldown": "8 min — Slow stroking, deep stretching",
        },
        "Saturday / السبت": {
            "focus": "Full Program Simulation",
            "warmup": "15 min — Full competition warm-up protocol",
            "main_block": [
                {"drill": "SP + FS Back-to-Back", "duration": "35 min", "reps": "Full programs", "cue": "Competition mindset — judges are watching, perform every element"},
                {"drill": "Debrief and Correction", "duration": "15 min", "reps": "Video review", "cue": "Review footage — identify top 3 corrections for next week"},
            ],
            "cooldown": "10 min — Recovery skate, mental cool-down",
        },
    }

    for day, content in schedule.items():
        with st.expander(f"📅 {day} — {content['focus']}", expanded=False):
            st.markdown(f"**🌡️ {'الإحماء' if ar else 'Warm-Up'}:** {content['warmup']}")
            st.markdown(f"**⏱ {'مدة الجلسة' if ar else 'Session Duration'}:** ~{daily_hours} hours")
            st.markdown(f"**🎯 {'التركيز' if ar else 'Focus'}:** {content['focus']}")
            st.markdown("---")
            st.markdown(f"**🏒 {'الكتلة الرئيسية' if ar else 'Main Block'}:**")

            rows = []
            for item in content["main_block"]:
                rows.append({
                    "التمرين / Drill": item["drill"],
                    "المدة / Duration": item["duration"],
                    "التكرارات / Reps": item["reps"],
                    "توجيه المدرب / Coach Cue": item["cue"],
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            st.markdown(f"**❄️ {'التهدئة' if ar else 'Cool-Down'}:** {content['cooldown']}")


# ---------------------------------------------------------------------------
# Tab 3: Off-Ice Conditioning
# ---------------------------------------------------------------------------

def _tab_off_ice_conditioning(ar):
    title = "برنامج التدريب خارج الجليد" if ar else "Off-Ice Conditioning Program"
    st.header(f"💪 {title}")

    tabs = st.tabs([
        "💥 " + ("القوة والقدرة" if ar else "Strength & Power"),
        "🌀 " + ("تدريب الدوران" if ar else "Rotation Training"),
        "🩰 " + ("المرونة والفنون" if ar else "Flexibility & Artistry"),
        "🧠 " + ("التدريب الذهني" if ar else "Mental Training"),
    ])

    with tabs[0]:
        st.subheader("💥 " + ("القوة والقدرة" if ar else "Strength & Power"))

        st.markdown("### 🏃 " + ("البليومتريكس / Plyometrics" if ar else "Plyometrics"))
        plyo = [
            {"exercise": "Box Jumps / القفز على الصندوق", "sets": "3", "reps": "10", "rest": "60s", "notes": "Land softly — absorb through knees"},
            {"exercise": "Jump Squats / القفز القرفصاء", "sets": "4", "reps": "8", "rest": "60s", "notes": "Maximum height — arms drive upward"},
            {"exercise": "Single-Leg Bounds / القفز على قدم واحدة", "sets": "3", "reps": "12 each", "rest": "60s", "notes": "Cover maximum horizontal distance"},
            {"exercise": "Depth Jumps / قفز العمق", "sets": "3", "reps": "6", "rest": "90s", "notes": "Minimal ground contact time — reactive"},
        ]
        plyo_df = pd.DataFrame(plyo)
        st.dataframe(plyo_df, use_container_width=True, hide_index=True)

        st.markdown("### 🏋️ " + ("القوة / Strength"))
        strength = [
            {"exercise": "Bulgarian Split Squat / القرفصاء البلغاري", "sets": "4", "reps": "8 each", "rest": "90s", "notes": "Rear foot elevated — deep range"},
            {"exercise": "Romanian Deadlift / رفعة رومانية", "sets": "3", "reps": "10", "rest": "90s", "notes": "Hip hinge — hamstring stretch at bottom"},
            {"exercise": "Hip Thrusts / دفع الورك", "sets": "4", "reps": "12", "rest": "60s", "notes": "Full glute extension at top"},
            {"exercise": "Single-Leg Press / ضغط الساق الواحدة", "sets": "3", "reps": "10 each", "rest": "60s", "notes": "Mirrors single-leg landing mechanics"},
        ]
        st.dataframe(pd.DataFrame(strength), use_container_width=True, hide_index=True)

        st.markdown("### 🧱 " + ("الجذع / Core"))
        core_exercises = [
            {"exercise": "Plank Rotations / تدوير الكوبرا", "sets": "3", "reps": "12 each side", "cue": "Hips level throughout"},
            {"exercise": "Russian Twists / الدوران الروسي", "sets": "3", "reps": "20 total", "cue": "Feet off floor, rotate to full range"},
            {"exercise": "V-Ups / رفعة V", "sets": "3", "reps": "15", "cue": "Straight legs — meet hands to feet at peak"},
            {"exercise": "Dead Bugs / الخنفساء الميتة", "sets": "3", "reps": "10 each side", "cue": "Lower back pressed to floor throughout"},
        ]
        st.dataframe(pd.DataFrame(core_exercises), use_container_width=True, hide_index=True)

        st.markdown("### 📅 " + ("جدول التدوير الأسبوعي / Weekly Periodization"))
        period = {
            "اليوم / Day": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
            "التركيز / Focus": ["Lower Body Power", "Core + Rotation", "Upper Body", "Recovery + Stretch", "Full Body Power", "Competition Sim", "Rest"],
            "الشدة / Intensity": ["High", "Medium", "Medium", "Low", "High", "Medium", "None"],
        }
        st.dataframe(pd.DataFrame(period), use_container_width=True, hide_index=True)

        st.markdown("### ✅ " + ("تتبع التمارين / Exercise Tracker"))
        exercises_to_track = ["Box Jumps", "Jump Squats", "Single-Leg Bounds", "Depth Jumps", "Bulgarian Split Squat", "Romanian Deadlift", "Hip Thrusts", "Single-Leg Press"]
        for ex in exercises_to_track:
            st.checkbox(f"✅ {ex}", key=f"strength_{ex}")

    with tabs[1]:
        st.subheader("🌀 " + ("تدريب الدوران" if ar else "Rotation Training"))

        st.markdown("### 🎪 " + ("تمارين الترامبولين / Trampoline Work"))
        trampoline = [
            {"drill": "Single Rotation Drill", "description": "Jump and complete exactly one full rotation — focus on vertical height first"},
            {"drill": "Double Rotation Drill", "description": "Consistent doubles from trampoline — use harness initially"},
            {"drill": "Triple Rotation Drill", "description": "Advanced — triple rotation at full height — arms pulled in maximum tight"},
            {"drill": "Layout Position Drill", "description": "Jump with arms fully extended overhead — no rotation — pure height"},
        ]
        for item in trampoline:
            with st.expander(f"🎪 {item['drill']}"):
                st.write(item["description"])

        st.markdown("### 🎡 " + ("منصة الدوران / Spinning Platform"))
        platform_items = [
            "Entry positions: start in each jump entry position (Lutz, Flip, Axel, Loop) before spinning",
            "Check-out technique: stop the spin exactly at 360, 720, 1080 — precision practice",
            "Pull-in timing: experiment with different arm positions to find maximum RPM configuration",
            "Back spin on platform: back inside edge balance transferred to spinning platform",
        ]
        for item in platform_items:
            st.markdown(f"• {item}")

        st.markdown("### 🪢 " + ("قفز بالحزام / Harness Jumps"))
        harness_items = [
            "Supported triple attempts: harness provides full lift — skater focuses on rotation technique",
            "Partial support quad attempts: harness provides safety only — skater must generate own height",
            "Quad toe loop harness: safest quad to learn — entry from backward outside edge",
            "Triple Axel harness: forward takeoff makes this the most complex — harness is essential early",
        ]
        for item in harness_items:
            st.markdown(f"• {item}")

        st.markdown("### 🩰 " + ("دوران خارج الجليد / Off-Ice Spin Practice"))
        spin_off_ice = [
            {"position": "Biellmann Position", "drill": "Daily stretch progression — back kick beyond head height", "frequency": "Daily — 15 min"},
            {"position": "Camel Position", "drill": "Hip rotation exercises at barre — hold 30 seconds", "frequency": "Daily — 10 min"},
            {"position": "Sit Spin", "drill": "Deep squat holds below parallel with free leg extended", "frequency": "Daily — 10 min"},
            {"position": "Layback", "drill": "Upper back arch progressive stretching — never lower back", "frequency": "Daily — 8 min"},
        ]
        st.dataframe(pd.DataFrame(spin_off_ice), use_container_width=True, hide_index=True)

    with tabs[2]:
        st.subheader("🩰 " + ("المرونة والفنون" if ar else "Flexibility & Artistry"))

        st.markdown("### 🤸 " + ("إطالات المرونة / Flexibility Stretches"))
        flex_items = [
            {"stretch": "Front Split / الانقسام الأمامي", "hold": "60 sec each side", "frequency": "Daily"},
            {"stretch": "Side Split / الانقسام الجانبي", "hold": "60 sec", "frequency": "Daily"},
            {"stretch": "Spiral Leg Extension / امتداد الساق الحلزوني", "hold": "30 sec", "frequency": "Daily"},
            {"stretch": "Layback Position / الاستلقاء للخلف", "hold": "30 sec", "frequency": "Daily"},
            {"stretch": "Biellmann Pull / سحب بيلمان", "hold": "45 sec each side", "frequency": "Daily"},
            {"stretch": "Hip Flexor Psoas Stretch / إطالة الفخذ الأمامي", "hold": "45 sec each side", "frequency": "Daily"},
        ]
        st.dataframe(pd.DataFrame(flex_items), use_container_width=True, hide_index=True)

        st.markdown("### 🎭 " + ("باليه الحاجز / Ballet Barre"))
        ballet = [
            {"exercise": "Tendus / تانديو", "reps": "16 each direction", "purpose": "Foot articulation and pointed toe"},
            {"exercise": "Dégagés / ديغاجيه", "reps": "16 each direction", "purpose": "Quick foot off floor — ankle strength"},
            {"exercise": "Développés / ديفيلوبيه", "reps": "8 each direction", "purpose": "Leg extension and hip flexibility"},
            {"exercise": "Grand Battements / غراند باتمان", "reps": "8 each direction", "purpose": "Maximum leg height and power"},
            {"exercise": "Ronds de jambe / رون دو جامب", "reps": "8 each direction", "purpose": "Hip rotation and flexibility"},
        ]
        st.dataframe(pd.DataFrame(ballet), use_container_width=True, hide_index=True)

        st.markdown("### 🎨 " + ("التدريب الفني / Artistic Training"))
        artistic = [
            "Mirror practice: 15 min daily — watch your arm positions, head, and expression",
            "Music interpretation: listen to your program music 3x daily — find the emotion in each phrase",
            "Expression exercises: practice delivering emotion to a 'judge' at the end of the rink",
            "Video analysis: watch World Champion programs — emulate the performance quality",
            "Choreography walk-through: walk through program without skates to focus purely on artistry",
        ]
        for item in artistic:
            st.markdown(f"• {item}")

    with tabs[3]:
        st.subheader("🧠 " + ("التدريب الذهني" if ar else "Mental Training"))

        st.markdown("### 🎯 " + ("التصور الذهني / Visualization"))
        st.info(
            "**" + ("البروتوكول اليومي للتصور" if ar else "Daily Visualization Protocol") + "** — 5 minutes every morning:\n"
            "1. Close eyes and take 5 deep breaths\n"
            "2. Visualize walking into the arena — feel the cold air, hear the music\n"
            "3. See yourself executing every element perfectly in your SP or FS\n"
            "4. Feel the landing of every jump — solid, controlled, crowd reacting\n"
            "5. See yourself receiving your scores — the number you are targeting\n"
            "6. Open eyes and write down what you saw — anchor the image"
        )

        st.markdown("### 🎪 " + ("تمارين التركيز / Focus Drills"))
        focus = [
            {"drill": "Clean Run-Through Challenge", "description": "Attempt the entire program — no falls, no stumbles. If any error occurs, note it and repeat the program immediately."},
            {"drill": "One-Element Focus", "description": "Choose one element and execute it 10 times in a row — any error resets the count. Develops consistency under pressure."},
            {"drill": "Eyes-of-a-Judge Drill", "description": "Skate as if a panel of 9 judges is watching every single second — maximum performance quality throughout."},
            {"drill": "The Last Element Focus", "description": "The last jump or spin in your program — practice it in isolation as the most important element, because fatigue makes it the hardest."},
        ]
        for item in focus:
            with st.expander(f"🧠 {item['drill']}"):
                st.write(item["description"])

        st.markdown("### 🏆 " + ("محاكاة المنافسة / Competition Simulation"))
        sim_protocol = [
            "Full program with 3 judges sitting rinkside — even if they are parents or coaches",
            "Wear competition costume — the psychological impact is real",
            "Replicate competition warm-up: 6-minute group warm-up protocol",
            "Run the program under time pressure — use a stopwatch",
            "Simulate a previous fall: execute a fall on purpose, stand up immediately, and continue — practice recovery",
            "Post-program debrief: what GOE would each element receive? Self-score honestly",
        ]
        for item in sim_protocol:
            st.markdown(f"• {item}")

        st.markdown("### ✅ " + ("تتبع التدريب الذهني / Mental Training Tracker"))
        mental_exercises = ["Morning Visualization (5 min)", "Clean Run-Through Challenge", "Music Listening (3x)", "Mirror Practice (15 min)", "Competition Simulation", "Journal/Reflection"]
        for ex in mental_exercises:
            st.checkbox(f"✅ {ex}", key=f"mental_{ex}")


# ---------------------------------------------------------------------------
# Tab 4: Drill Library
# ---------------------------------------------------------------------------

def _tab_drill_library(ar):
    title = "مكتبة التمارين" if ar else "Drill Library"
    st.header(f"📋 {title}")

    drills_db = _load_drills_db()
    drills = drills_db.get("drills", [])

    if not drills:
        st.error("لا يمكن تحميل قاعدة بيانات التمارين." if ar else "Cannot load drills database.")
        return

    # Filters
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        all_cats = sorted(set(d["category"] for d in drills))
        cat_filter = st.selectbox("الفئة / Category", ["All"] + all_cats)
    with col2:
        all_levels = sorted(set(d["level"] for d in drills))
        level_filter = st.selectbox("المستوى / Level", ["All"] + all_levels)
    with col3:
        all_locations = sorted(set(d["location"] for d in drills))
        loc_filter = st.selectbox("الموقع / Location", ["All"] + all_locations)
    with col4:
        search_term = st.text_input("🔍 " + ("بحث / Search"), "")

    # Filter drills
    filtered = drills
    if cat_filter != "All":
        filtered = [d for d in filtered if d["category"] == cat_filter]
    if level_filter != "All":
        filtered = [d for d in filtered if d["level"] == level_filter]
    if loc_filter != "All":
        filtered = [d for d in filtered if d["location"] == loc_filter]
    if search_term:
        st._term = search_term.lower()
        filtered = [
            d for d in filtered
            if st._term in d["name_en"].lower()
            or st._term in d["name_ar"]
            or st._term in d["purpose"].lower()
        ]

    st.markdown(f"**{'التمارين المعروضة' if ar else 'Showing'}:** {len(filtered)} / {len(drills)}")

    level_colors = {"basic": "🟢", "intermediate": "🟡", "advanced": "🟠", "elite": "🔴"}

    for drill in filtered:
        level_icon = level_colors.get(drill["level"], "⚪")
        expander_title = f"{level_icon} [{drill['id']}] {drill['name_ar']} / {drill['name_en']} — {drill['category'].upper()}"
        with st.expander(expander_title):
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown(f"**🎯 {'الهدف / Purpose'}:** {drill['purpose']}")
                st.markdown(f"**📍 {'الموقع / Location'}:** {drill['location']}")
                st.markdown(f"**⏱ {'المدة / Duration'}:** {drill['duration_minutes']} min")
                st.markdown(f"**🔁 {'التكرارات / Reps'}:** {drill['repetitions']}")
                st.markdown(f"**🛠 {'المعدات / Equipment'}:** {drill['equipment']}")

            with col_b:
                st.markdown(f"**🎿 {'العناصر المستهدفة / Target Elements'}:** {', '.join(drill['target_elements'])}")
                st.markdown(f"**📊 {'المستوى / Level'}:** {drill['level'].capitalize()}")

            st.markdown("**📝 " + ("خطوات الأداء / How to Perform" if ar else "How to Perform") + ":**")
            for i, step in enumerate(drill["steps"], 1):
                st.markdown(f"{i}. {step}")

            st.markdown("**💬 " + ("توجيهات المدرب / Coach Cues" if ar else "Coach Cues") + ":**")
            for cue in drill["coach_cues"]:
                st.markdown(f"• {cue}")

            col_c, col_d = st.columns(2)
            with col_c:
                st.markdown("**⚠️ " + ("أخطاء شائعة / Common Mistakes" if ar else "Common Mistakes") + ":**")
                for mistake in drill["common_mistakes"]:
                    st.markdown(f"• {mistake}")
            with col_d:
                st.markdown("**📈 " + ("التطور / Progressions" if ar else "Progressions") + ":**")
                for prog in drill["progressions"]:
                    st.markdown(f"• {prog}")


# ---------------------------------------------------------------------------
# Tab 5: ISU Judges Guidelines
# ---------------------------------------------------------------------------

def _tab_isu_guidelines(ar):
    title = "دليل الحكام ISU" if ar else "ISU Judges' Guidelines"
    st.header(f"📖 {title}")

    subtabs = st.tabs([
        "⭐ " + ("معايير GOE" if ar else "GOE Criteria"),
        "💰 " + ("قيم العناصر" if ar else "Base Values"),
        "🎯 " + ("حاسبة البرنامج" if ar else "Program Calculator"),
        "📅 " + ("تخطيط الموسم" if ar else "Season Planning"),
    ])

    with subtabs[0]:
        st.subheader("⭐ " + ("معايير GOE (من -5 إلى +5)" if ar else "GOE Criteria (-5 to +5)"))

        st.markdown("### 🏒 " + ("القفزات — GOE إيجابي / Jumps — Positive GOE"))
        jump_pos = [
            "Clear 3-turn entry / difficult entry (spread eagle, Ina Bauer, outside spread eagle)",
            "Good flow out of the jump — continuous skating immediately after landing",
            "Varied position in the air / delay of rotation (especially valued in men's quads)",
            "Good speed into the jump — not timid or slowed approach",
            "Good height AND distance — horizontal as well as vertical",
            "Perfect landing — immediate strong flow out of landing edge",
            "Strong and effortless execution — looks easy, no visible struggle",
        ]
        for item in jump_pos:
            st.markdown(f"✅ {item}")

        st.markdown("### 🚫 " + ("القفزات — GOE سلبي / Jumps — Negative GOE"))
        jump_neg_data = [
            {"Issue": "Under-rotation < 1/4 turn", "GOE Impact": "-1 to -2"},
            {"Issue": "Under-rotation 1/4 to 1/2 turn", "GOE Impact": "-2 to -4"},
            {"Issue": "Under-rotation > 1/2 turn (downgraded < )", "GOE Impact": "-3 to -5"},
            {"Issue": "Fall on jump", "GOE Impact": "-5 (maximum)"},
            {"Issue": "Two-foot landing", "GOE Impact": "-2 to -4"},
            {"Issue": "Hand(s) down on landing", "GOE Impact": "-1 to -3"},
            {"Issue": "Step out on landing", "GOE Impact": "-2 to -4"},
            {"Issue": "Pre-rotation on takeoff", "GOE Impact": "-1 to -3"},
            {"Issue": "Flutz (wrong Lutz edge)", "GOE Impact": "e notation + -1 to -3"},
            {"Issue": "Lip (wrong Flip edge)", "GOE Impact": "e notation + -1 to -3"},
            {"Issue": "Unclear take-off", "GOE Impact": "-1 to -2"},
            {"Issue": "Stumble on entry or after landing", "GOE Impact": "-1 to -2"},
        ]
        st.dataframe(pd.DataFrame(jump_neg_data), use_container_width=True, hide_index=True)

        st.markdown("### 🌀 " + ("الدوران — معايير GOE / Spins — GOE Criteria"))
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**✅ إيجابي / Positive:**")
            spin_pos = [
                "Excellent centering throughout",
                "Beautiful position(s) clearly achieved",
                "Strong, controlled entrance",
                "Great speed maintained to end",
                "Creative or unexpected position",
                "Smooth transition between positions",
            ]
            for s in spin_pos:
                st.markdown(f"• {s}")
        with col2:
            st.markdown("**❌ سلبي / Negative:**")
            spin_neg = [
                "Traveling across the ice",
                "Visible deceleration",
                "Unstable entry with steps",
                "Poor position quality",
                "Not completing minimum rotations in a position",
                "Change of foot not clean",
            ]
            for s in spin_neg:
                st.markdown(f"• {s}")

        st.markdown("### 🎭 " + ("PCS — مكونات البرنامج / Program Component Scores"))
        pcs_components = [
            {
                "Component": "Skating Skills / مهارات التزلج",
                "Max": "10.00",
                "Key Criteria": "Edge quality, power, speed, multi-directional skating, balance, flow, use of blade"
            },
            {
                "Component": "Transitions / الانتقالات",
                "Max": "10.00",
                "Key Criteria": "Variety of turns, steps, linking movements between elements, difficulty and creativity"
            },
            {
                "Component": "Performance / الأداء",
                "Max": "10.00",
                "Key Criteria": "Physical and emotional involvement, projection, relationship with music, commitment"
            },
            {
                "Component": "Composition / التأليف",
                "Max": "10.00",
                "Key Criteria": "Purposeful use of space, pattern, phrasing, ice coverage, balance of program"
            },
            {
                "Component": "Interpretation / التفسير",
                "Max": "10.00",
                "Key Criteria": "Use of music, timing of movements to music, effortless quality, musical sensitivity"
            },
        ]
        st.dataframe(pd.DataFrame(pcs_components), use_container_width=True, hide_index=True)
        st.info("📌 PCS is scored in 0.25 increments. In Senior competitions, each component has a multiplier applied (×1.0 for SP, ×2.0 for FS in most disciplines).")

    with subtabs[1]:
        st.subheader("💰 " + ("قيم الأساس ISU 2024 / ISU 2024 Base Values"))

        bv_data = [
            {"Element": "1A", "BV": "1.10", "With +REP (×1.5)": "—"},
            {"Element": "2A", "BV": "3.30", "With +REP (×1.5)": "4.95"},
            {"Element": "3A", "BV": "8.00", "With +REP (×1.5)": "12.00"},
            {"Element": "4A", "BV": "12.50", "With +REP (×1.5)": "18.75"},
            {"Element": "1Lo", "BV": "0.50", "With +REP (×1.5)": "—"},
            {"Element": "2Lo", "BV": "1.70", "With +REP (×1.5)": "2.55"},
            {"Element": "3Lo", "BV": "4.90", "With +REP (×1.5)": "7.35"},
            {"Element": "4Lo", "BV": "9.80", "With +REP (×1.5)": "14.70"},
            {"Element": "1F", "BV": "0.50", "With +REP (×1.5)": "—"},
            {"Element": "2F", "BV": "1.80", "With +REP (×1.5)": "2.70"},
            {"Element": "3F", "BV": "5.30", "With +REP (×1.5)": "7.95"},
            {"Element": "4F", "BV": "11.00", "With +REP (×1.5)": "16.50"},
            {"Element": "1Lz", "BV": "0.60", "With +REP (×1.5)": "—"},
            {"Element": "2Lz", "BV": "2.10", "With +REP (×1.5)": "3.15"},
            {"Element": "3Lz", "BV": "5.90", "With +REP (×1.5)": "8.85"},
            {"Element": "4Lz", "BV": "11.50", "With +REP (×1.5)": "17.25"},
            {"Element": "1S", "BV": "0.40", "With +REP (×1.5)": "—"},
            {"Element": "2S", "BV": "1.30", "With +REP (×1.5)": "1.95"},
            {"Element": "3S", "BV": "4.30", "With +REP (×1.5)": "6.45"},
            {"Element": "4S", "BV": "9.70", "With +REP (×1.5)": "14.55"},
            {"Element": "1T", "BV": "0.40", "With +REP (×1.5)": "—"},
            {"Element": "2T", "BV": "1.30", "With +REP (×1.5)": "1.95"},
            {"Element": "3T", "BV": "4.20", "With +REP (×1.5)": "6.30"},
            {"Element": "4T", "BV": "9.50", "With +REP (×1.5)": "14.25"},
            {"Element": "CCoSp4", "BV": "3.50", "With +REP (×1.5)": "—"},
            {"Element": "CSp4", "BV": "2.60", "With +REP (×1.5)": "—"},
            {"Element": "CSSp4", "BV": "3.00", "With +REP (×1.5)": "—"},
            {"Element": "FCCoSp4", "BV": "3.50", "With +REP (×1.5)": "—"},
            {"Element": "FSSp4", "BV": "3.00", "With +REP (×1.5)": "—"},
            {"Element": "StSq4", "BV": "3.90", "With +REP (×1.5)": "—"},
            {"Element": "ChSq1", "BV": "3.00", "With +REP (×1.5)": "—"},
        ]
        st.dataframe(pd.DataFrame(bv_data), use_container_width=True, hide_index=True)
        st.info("📌 +REP bonus applies when a jump is repeated (once per type allowed). The repeated jump must be in a combination or sequence.")

    with subtabs[2]:
        st.subheader("🎯 " + ("حاسبة برنامج المنافسة" if ar else "Competition Program Calculator"))

        col1, col2 = st.columns(2)
        with col1:
            discipline = st.selectbox(
                "الانضباط / Discipline",
                ["Senior Men", "Senior Ladies", "Junior Men", "Junior Ladies"]
            )
        with col2:
            program_type = st.selectbox("نوع البرنامج / Program Type", ["Short Program (SP)", "Free Skate (FS)"])

        is_sp = "Short" in program_type

        if is_sp:
            st.markdown("### 📋 " + ("مخطط البرنامج القصير" if ar else "Short Program Layout"))
            sp_rules = {
                "Senior Men": [
                    "1 Jump Combination: Any two or three jumps (e.g., 4T+3T, 3A+3T)",
                    "1 Solo Jump: One of 3A, 4T, 4S, 4Lo, 4F, 4Lz (must be Axel or 4-revolution)",
                    "1 Solo Jump: Any double or triple (cannot be same type as combo jump)",
                    "1 Spin: Flying spin (FCCoSp or equivalent)",
                    "1 Spin: Spin with only one position",
                    "1 Spin: Combination spin (CCoSp)",
                    "1 Step Sequence (StSq)",
                ],
                "Senior Ladies": [
                    "1 Jump Combination: Any two or three jumps",
                    "1 Solo Axel (1A, 2A, or 3A)",
                    "1 Solo Jump: Any double or triple",
                    "1 Spin: Flying spin",
                    "1 Spin: Spin with only one position",
                    "1 Spin: Combination spin",
                    "1 Step Sequence (StSq)",
                ],
                "Junior Men": [
                    "1 Jump Combination: Any two or three jumps",
                    "1 Solo Axel",
                    "1 Solo Jump: Any double or triple",
                    "1 Spin: Flying spin",
                    "1 Spin: One-position spin",
                    "1 Spin: Combination spin",
                    "1 Step Sequence",
                ],
                "Junior Ladies": [
                    "1 Jump Combination: Any two or three jumps (max 3 triples)",
                    "1 Solo Axel",
                    "1 Solo Jump: Any double or triple",
                    "1 Spin: Flying spin",
                    "1 Spin: One-position spin",
                    "1 Spin: Combination spin",
                    "1 Step Sequence",
                ],
            }
            for rule in sp_rules.get(discipline, []):
                st.markdown(f"• {rule}")

        else:
            st.markdown("### 📋 " + ("مخطط البرنامج الحر" if ar else "Free Skate Layout"))
            fs_limits = {
                "Senior Men": {"jumps": 8, "spins": 3, "step_seq": 1, "choro_seq": 1, "note": "Max 3 quads; max 3 jump combos/sequences"},
                "Senior Ladies": {"jumps": 7, "spins": 3, "step_seq": 1, "choro_seq": 1, "note": "Max 3 triples/quads; max 3 jump combos/sequences"},
                "Junior Men": {"jumps": 7, "spins": 3, "step_seq": 1, "choro_seq": 1, "note": "Max 3 quads"},
                "Junior Ladies": {"jumps": 7, "spins": 3, "step_seq": 1, "choro_seq": 1, "note": "Max 3 jump combos"},
            }
            limits = fs_limits.get(discipline, {})
            if limits:
                col_l1, col_l2, col_l3, col_l4 = st.columns(4)
                col_l1.metric("Max Jumps", limits["jumps"])
                col_l2.metric("Spins", limits["spins"])
                col_l3.metric("StSq", limits["step_seq"])
                col_l4.metric("ChSq", limits["choro_seq"])
                st.info(f"📌 {limits['note']}")

        st.markdown("---")
        st.markdown("### 💰 " + ("احسب أقصى TES ممكن / Calculate Maximum TES"))

        bv_lookup = {
            "4A": 12.50, "3A": 8.00, "2A": 3.30,
            "4Lz": 11.50, "3Lz": 5.90, "2Lz": 2.10,
            "4F": 11.00, "3F": 5.30, "2F": 1.80,
            "4Lo": 9.80, "3Lo": 4.90, "2Lo": 1.70,
            "4S": 9.70, "3S": 4.30, "2S": 1.30,
            "4T": 9.50, "3T": 4.20, "2T": 1.30,
            "CCoSp4": 3.50, "CSp4": 2.60, "CSSp4": 3.00, "FCCoSp4": 3.50, "FSSp4": 3.00,
            "StSq4": 3.90, "ChSq1": 3.00,
        }

        available_jumps = st.multiselect(
            "اختر قفزاتك / Select Your Jumps",
            list(bv_lookup.keys()),
            default=["3A", "3Lz", "3F", "3Lo", "3S", "3T", "2A"],
        )

        second_half = st.multiselect(
            "قفزات في النصف الثاني (+10%) / Second Half Jumps (+10%)",
            available_jumps,
        )

        if available_jumps:
            total_tes = 0
            calc_rows = []
            for elem in available_jumps:
                bv = bv_lookup.get(elem, 0)
                bonus = 1.10 if elem in second_half else 1.00
                effective_bv = round(bv * bonus, 2)
                total_tes += effective_bv
                calc_rows.append({
                    "العنصر / Element": elem,
                    "BV": bv,
                    "Bonus": "10%" if bonus > 1 else "—",
                    "Effective BV": effective_bv,
                })

            st.dataframe(pd.DataFrame(calc_rows), use_container_width=True, hide_index=True)

            # Add spin values
            spin_total = 3.50 + 3.00 + 3.50  # CCoSp4 + CSSp4 + FCCoSp4
            step_total = 3.90 + 3.00  # StSq4 + ChSq1
            jump_total = total_tes
            grand_total = jump_total + spin_total + step_total

            col_t1, col_t2, col_t3, col_t4 = st.columns(4)
            col_t1.metric("Jump TES", f"{jump_total:.2f}")
            col_t2.metric("Spin TES (Level 4)", f"{spin_total:.2f}")
            col_t3.metric("Steps TES", f"{step_total:.2f}")
            col_t4.metric("Total TES (BV only)", f"{grand_total:.2f}")

            st.success(f"✅ Estimated Max TES (BV only, no GOE): **{grand_total:.2f}**")
            st.info(f"🏆 With avg +1.5 GOE per element: ~{grand_total + len(available_jumps)*1.5:.1f} | With avg +3.0 GOE: ~{grand_total + len(available_jumps)*3.0:.1f}")

    with subtabs[3]:
        st.subheader("📅 " + ("تخطيط الموسم" if ar else "Season Planning"))

        season_data = [
            {
                "Phase": "July–August / يوليو-أغسطس",
                "Name": "Base Conditioning / التأهيل الأساسي",
                "On-Ice Focus": "Edges, spins, basic jump consistency",
                "Off-Ice Focus": "Heavy strength + plyometrics training",
                "Elements to Train": "Master all existing elements clean",
                "Competition Goal": "No competitions — build the foundation",
                "Intensity": "Medium",
            },
            {
                "Phase": "September–October / سبتمبر-أكتوبر",
                "Name": "Technical Building / البناء التقني",
                "On-Ice Focus": "New elements: new quads or triples, new spin positions",
                "Off-Ice Focus": "Power maintenance + rotation training",
                "Elements to Train": "Add next quad or next triple — harness work",
                "Competition Goal": "Early season B-events for practice",
                "Intensity": "High",
            },
            {
                "Phase": "November–December / نوفمبر-ديسمبر",
                "Name": "Competition Preparation / التحضير للمنافسة",
                "On-Ice Focus": "Full programs, GOE quality, PCS refinement",
                "Off-Ice Focus": "Maintenance only — preserve what was built",
                "Elements to Train": "Solidify all program elements",
                "Competition Goal": "Grand Prix events, National Championships",
                "Intensity": "Very High",
            },
            {
                "Phase": "January–February / يناير-فبراير",
                "Name": "Competition Peak / ذروة المنافسة",
                "On-Ice Focus": "Competition simulation, mental preparation",
                "Off-Ice Focus": "Recovery and flexibility priority",
                "Elements to Train": "Maintenance only — compete, do not train",
                "Competition Goal": "European/Four Continents Championships",
                "Intensity": "Maximum",
            },
            {
                "Phase": "March–April / مارس-أبريل",
                "Name": "Worlds Preparation + Recovery / التحضير للعالمية",
                "On-Ice Focus": "Fine-tuning, GOE maximization on all elements",
                "Off-Ice Focus": "Active recovery — yoga, swimming, light gym",
                "Elements to Train": "Perfect each element — no new elements",
                "Competition Goal": "ISU World Championships — peak performance",
                "Intensity": "Peak then Taper",
            },
        ]
        season_df = pd.DataFrame(season_data)
        st.dataframe(season_df, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.markdown("### 📊 " + ("رسم بياني لشدة الموسم / Season Intensity Chart"))
        months = ["Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar", "Apr"]
        intensity_vals = [60, 65, 80, 85, 90, 95, 98, 100, 95, 80]
        fig_season = go.Figure()
        fig_season.add_trace(go.Scatter(
            x=months,
            y=intensity_vals,
            mode="lines+markers",
            line=dict(color="#ffd60a", width=3),
            marker=dict(size=10, color="#00b4d8"),
            fill="tozeroy",
            fillcolor="rgba(0,180,216,0.2)",
            name="Training Intensity",
        ))
        fig_season.update_layout(
            title="Season Periodization — Training Intensity",
            xaxis_title="Month",
            yaxis_title="Intensity (%)",
            yaxis_range=[0, 110],
            paper_bgcolor="#0e1117",
            plot_bgcolor="#1e2130",
            font_color="white",
            height=300,
        )
        st.plotly_chart(fig_season, use_container_width=True)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def show_elite_coach_page(lang="ar"):
    ar = lang == "ar"

    title = "وحدة المدرب النخبة" if ar else "Elite Coaching Module"
    subtitle = "نظام تدريب متكامل للوصول إلى البطولة العالمية" if ar else "Complete training system to reach World Championship level"

    st.title(f"🏆 {title}")
    st.caption(subtitle)

    tab_labels = [
        "🧠 " + ("تحليل الأداء" if ar else "Performance Analysis"),
        "🏒 " + ("التدريب على الجليد" if ar else "On-Ice Training"),
        "💪 " + ("التدريب خارج الجليد" if ar else "Off-Ice Conditioning"),
        "📋 " + ("مكتبة التمارين" if ar else "Drill Library"),
        "📖 " + ("دليل الحكام ISU" if ar else "ISU Judges' Guide"),
    ]

    tabs = st.tabs(tab_labels)

    with tabs[0]:
        _tab_performance_analysis(ar)
    with tabs[1]:
        _tab_on_ice_training(ar)
    with tabs[2]:
        _tab_off_ice_conditioning(ar)
    with tabs[3]:
        _tab_drill_library(ar)
    with tabs[4]:
        _tab_isu_guidelines(ar)


if __name__ == "__main__":
    st.set_page_config(page_title="Elite Coach Module", layout="wide")
    show_elite_coach_page(lang="ar")
