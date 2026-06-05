"""
محسّن البرنامج التنافسي - Program Optimizer
بناء برنامج المنافسة وتحليل الفجوة مع بطل العالم
"""
import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

DB_PATH = "skating_database.db"


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

JUMP_BASE_VALUES = {
    "4A": 12.50, "3A": 8.00, "2A": 3.30, "1A": 1.10,
    "4Lz": 11.50, "3Lz": 5.90, "2Lz": 2.10, "1Lz": 0.60,
    "4F": 11.00, "3F": 5.30, "2F": 1.80, "1F": 0.50,
    "4Lo": 9.80, "3Lo": 4.90, "2Lo": 1.70, "1Lo": 0.50,
    "4S": 9.70, "3S": 4.30, "2S": 1.30, "1S": 0.40,
    "4T": 9.50, "3T": 4.20, "2T": 1.30, "1T": 0.40,
}

SPIN_BASE_VALUES = {
    "CCoSp4": 3.50, "CCoSp3": 3.00, "CCoSp2": 2.50, "CCoSp1": 2.00,
    "CSp4": 2.60, "CSp3": 2.30, "CSp2": 1.80, "CSp1": 1.40,
    "CSSp4": 3.00, "CSSp3": 2.60, "CSSp2": 2.30, "CSSp1": 1.70,
    "FCCoSp4": 3.50, "FCCoSp3": 3.00, "FCCoSp2": 2.50, "FCCoSp1": 2.00,
    "FSSp4": 3.00, "FSSp3": 2.60, "FSSp2": 2.30, "FSSp1": 1.70,
    "FCSp4": 3.20, "FCSp3": 2.80, "FCSp2": 2.30, "FCSp1": 1.90,
    "SSp4": 2.70, "SSp3": 2.10, "SSp2": 1.80, "SSp1": 1.50,
    "LSp4": 2.70, "LSp3": 2.40, "LSp2": 1.90, "LSp1": 1.50,
    "USp4": 3.00, "USp3": 2.50, "USp2": 2.00, "USp1": 1.20,
}

STEP_BASE_VALUES = {
    "StSq4": 3.90, "StSq3": 3.30, "StSq2": 2.60, "StSq1": 1.80,
    "ChSq1": 3.00,
}

WORLD_CHAMPION_BENCHMARKS = {
    "Senior Men": {
        "TES_SP": 57.0, "PCS_SP": 48.0, "Total_SP": 105.0,
        "TES_FS": 115.0, "PCS_FS": 100.0, "Total_FS": 215.0,
        "Combined": 320.0,
        "description": "Nathan Chen, Yuzuru Hanyu, Ilia Malinin level",
    },
    "Senior Ladies": {
        "TES_SP": 42.0, "PCS_SP": 40.0, "Total_SP": 82.0,
        "TES_FS": 88.0, "PCS_FS": 80.0, "Total_FS": 168.0,
        "Combined": 250.0,
        "description": "Kaori Sakamoto, Alysa Liu level",
    },
    "Junior Men": {
        "TES_SP": 42.0, "PCS_SP": 36.0, "Total_SP": 78.0,
        "TES_FS": 82.0, "PCS_FS": 68.0, "Total_FS": 150.0,
        "Combined": 228.0,
        "description": "ISU Junior Grand Prix Final champion level",
    },
    "Junior Ladies": {
        "TES_SP": 36.0, "PCS_SP": 32.0, "Total_SP": 68.0,
        "TES_FS": 74.0, "PCS_FS": 62.0, "Total_FS": 136.0,
        "Combined": 204.0,
        "description": "ISU Junior Grand Prix Final champion level",
    },
}

FS_LIMITS = {
    "Senior Men": {"jumps": 8, "spins": 3, "step_seq": 1, "choro_seq": 1, "max_quads": 3, "max_combos": 3},
    "Senior Ladies": {"jumps": 7, "spins": 3, "step_seq": 1, "choro_seq": 1, "max_quads": 2, "max_combos": 3},
    "Junior Men": {"jumps": 7, "spins": 3, "step_seq": 1, "choro_seq": 1, "max_quads": 3, "max_combos": 3},
    "Junior Ladies": {"jumps": 7, "spins": 3, "step_seq": 1, "choro_seq": 1, "max_quads": 0, "max_combos": 3},
}

SP_REQUIREMENTS = {
    "Senior Men": {
        "elements": [
            "Jump combination (any two or three jumps)",
            "Solo jump — Axel or quad (must be different from combo)",
            "Solo jump — any double or triple",
            "Flying spin (FCCoSp or similar)",
            "One-position spin",
            "Combination spin (CCoSp4)",
            "Step sequence (StSq)",
        ]
    },
    "Senior Ladies": {
        "elements": [
            "Jump combination (any two or three jumps)",
            "Solo Axel (1A, 2A, or 3A)",
            "Solo jump (any double or triple)",
            "Flying spin",
            "One-position spin",
            "Combination spin",
            "Step sequence",
        ]
    },
    "Junior Men": {
        "elements": [
            "Jump combination",
            "Solo Axel",
            "Solo jump (max triple)",
            "Flying spin",
            "One-position spin",
            "Combination spin",
            "Step sequence",
        ]
    },
    "Junior Ladies": {
        "elements": [
            "Jump combination",
            "Solo Axel",
            "Solo jump (max triple)",
            "Flying spin",
            "One-position spin",
            "Combination spin",
            "Step sequence",
        ]
    },
}


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _calculate_tes(jumps_selected, spins_selected, steps_selected, second_half_jumps):
    jump_total = 0.0
    for j in jumps_selected:
        bv = JUMP_BASE_VALUES.get(j, 0)
        if j in second_half_jumps:
            bv *= 1.10
        jump_total += bv

    spin_total = sum(SPIN_BASE_VALUES.get(s, 0) for s in spins_selected)
    step_total = sum(STEP_BASE_VALUES.get(s, 0) for s in steps_selected)
    return round(jump_total, 2), round(spin_total, 2), round(step_total, 2)


def _optimal_second_half(jumps_list):
    """Returns the jumps that should go in the second half to maximize TES (highest BV jumps)."""
    sorted_jumps = sorted(jumps_list, key=lambda j: JUMP_BASE_VALUES.get(j, 0), reverse=True)
    half = max(1, len(sorted_jumps) // 2)
    return sorted_jumps[:half]


# ---------------------------------------------------------------------------
# Tab 1: Program Builder
# ---------------------------------------------------------------------------

def _tab_program_builder(ar):
    title = "بناء البرنامج" if ar else "Program Builder"
    st.header(f"🏗️ {title}")

    col1, col2 = st.columns([1, 2])

    with col1:
        discipline = st.selectbox(
            "الانضباط / Discipline",
            ["Senior Men", "Senior Ladies", "Junior Men", "Junior Ladies"],
            key="pb_discipline",
        )
        program_type = st.selectbox(
            "نوع البرنامج / Program",
            ["Free Skate (FS)", "Short Program (SP)"],
            key="pb_program",
        )
        is_fs = "Free" in program_type
        limits = FS_LIMITS.get(discipline, {})

    with col2:
        if not is_fs:
            st.subheader("📋 " + ("متطلبات البرنامج القصير" if ar else "SP Requirements"))
            reqs = SP_REQUIREMENTS.get(discipline, {})
            for elem in reqs.get("elements", []):
                st.markdown(f"• {elem}")
        else:
            st.subheader("📋 " + ("حدود البرنامج الحر" if ar else "FS Limits"))
            if limits:
                colA, colB, colC, colD = st.columns(4)
                colA.metric("Max Jumps", limits["jumps"])
                colB.metric("Max Quads", limits["max_quads"])
                colC.metric("Spins", limits["spins"])
                colD.metric("Max Combos", limits["max_combos"])

    st.markdown("---")

    col_j, col_s, col_st = st.columns(3)

    quad_jumps = ["4A", "4Lz", "4F", "4Lo", "4S", "4T"]
    triple_jumps = ["3A", "3Lz", "3F", "3Lo", "3S", "3T"]
    double_jumps = ["2A", "2Lz", "2F", "2Lo", "2S", "2T"]
    all_jumps = quad_jumps + triple_jumps + double_jumps

    with col_j:
        st.subheader("🏒 " + ("القفزات المتاحة / Available Jumps"))
        st.caption("اختر القفزات التي يمكن للمتزلج أداؤها / Select jumps the skater can perform")

        selected_quads = st.multiselect("Quad Jumps / رباعيات", quad_jumps, key="pb_quads")
        selected_triples = st.multiselect("Triple Jumps / ثلاثيات", triple_jumps,
                                          default=["3A", "3Lz", "3F", "3Lo", "3S", "3T"], key="pb_triples")
        selected_doubles = st.multiselect("Double Jumps / مضاعفات", double_jumps, default=["2A"], key="pb_doubles")

    with col_s:
        st.subheader("🌀 " + ("الدوران / Spins"))
        flying_spin = st.selectbox("Flying Spin", ["FCCoSp4", "FSSp4", "FCSp4", "FCCoSp3"], key="pb_fly")
        one_pos_spin = st.selectbox("One-Position Spin", ["CSSp4", "CSp4", "SSp4", "LSp4", "CSSp3"], key="pb_one")
        combo_spin = st.selectbox("Combination Spin", ["CCoSp4", "FCCoSp4", "CCoSp3"], key="pb_combo")

    with col_st:
        st.subheader("👣 " + ("الخطوات / Steps"))
        step_seq = st.selectbox("Step Sequence / تسلسل الخطوات", ["StSq4", "StSq3", "StSq2", "StSq1"], key="pb_stseq")
        include_chsq = st.checkbox("Include ChSq1 (Choreographic Sequence)", value=True, key="pb_chsq")

    all_available = selected_quads + selected_triples + selected_doubles

    if all_available:
        max_jumps = limits.get("jumps", 8) if is_fs else 3
        selected_for_program = all_available[:max_jumps]

        opt_second_half = _optimal_second_half(selected_for_program)

        st.markdown("---")
        st.subheader("🗓️ " + ("ترتيب البرنامج الأمثل / Optimal Program Layout"))

        first_half = [j for j in selected_for_program if j not in opt_second_half]
        second_half_actual = [j for j in selected_for_program if j in opt_second_half]

        prog_col1, prog_col2 = st.columns(2)
        with prog_col1:
            st.markdown("**🥇 " + ("النصف الأول / First Half" if ar else "First Half") + ":**")
            for i, jump in enumerate(first_half, 1):
                bv = JUMP_BASE_VALUES.get(jump, 0)
                st.markdown(f"  {i}. `{jump}` — BV: {bv}")

        with prog_col2:
            st.markdown("**🥇 " + ("النصف الثاني (+10%) / Second Half (+10%)" if ar else "Second Half (+10%)") + ":**")
            for i, jump in enumerate(second_half_actual, len(first_half) + 1):
                bv = JUMP_BASE_VALUES.get(jump, 0)
                bv_bonus = round(bv * 1.10, 2)
                st.markdown(f"  {i}. `{jump}` — BV: {bv} → **{bv_bonus}** (+10%)")

        spins_list = [flying_spin, one_pos_spin, combo_spin]
        steps_list = [step_seq]
        if include_chsq:
            steps_list.append("ChSq1")

        jump_tes, spin_tes, step_tes = _calculate_tes(
            selected_for_program,
            spins_list,
            steps_list,
            opt_second_half,
        )
        total_tes = jump_tes + spin_tes + step_tes

        st.markdown("---")
        st.subheader("💰 " + ("نتيجة TES المقدرة / Estimated TES Score"))

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Jump TES (BV)", f"{jump_tes:.2f}")
        c2.metric("Spin TES", f"{spin_tes:.2f}")
        c3.metric("Steps TES", f"{step_tes:.2f}")
        c4.metric("Total TES (BV)", f"{total_tes:.2f}")

        goe_avg_realistic = 1.5
        with_goe = round(total_tes + len(selected_for_program) * goe_avg_realistic, 2)
        wc_bench = WORLD_CHAMPION_BENCHMARKS.get(discipline, {})
        wc_tes = wc_bench.get("TES_FS" if is_fs else "TES_SP", 100)
        gap = round(wc_tes - total_tes, 2)

        col_info1, col_info2 = st.columns(2)
        with col_info1:
            st.info(f"📊 With avg +1.5 GOE per element: ~**{with_goe:.1f}**")
        with col_info2:
            if gap > 0:
                st.warning(f"📉 Gap to World Champion TES ({discipline}): **{gap:.1f} points**")
            else:
                st.success(f"🏆 World Champion TES level achieved!")

        # Bar chart
        fig_bar = go.Figure(go.Bar(
            x=["Jump TES", "Spin TES", "Steps TES"],
            y=[jump_tes, spin_tes, step_tes],
            marker_color=["#00b4d8", "#ffd60a", "#06d6a0"],
            text=[f"{v:.2f}" for v in [jump_tes, spin_tes, step_tes]],
            textposition="outside",
        ))
        fig_bar.update_layout(
            title="TES Breakdown",
            yaxis_title="Base Value",
            paper_bgcolor="#0e1117",
            plot_bgcolor="#1e2130",
            font_color="white",
            height=300,
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    else:
        st.info("👆 " + ("اختر قفزات المتزلج لبدء البناء." if ar else "Select the skater's available jumps to start building."))


# ---------------------------------------------------------------------------
# Tab 2: World Champion Comparison
# ---------------------------------------------------------------------------

def _tab_world_champion_comparison(ar):
    title = "مقارنة بالبطل العالمي" if ar else "World Champion Comparison"
    st.header(f"📊 {title}")

    discipline = st.selectbox(
        "الانضباط / Discipline",
        ["Senior Men", "Senior Ladies", "Junior Men", "Junior Ladies"],
        key="wc_discipline",
    )

    bench = WORLD_CHAMPION_BENCHMARKS.get(discipline, {})
    st.caption(f"🏆 World Champion Level Reference: {bench.get('description', '')}")

    # Display benchmarks
    st.subheader("📈 " + ("معايير البطل العالمي / World Champion Benchmarks"))
    bench_cols = st.columns(6)
    bench_cols[0].metric("SP TES", bench.get("TES_SP", "—"))
    bench_cols[1].metric("SP PCS", bench.get("PCS_SP", "—"))
    bench_cols[2].metric("SP Total", bench.get("Total_SP", "—"))
    bench_cols[3].metric("FS TES", bench.get("TES_FS", "—"))
    bench_cols[4].metric("FS PCS", bench.get("PCS_FS", "—"))
    bench_cols[5].metric("FS Total", bench.get("Total_FS", "—"))

    st.markdown("---")
    st.subheader("📝 " + ("أدخل درجات المتزلج الحالية / Enter Skater's Current Scores"))

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**SP Scores:**")
        skater_sp_tes = st.number_input("SP TES", min_value=0.0, max_value=200.0, value=25.0, step=0.5, key="skater_sp_tes")
        skater_sp_pcs = st.number_input("SP PCS", min_value=0.0, max_value=100.0, value=22.0, step=0.5, key="skater_sp_pcs")
    with col2:
        st.markdown("**FS Scores:**")
        skater_fs_tes = st.number_input("FS TES", min_value=0.0, max_value=300.0, value=45.0, step=0.5, key="skater_fs_tes")
        skater_fs_pcs = st.number_input("FS PCS", min_value=0.0, max_value=200.0, value=40.0, step=0.5, key="skater_fs_pcs")

    skater_sp_total = round(skater_sp_tes + skater_sp_pcs, 2)
    skater_fs_total = round(skater_fs_tes + skater_fs_pcs, 2)
    skater_combined = round(skater_sp_total + skater_fs_total, 2)

    st.markdown("---")
    st.subheader("📊 " + ("تحليل الفجوة / Gap Analysis"))

    gap_data = {
        "المقياس / Metric": ["SP TES", "SP PCS", "SP Total", "FS TES", "FS PCS", "FS Total", "Combined Total"],
        "المتزلج / Skater": [skater_sp_tes, skater_sp_pcs, skater_sp_total, skater_fs_tes, skater_fs_pcs, skater_fs_total, skater_combined],
        "البطل العالمي / World Champ": [
            bench.get("TES_SP", 0), bench.get("PCS_SP", 0), bench.get("Total_SP", 0),
            bench.get("TES_FS", 0), bench.get("PCS_FS", 0), bench.get("Total_FS", 0),
            bench.get("Combined", 0),
        ],
    }
    gap_df = pd.DataFrame(gap_data)
    gap_df["الفجوة / Gap"] = gap_df["البطل العالمي / World Champ"] - gap_df["المتزلج / Skater"]
    gap_df["النسبة / %"] = (gap_df["المتزلج / Skater"] / gap_df["البطل العالمي / World Champ"] * 100).round(1)
    st.dataframe(gap_df, use_container_width=True, hide_index=True)

    # Radar chart comparison
    categories = ["SP TES", "SP PCS", "FS TES", "FS PCS"]
    skater_norm = [
        (skater_sp_tes / bench.get("TES_SP", 1)) * 100,
        (skater_sp_pcs / bench.get("PCS_SP", 1)) * 100,
        (skater_fs_tes / bench.get("TES_FS", 1)) * 100,
        (skater_fs_pcs / bench.get("PCS_FS", 1)) * 100,
    ]
    wc_norm = [100, 100, 100, 100]

    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(
        r=skater_norm + [skater_norm[0]],
        theta=categories + [categories[0]],
        fill="toself",
        name="Current Skater",
        line_color="#00b4d8",
        fillcolor="rgba(0,180,216,0.3)",
    ))
    fig_radar.add_trace(go.Scatterpolar(
        r=wc_norm + [wc_norm[0]],
        theta=categories + [categories[0]],
        fill="toself",
        name="World Champion",
        line_color="#ffd60a",
        fillcolor="rgba(255,214,10,0.1)",
    ))
    fig_radar.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 120])),
        title="Skater vs World Champion (Normalized to 100%)",
        paper_bgcolor="#0e1117",
        plot_bgcolor="#0e1117",
        font_color="white",
        height=400,
    )
    st.plotly_chart(fig_radar, use_container_width=True)

    # Road to World Champion timeline
    st.markdown("---")
    st.subheader("🗺️ " + ("طريق إلى البطولة العالمية / Road to World Champion Timeline"))

    combined_gap = bench.get("Combined", 0) - skater_combined
    annual_improvement = max(5, combined_gap * 0.3)

    milestones = []
    current = skater_combined
    for year in range(1, 8):
        current = min(bench.get("Combined", 0), current + annual_improvement)
        level = "Beginner" if current < bench.get("Combined", 0) * 0.5 else \
                "Regional" if current < bench.get("Combined", 0) * 0.7 else \
                "National" if current < bench.get("Combined", 0) * 0.85 else \
                "International" if current < bench.get("Combined", 0) * 0.95 else \
                "World Level"
        milestones.append({
            "Year / السنة": f"Year {year}",
            "Target Score / الدرجة المستهدفة": round(current, 1),
            "Level / المستوى": level,
            "Gap Remaining / الفجوة المتبقية": round(bench.get("Combined", 0) - current, 1),
        })
        if current >= bench.get("Combined", 0):
            break

    milestone_df = pd.DataFrame(milestones)
    st.dataframe(milestone_df, use_container_width=True, hide_index=True)

    # Timeline chart
    if not milestone_df.empty:
        fig_timeline = go.Figure()
        fig_timeline.add_trace(go.Scatter(
            x=milestone_df["Year / السنة"],
            y=milestone_df["Target Score / الدرجة المستهدفة"],
            mode="lines+markers",
            name="Projected Score",
            line=dict(color="#00b4d8", width=3),
            marker=dict(size=10),
        ))
        fig_timeline.add_hline(
            y=bench.get("Combined", 0),
            line_dash="dash",
            line_color="#ffd60a",
            annotation_text="World Champion Level",
            annotation_position="bottom right",
        )
        fig_timeline.add_hline(
            y=skater_combined,
            line_dash="dot",
            line_color="#06d6a0",
            annotation_text="Current Level",
            annotation_position="top right",
        )
        fig_timeline.update_layout(
            title="Projected Score Development Timeline",
            xaxis_title="Development Year",
            yaxis_title="Combined Score",
            paper_bgcolor="#0e1117",
            plot_bgcolor="#1e2130",
            font_color="white",
            height=350,
        )
        st.plotly_chart(fig_timeline, use_container_width=True)


# ---------------------------------------------------------------------------
# Tab 3: Development Goals
# ---------------------------------------------------------------------------

def _tab_development_goals(ar):
    title = "أهداف التطوير" if ar else "Development Goals"
    st.header(f"🎯 {title}")

    col1, col2 = st.columns(2)
    with col1:
        discipline = st.selectbox(
            "الانضباط / Discipline",
            ["Senior Men", "Senior Ladies", "Junior Men", "Junior Ladies"],
            key="dg_discipline",
        )
    with col2:
        current_level_label = st.selectbox(
            "المستوى الحالي / Current Level",
            ["Beginner (<50%)", "Developing (50-70%)", "Regional (70-80%)", "National (80-90%)", "International (90-95%)", "World Level (95%+)"],
        )

    bench = WORLD_CHAMPION_BENCHMARKS.get(discipline, {})

    current_pct_map = {
        "Beginner (<50%)": 0.35,
        "Developing (50-70%)": 0.60,
        "Regional (70-80%)": 0.75,
        "National (80-90%)": 0.85,
        "International (90-95%)": 0.92,
        "World Level (95%+)": 0.97,
    }
    current_pct = current_pct_map.get(current_level_label, 0.60)
    current_combined = round(bench.get("Combined", 200) * current_pct, 1)

    st.info(f"🎯 Current estimated combined score: **{current_combined}** / World Champion: **{bench.get('Combined', '—')}**")

    # Short term goals
    st.markdown("---")
    st.subheader("📅 " + ("أهداف قصيرة المدى (3 أشهر) / Short-Term Goals (3 months)"))

    short_term_goals = _generate_short_term_goals(discipline, current_pct, ar)
    for goal in short_term_goals:
        completed = st.checkbox(f"✅ {goal}", key=f"short_{goal}")
        if completed:
            st.success(f"   ✅ " + ("تم إنجازه!" if ar else "Completed!"))

    # Medium term goals
    st.markdown("---")
    st.subheader("📅 " + ("أهداف متوسطة المدى (6 أشهر) / Medium-Term Goals (6 months)"))

    medium_term_goals = _generate_medium_term_goals(discipline, current_pct, ar)
    for goal in medium_term_goals:
        completed = st.checkbox(f"📈 {goal}", key=f"medium_{goal}")
        if completed:
            st.success(f"   ✅ " + ("تم إنجازه!" if ar else "Completed!"))

    # Long term goals
    st.markdown("---")
    st.subheader("📅 " + ("أهداف طويلة المدى (12 شهر) / Long-Term Goals (12 months)"))

    long_term_goals = _generate_long_term_goals(discipline, current_pct, bench, ar)
    for goal in long_term_goals:
        completed = st.checkbox(f"🏆 {goal}", key=f"long_{goal}")
        if completed:
            st.success(f"   ✅ " + ("تم إنجازه!" if ar else "Completed!"))

    # Progress chart
    st.markdown("---")
    st.subheader("📊 " + ("تتبع التقدم / Progress Tracking"))

    target_3m = round(current_combined * 1.08, 1)
    target_6m = round(current_combined * 1.18, 1)
    target_12m = round(current_combined * 1.30, 1)
    wc_target = bench.get("Combined", 200)

    progress_data = {
        "Milestone": ["Current", "3 Months", "6 Months", "12 Months", "World Champion"],
        "Target Score": [current_combined, target_3m, target_6m, target_12m, wc_target],
        "% of World Champion": [
            round(current_combined / wc_target * 100, 1),
            round(target_3m / wc_target * 100, 1),
            round(target_6m / wc_target * 100, 1),
            round(target_12m / wc_target * 100, 1),
            100.0,
        ],
    }

    progress_df = pd.DataFrame(progress_data)
    st.dataframe(progress_df, use_container_width=True, hide_index=True)

    fig_prog = go.Figure()
    fig_prog.add_trace(go.Bar(
        x=progress_data["Milestone"],
        y=progress_data["% of World Champion"],
        marker_color=["#ef233c", "#f77f00", "#fcbf49", "#06d6a0", "#ffd60a"],
        text=[f"{v}%" for v in progress_data["% of World Champion"]],
        textposition="outside",
    ))
    fig_prog.add_hline(y=100, line_dash="dash", line_color="#ffd60a", annotation_text="World Champion Level")
    fig_prog.update_layout(
        title="Progress Toward World Champion Level",
        yaxis_title="% of World Champion",
        yaxis_range=[0, 120],
        paper_bgcolor="#0e1117",
        plot_bgcolor="#1e2130",
        font_color="white",
        height=350,
    )
    st.plotly_chart(fig_prog, use_container_width=True)

    # Element-specific targets
    st.markdown("---")
    st.subheader("🎿 " + ("أهداف تطوير العناصر / Element Development Targets"))

    elem_targets = _generate_element_targets(discipline, current_pct, ar)
    for phase, elements in elem_targets.items():
        st.markdown(f"**{phase}:**")
        for elem in elements:
            st.markdown(f"  • {elem}")


def _generate_short_term_goals(discipline, current_pct, ar):
    goals_map = {
        "Senior Men": [
            "Consistent 3-turn entry on all Lutz jumps — eliminate Flutz error",
            "Add 3-count landing hold after every triple jump — reduce two-foot landings by 80%",
            "Increase spin RPM by 20% through optimized arm pull-in technique",
            "Step sequence: achieve Level 3 consistently in every practice",
            "Complete 5 clean short program run-throughs in a row without falls",
        ],
        "Senior Ladies": [
            "Fix triple Flip edge — document approach edge in every practice video",
            "Layback spin: achieve 8+ rotations per attempt consistently",
            "Spiral sequence flexibility: reach 180-degree spiral leg position",
            "Clean triple-triple combination in 8 out of 10 attempts",
            "Program component quality: film and self-evaluate PCS elements weekly",
        ],
        "Junior Men": [
            "Consistent double Axel landing — hold 3 seconds after each attempt",
            "Learn triple toe loop — 10 clean landings in a row before moving on",
            "Spin Level 2 → Level 3: add two spin features (change of foot, difficult position)",
            "Step sequence: map out a full serpentine pattern using the whole rink",
            "Complete full Junior SP 5 times in a row cleanly",
        ],
        "Junior Ladies": [
            "Triple Salchow consistency: 90% clean landing rate in practice",
            "Flying camel spin: achieve camel position before landing in 8 out of 10",
            "Ballet: develop pointed toe and extended free leg consistently",
            "Remove all visible stumbles from short program transitions",
            "Film 3 full practice run-throughs and analyze GOE on each element",
        ],
    }
    return goals_map.get(discipline, ["Set specific technical goals with your coach."])


def _generate_medium_term_goals(discipline, current_pct, ar):
    goals_map = {
        "Senior Men": [
            "Add quad toe loop to free skate: harness work → unassisted",
            "Improve average GOE on triple Axel from +1 to +2.5",
            "PCS: achieve 8.0+ on Skating Skills in a regional competition",
            "Step sequence Level 3 → Level 4: add counter and bracket turns",
            "Score 75%+ of World Champion FS TES benchmark in a regional competition",
        ],
        "Senior Ladies": [
            "Triple Lutz + triple toe combination: 80% success rate in practice",
            "Add Biellmann position to combination spin for a level feature",
            "PCS Performance score: 7.5+ from all judges in a local competition",
            "Choreographic sequence: develop artistic expression for the ChSq1",
            "Compete in and complete 3 full competitions with no falls",
        ],
        "Junior Men": [
            "Triple Axel: achieve first clean landing → 70% consistency",
            "Triple Lutz: clean and consistent from correct outside edge",
            "Spin Level 4 on combination spin: all 4 positions with 4 rotations each",
            "Second half of free skate: maintain jump quality when tired — physical conditioning",
            "Represent at a regional Junior competition and achieve positive GOE on spins",
        ],
        "Junior Ladies": [
            "Triple-triple combination: triple toe + triple toe combination clean",
            "Spin combination Level 3: three positions with 3+ rotations each",
            "Artistic development: take 20 ballet classes over the next 6 months",
            "Music interpretation: choreography should be visibly connected to the music",
            "Compete in 3 Junior-level competitions and score PCS above 5.0 per component",
        ],
    }
    return goals_map.get(discipline, ["Develop a 6-month plan with your coach."])


def _generate_long_term_goals(discipline, current_pct, bench, ar):
    wc_combined = bench.get("Combined", 200)
    target_1yr = round(wc_combined * min(0.99, current_pct + 0.15), 1)
    target_tes = round(bench.get("TES_FS", 80) * min(0.99, current_pct + 0.15), 1)
    target_pcs = round(bench.get("PCS_FS", 70) * min(0.99, current_pct + 0.15), 1)

    goals_map = {
        "Senior Men": [
            f"Target combined score of {target_1yr} within 12 months (World Champ: {wc_combined})",
            f"FS TES target: {target_tes} (World Champ benchmark: {bench.get('TES_FS', '—')})",
            f"PCS target: {target_pcs} average per component in FS",
            "Successfully compete at an ISU Grand Prix or Challenger Series event",
            "Land at least one quad jump cleanly in competition",
        ],
        "Senior Ladies": [
            f"Target combined score of {target_1yr} within 12 months",
            "Qualify and compete at National Championship level",
            "Triple-triple combination in competition — no two-foot, no under-rotation",
            "PCS Interpretation score 7.0+ from majority of judges at national level",
            "Full competition season: 5 competitions with improving scores each event",
        ],
        "Junior Men": [
            f"Target combined score of {target_1yr} in Junior competitions",
            "Triple Axel in competition: at least one attempt landed cleanly",
            "Junior Grand Prix qualifier: achieve the minimum TES threshold to compete",
            "Year-end: have all triple jumps in the free skate with 70%+ consistency",
            "Physical benchmark: maintain weight and fitness for the entire season",
        ],
        "Junior Ladies": [
            f"Target combined score of {target_1yr} in Junior competitions",
            "Compete at ISU Junior Grand Prix event — score above regional baseline",
            "All double jumps consistent and clean — foundation for upcoming triple program",
            "Triple Lutz and triple Flip in program at 70%+ clean rate in practice",
            "Ballet and artistry: visibly improve PCS Performance score by +1.0 point year-over-year",
        ],
    }
    return goals_map.get(discipline, ["Set long-term goals with your coach."])


def _generate_element_targets(discipline, current_pct, ar):
    targets = {
        "3 Months — Consistency Focus / التركيز على الاتساق": [
            "All existing doubles: 95% clean rate",
            "Entry edges: correct edge on all Lutz and Flip attempts",
            "Spins: no spin below Level 2 in practice",
        ],
        "6 Months — New Elements / عناصر جديدة": [
            "Add next single triple jump to practice",
            "Add difficult position to combination spin",
            "Level 4 step sequence practiced consistently",
        ],
        "12 Months — Competition Program / برنامج المنافسة": [
            "All program elements consistent at 80%+ clean rate",
            "SP and FS memorized and competition-ready",
            "GOE average on all elements: +1.0 or better",
        ],
    }
    return targets


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def show_program_optimizer(lang="ar"):
    ar = lang == "ar"

    title = "محسّن البرنامج التنافسي" if ar else "Competition Program Optimizer"
    subtitle = "بناء البرنامج المثالي وتحليل الفجوة مع البطل العالمي" if ar else "Build the optimal competition program and analyze the gap to World Champion"

    st.title(f"🏗️ {title}")
    st.caption(subtitle)

    tab_labels = [
        "🏗️ " + ("بناء البرنامج" if ar else "Program Builder"),
        "📊 " + ("مقارنة بالبطل العالمي" if ar else "World Champion Comparison"),
        "🎯 " + ("أهداف التطوير" if ar else "Development Goals"),
    ]

    tabs = st.tabs(tab_labels)

    with tabs[0]:
        _tab_program_builder(ar)
    with tabs[1]:
        _tab_world_champion_comparison(ar)
    with tabs[2]:
        _tab_development_goals(ar)


if __name__ == "__main__":
    st.set_page_config(page_title="Program Optimizer", layout="wide")
    show_program_optimizer(lang="ar")
