"""
╔══════════════════════════════════════════════════════════════════╗
║  RESILIENCE ENABLING CONDITIONS — DIAGNOSTIC TOOL              ║
║  Interactive Dashboard for RtR Partner Survey Analysis          ║
║  Race to Resilience · Climate Resilience Assessment             ║
╚══════════════════════════════════════════════════════════════════╝
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO

# ── Page config ──────────────────────────────────────────────────
st.set_page_config(
    page_title="Resilience Diagnostic Tool",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ───────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&family=JetBrains+Mono:wght@400;500&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.kpi-card {
    background: linear-gradient(135deg, #f8f9fc 0%, #eef1f8 100%);
    border: 1px solid #dde3ee; border-radius: 14px;
    padding: 1.3rem 1.5rem; text-align: center;
    box-shadow: 0 2px 12px rgba(60,70,100,0.06); transition: transform 0.2s;
}
.kpi-card:hover { transform: translateY(-2px); }
.kpi-val { font-family: 'JetBrains Mono', monospace; font-size: 2.1rem; font-weight: 700; margin: 0.2rem 0; }
.kpi-label { font-size: 0.82rem; color: #5a6078; font-weight: 500; letter-spacing: 0.03em; text-transform: uppercase; }
.kpi-sub { font-size: 0.75rem; color: #8892a8; margin-top: 0.15rem; }
.sec-head { font-size: 1.15rem; font-weight: 700; color: #1a1f36; border-left: 4px solid #4e6af0; padding-left: 0.8rem; margin: 1.5rem 0 0.8rem 0; }
.insight-box { background: #f0f4ff; border-left: 4px solid #4e6af0; border-radius: 0 10px 10px 0; padding: 1rem 1.2rem; margin: 0.8rem 0 1.2rem 0; font-size: 0.92rem; color: #1a1f36; line-height: 1.65; }
.insight-box b { color: #4e6af0; }
.warn-box { background: #fff8f0; border-left: 4px solid #e8573a; border-radius: 0 10px 10px 0; padding: 1rem 1.2rem; margin: 0.8rem 0 1.2rem 0; font-size: 0.92rem; color: #1a1f36; line-height: 1.65; }
.warn-box b { color: #e8573a; }
.ok-box { background: #f0faf4; border-left: 4px solid #2ebd6e; border-radius: 0 10px 10px 0; padding: 1rem 1.2rem; margin: 0.8rem 0 1.2rem 0; font-size: 0.92rem; color: #1a1f36; line-height: 1.65; }
.ok-box b { color: #2ebd6e; }
.explain-box { background: #fafafa; border: 1px solid #e8e8e8; border-radius: 10px; padding: 1rem 1.2rem; margin: 0.5rem 0 1rem 0; font-size: 0.88rem; color: #4a5068; line-height: 1.6; }
.q-ref { background: #f8f9fc; border: 1px solid #dde3ee; border-radius: 10px; padding: 1rem 1.2rem; margin: 0.5rem 0; font-size: 0.85rem; color: #4a5068; line-height: 1.55; }
.badge { display: inline-block; padding: 0.2rem 0.65rem; border-radius: 6px; font-size: 0.75rem; font-weight: 600; }
.badge-green { background: #d4edda; color: #155724; }
.badge-red { background: #f8d7da; color: #721c24; }
.badge-yellow { background: #fff3cd; color: #856404; }
.badge-blue { background: #d6e4f0; color: #1a4e79; }
footer { visibility: hidden; }
.stTabs [data-baseweb="tab-list"] { gap: 4px; }
.stTabs [data-baseweb="tab"] { border-radius: 8px 8px 0 0; font-weight: 600; font-size: 0.85rem; }
</style>
""", unsafe_allow_html=True)

# ── Color palette ────────────────────────────────────────────────
COLORS = {"q1": "#4e6af0", "q2": "#e8573a", "q3": "#2ebd6e", "accent": "#7c3aed", "bg": "#f8f9fc"}
CAT_PALETTE = px.colors.qualitative.Set2
TYPE_COLORS = {"Enabler": "#2ebd6e", "Bottleneck": "#e8573a", "Emerging": "#f5a623", "Latent": "#8892a8"}

# ── Scale interpretation helpers ─────────────────────────────────

Q1_SCALE = {
    0: "Don't know / Not applicable",
    1: "Not observed",
    2: "Observed in isolated cases",
    3: "Observed in several member organizations or initiatives",
    4: "Observed across most or all member organizations or initiatives",
}
Q2_SCALE = {
    0: "Don't know / Not applicable",
    1: "Not critical — no impact on success",
    2: "Slightly critical — some impact, not a major determinant",
    3: "Moderately critical — somewhat important, other factors mattered equally",
    4: "Very critical — important role, strongly contributed to success",
    5: "Extremely critical — essential, decisive influence on success",
}
Q3_SCALE = {
    0: "Don't know / Not applicable",
    1: "Not at all — gap remained a major obstacle",
    2: "To a small extent — partially addressed, limited impact",
    3: "To some extent — moderately addressed, mixed results",
    4: "To a large extent — clearly addressed, most members overcame it",
    5: "Completely — fully addressed and effectively overcome",
}


def interpret_q1(val):
    if val >= 3.5: return "widely observed across most member organizations"
    if val >= 2.5: return "observed in several organizations but not uniformly"
    if val >= 1.5: return "observed only in isolated cases"
    return "largely not observed"


def interpret_q2(val):
    if val >= 4.0: return "considered very to extremely critical for implementation success"
    if val >= 3.0: return "considered moderately to very critical"
    if val >= 2.0: return "considered slightly to moderately critical"
    return "considered not critical or of minimal importance"


def interpret_q3(val):
    if val >= 3.5: return "addressed to a large extent or completely"
    if val >= 2.5: return "addressed to some extent with mixed results"
    if val >= 1.5: return "addressed only to a small extent"
    return "largely not addressed — gaps remain as major obstacles"


# ══════════════════════════════════════════════════════════════════
#  DATA LOADING & PROCESSING
# ══════════════════════════════════════════════════════════════════

@st.cache_data
def load_data(file) -> pd.DataFrame:
    df = pd.read_excel(file, sheet_name="DATASET")
    df.columns = df.columns.str.strip()
    for col in ["Q1 Mean", "Q2 Mean", "Q3 Mean"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def compute_metrics(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    d["Gap"] = d["Q2 Mean"] - d["Q1 Mean"]
    d["Resolution Gap"] = d["Q2 Mean"] - d["Q3 Mean"]
    d["System Stress"] = d["Q2 Mean"] - (d["Q1 Mean"] + d["Q3 Mean"]) / 2
    d["Priority Score"] = d["Q2 Mean"] * d["Gap"]
    d["Efficiency"] = np.where(d["Q2 Mean"] != 0, d["Q3 Mean"] / d["Q2 Mean"], np.nan)
    return d


def classify_typology(row, t_high, t_low):
    q1, q2, q3 = row["Q1 Mean"], row["Q2 Mean"], row["Q3 Mean"]
    if q1 >= t_high and q2 >= t_high and q3 >= t_high:
        return "Enabler"
    if q1 < t_low and q2 < t_low:
        return "Latent"
    if q1 < t_low and q2 >= t_high and q3 < t_low:
        return "Bottleneck"
    if q1 < t_low and q2 >= t_low:
        return "Emerging"
    if q2 - q1 > 0.5 and q3 < t_low:
        return "Bottleneck"
    if q1 >= t_high and q3 >= t_high:
        return "Enabler"
    if q2 >= t_low and q3 < t_low:
        return "Emerging"
    return "Latent"


# ══════════════════════════════════════════════════════════════════
#  CHART HELPERS
# ══════════════════════════════════════════════════════════════════

def plotly_defaults(fig, height=460):
    fig.update_layout(
        font=dict(family="DM Sans, sans-serif", size=12),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(248,249,252,1)",
        margin=dict(l=40, r=30, t=50, b=40), height=height,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_xaxes(gridcolor="#eaecf2", zeroline=False)
    fig.update_yaxes(gridcolor="#eaecf2", zeroline=False)
    return fig


def kpi_html(value, label, sublabel="", color="#4e6af0"):
    return f"""<div class="kpi-card"><div class="kpi-label">{label}</div>
    <div class="kpi-val" style="color:{color}">{value}</div>
    <div class="kpi-sub">{sublabel}</div></div>"""


# ══════════════════════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("## 🌍 Resilience Diagnostic")
    st.markdown("---")
    uploaded = st.file_uploader("Upload Excel file", type=["xlsx", "xls"])
    st.markdown("---")
    st.markdown("### ⚙️ Typology Thresholds")
    t_high = st.slider("High threshold", 1.0, 5.0, 3.2, 0.1, help="Values ≥ this → HIGH")
    t_low = st.slider("Low threshold", 1.0, 5.0, 2.8, 0.1, help="Values < this → LOW")
    if t_low >= t_high:
        st.warning("Low threshold should be < High threshold")

# ══════════════════════════════════════════════════════════════════
#  LANDING PAGE
# ══════════════════════════════════════════════════════════════════

if uploaded is None:
    st.markdown("""
    <div style="text-align:center; padding:4rem 2rem;">
        <h1 style="font-size:2.6rem; font-weight:700; color:#1a1f36;">🌍 Resilience Enabling Conditions</h1>
        <h3 style="color:#5a6078; font-weight:400;">Diagnostic Analysis Tool — Race to Resilience</h3>
        <p style="color:#8892a8; max-width:580px; margin:1.5rem auto; line-height:1.7;">
            Upload your survey Excel file using the sidebar to begin. The app reads the <b>DATASET</b> sheet
            and generates interactive analyses across eight diagnostic dimensions to identify strengths,
            gaps, bottlenecks, and priorities in resilience enabling conditions.
        </p>
    </div>""", unsafe_allow_html=True)
    st.stop()

# ── Load & process ───────────────────────────────────────────────
raw_df = load_data(uploaded)
df = compute_metrics(raw_df)

# ── Sidebar dynamic filters ─────────────────────────────────────
with st.sidebar:
    st.markdown("---")
    st.markdown("### 🔍 Filters")
    all_cats = sorted(df["Category"].dropna().unique())
    sel_cats = st.multiselect("Category", all_cats, default=all_cats)
    available_subs = sorted(df.loc[df["Category"].isin(sel_cats), "Sub Categories"].dropna().unique())
    sel_subs = st.multiselect("Sub Categories", available_subs, default=available_subs)

fdf = df[df["Category"].isin(sel_cats) & df["Sub Categories"].isin(sel_subs)].copy()
if fdf.empty:
    st.error("No data matches the selected filters.")
    st.stop()

fdf["Typology"] = fdf.apply(lambda r: classify_typology(r, t_high, t_low), axis=1)

# ══════════════════════════════════════════════════════════════════
#  TABS
# ══════════════════════════════════════════════════════════════════

tabs = st.tabs([
    "🏠 Introduction",
    "📊 Overview",
    "🔻 Gap Analysis",
    "📁 Categories",
    "🧬 Typology",
    "📈 Variability",
    "🎯 Priority & Capacity",
    "🗂 Data Explorer",
    "📖 Glossary & Scales",
])

# ──────────────────────────────────────────────────────────────────
#  TAB 0 — INTRODUCTION
# ──────────────────────────────────────────────────────────────────
with tabs[0]:
    st.markdown("# 🌍 Introduction to this Diagnostic Tool")
    st.markdown("")

    st.markdown("""
    This dashboard analyses data from the **Race to Resilience (RtR) Partner Survey** on enabling conditions
    for climate resilience. RtR Partners were asked to assess — from their experience coordinating
    member organizations — how enabling conditions behave across three complementary dimensions.
    """)

    st.markdown("---")
    st.markdown("### 📋 The Three Survey Questions")

    st.markdown("""
    <div class="q-ref">
    <b style="color:#4e6af0;">Q1 — Observation of Enabling Conditions (Scale 0–4)</b><br>
    <i>"Based on your RtR Partner role, have you observed the following enabling conditions supporting
    the implementation of resilience actions across your network of members?"</i><br><br>
    <b>Scale:</b> 0 = Don't know · 1 = Not observed · 2 = Observed in isolated cases ·
    3 = Observed in several organizations · 4 = Observed across most or all organizations
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="q-ref">
    <b style="color:#e8573a;">Q2 — Critical Importance for Success (Scale 0–5)</b><br>
    <i>"From your experience as a RtR partner, to what extent was this factor critical for the successful
    implementation of actions carried out by your member organizations?"</i><br><br>
    <b>Scale:</b> 0 = Don't know · 1 = Not critical · 2 = Slightly critical ·
    3 = Moderately critical · 4 = Very critical · 5 = Extremely critical
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="q-ref">
    <b style="color:#2ebd6e;">Q3 — Degree of Gap Resolution (Scale 0–5)</b><br>
    <i>"From your experience as a RtR partner, to what extent was this gap or challenge faced by your
    member organizations successfully addressed or overcome during the implementation of their actions?"</i><br><br>
    <b>Scale:</b> 0 = Don't know · 1 = Not at all · 2 = To a small extent ·
    3 = To some extent · 4 = To a large extent · 5 = Completely
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📊 Summary of Results at a Glance")

    avg_q1 = fdf["Q1 Mean"].mean()
    avg_q2 = fdf["Q2 Mean"].mean()
    avg_q3 = fdf["Q3 Mean"].mean()
    avg_gap = fdf["Gap"].mean()
    avg_eff = fdf["Efficiency"].mean()
    n_vars = len(fdf)
    n_cats = fdf["Category"].nunique()
    n_bottle = (fdf["Typology"] == "Bottleneck").sum()
    n_enablers = (fdf["Typology"] == "Enabler").sum()

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.markdown(kpi_html(f"{avg_q1:.2f}", "Q1 Observation", f"of 4 · {interpret_q1(avg_q1)}", COLORS["q1"]), unsafe_allow_html=True)
    k2.markdown(kpi_html(f"{avg_q2:.2f}", "Q2 Criticality", f"of 5 · {interpret_q2(avg_q2)}", COLORS["q2"]), unsafe_allow_html=True)
    k3.markdown(kpi_html(f"{avg_q3:.2f}", "Q3 Resolution", f"of 5 · {interpret_q3(avg_q3)}", COLORS["q3"]), unsafe_allow_html=True)
    k4.markdown(kpi_html(f"{avg_gap:.2f}", "Avg Gap", "Q2 − Q1", COLORS["accent"]), unsafe_allow_html=True)
    k5.markdown(kpi_html(f"{avg_eff:.0%}", "Avg Efficiency", "Q3 / Q2", "#1a1f36"), unsafe_allow_html=True)

    st.markdown("")

    # Auto-generated executive summary
    st.markdown("### 🧠 Automated Executive Interpretation")
    exec_text = f"""
    <div class="insight-box">
    The survey assessed <b>{n_vars} enabling conditions</b> across <b>{n_cats} categories</b>
    (Governance, Financial Conditions, Knowledge & Capacities, and Partnerships & Inclusion).<br><br>

    <b>On average, enabling conditions were {interpret_q1(avg_q1)}</b> (Q1 mean = {avg_q1:.2f} on a 0–4 scale).
    This means that, from the partners' perspective, most conditions are present in several but not all member organizations.<br><br>

    <b>Partners rated these factors as {interpret_q2(avg_q2)}</b> for implementation success
    (Q2 mean = {avg_q2:.2f} on a 0–5 scale). There is a clear perception that enabling conditions
    matter significantly for achieving resilience outcomes.<br><br>

    <b>Regarding gap resolution, challenges were {interpret_q3(avg_q3)}</b>
    (Q3 mean = {avg_q3:.2f} on a 0–5 scale). This suggests that while some progress has been made,
    important gaps remain unresolved.<br><br>

    The average <b>Gap (Q2 − Q1) = {avg_gap:.2f}</b> indicates that criticality consistently exceeds
    observed availability — partners recognize these conditions as more important than currently present.
    The average <b>Efficiency (Q3/Q2) = {avg_eff:.0%}</b> means that, on average, only {avg_eff:.0%}
    of the perceived critical need is being effectively addressed.<br><br>

    The typology analysis identified <b>{n_bottle} bottleneck(s)</b> (high criticality, low availability,
    low resolution) and <b>{n_enablers} enabler(s)</b> (high on all three dimensions).
    </div>
    """
    st.markdown(exec_text, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🗺 How to Navigate This Dashboard")
    st.markdown("""
    <div class="explain-box">
    Each tab provides a different analytical lens on the same data:<br><br>
    <b>📊 Overview</b> — Global averages and category-level radar/bar charts. Start here for the big picture.<br>
    <b>🔻 Gap Analysis</b> — Identifies where criticality exceeds availability. Larger gaps = higher unmet need.<br>
    <b>📁 Categories</b> — Breaks down results by category and sub-category with heatmaps.<br>
    <b>🧬 Typology</b> — Classifies each condition as Enabler, Bottleneck, Emerging, or Latent.<br>
    <b>📈 Variability</b> — Shows where partners disagreed most, signaling contested or context-dependent factors.<br>
    <b>🎯 Priority & Capacity</b> — Ranks conditions by urgency and measures adaptive efficiency.<br>
    <b>🗂 Data Explorer</b> — Full searchable dataset with download options.<br>
    <b>📖 Glossary & Scales</b> — Complete reference for all metrics, scales, and survey questions.
    </div>
    """, unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────
#  TAB 1 — OVERVIEW
# ──────────────────────────────────────────────────────────────────
with tabs[1]:
    st.markdown('<div class="sec-head">Global Averages</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="explain-box">
    <b>What is this?</b> These cards show the overall mean across all assessed enabling conditions for each
    survey dimension. They answer: <i>On average, how observed are enabling conditions (Q1)? How critical
    are they considered (Q2)? And to what extent have gaps been resolved (Q3)?</i><br><br>
    <b>How to read it:</b> Compare Q1, Q2, and Q3 side by side. A large difference between Q2 and Q1 signals
    that conditions are seen as more important than currently available. The Gap (Q2−Q1) quantifies this mismatch.
    Efficiency (Q3/Q2) shows what proportion of the critical need is being addressed.
    </div>
    """, unsafe_allow_html=True)

    avg_q1 = fdf["Q1 Mean"].mean()
    avg_q2 = fdf["Q2 Mean"].mean()
    avg_q3 = fdf["Q3 Mean"].mean()
    avg_gap = fdf["Gap"].mean()
    avg_eff = fdf["Efficiency"].mean()

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.markdown(kpi_html(f"{avg_q1:.2f}", "Q1 Observation", "Scale 0–4", COLORS["q1"]), unsafe_allow_html=True)
    k2.markdown(kpi_html(f"{avg_q2:.2f}", "Q2 Criticality", "Scale 0–5", COLORS["q2"]), unsafe_allow_html=True)
    k3.markdown(kpi_html(f"{avg_q3:.2f}", "Q3 Resolution", "Scale 0–5", COLORS["q3"]), unsafe_allow_html=True)
    k4.markdown(kpi_html(f"{avg_gap:.2f}", "Avg Gap", "Q2 − Q1", COLORS["accent"]), unsafe_allow_html=True)
    k5.markdown(kpi_html(f"{avg_eff:.0%}", "Avg Efficiency", "Q3 / Q2", "#1a1f36"), unsafe_allow_html=True)

    # Auto-interpretation
    st.markdown(f"""
    <div class="insight-box">
    <b>🔍 Interpretation:</b> On average, enabling conditions are <b>{interpret_q1(avg_q1)}</b>
    (Q1 = {avg_q1:.2f}/4). Partners rate them as <b>{interpret_q2(avg_q2)}</b> for success
    (Q2 = {avg_q2:.2f}/5). Gaps have been <b>{interpret_q3(avg_q3)}</b>
    (Q3 = {avg_q3:.2f}/5). The system is currently addressing <b>{avg_eff:.0%}</b> of its critical needs.
    </div>
    """, unsafe_allow_html=True)

    # Radar by Category
    st.markdown('<div class="sec-head">Radar Chart — Category Comparison</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="explain-box">
    <b>What is this?</b> A radar (spider) chart showing the average Q1, Q2, and Q3 for each of the four
    enabling condition categories. Each axis represents one category; each colored polygon represents
    one survey dimension.<br><br>
    <b>How to read it:</b> If the Q2 polygon (red, criticality) extends much further than Q1 (blue, observation),
    it means that category's conditions are seen as critical but insufficiently present. If Q3 (green, resolution)
    is close to Q2, gaps are being well addressed. Look for categories where the polygons diverge most — those
    are the areas with the greatest tension between need and reality.
    </div>
    """, unsafe_allow_html=True)

    cat_avg = fdf.groupby("Category")[["Q1 Mean", "Q2 Mean", "Q3 Mean"]].mean().reset_index()
    fig_radar = go.Figure()
    cats_list = cat_avg["Category"].tolist()
    for col, color, name in [
        ("Q1 Mean", COLORS["q1"], "Q1 — Observation (0–4)"),
        ("Q2 Mean", COLORS["q2"], "Q2 — Criticality (0–5)"),
        ("Q3 Mean", COLORS["q3"], "Q3 — Resolution (0–5)"),
    ]:
        vals = cat_avg[col].tolist()
        vals.append(vals[0])
        fig_radar.add_trace(go.Scatterpolar(
            r=vals, theta=cats_list + [cats_list[0]], name=name,
            line=dict(color=color, width=2.5), fill="toself",
            fillcolor=f"rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},0.08)",
        ))
    fig_radar.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 5], tickfont=dict(size=10)),
                   angularaxis=dict(tickfont=dict(size=10))),
        font=dict(family="DM Sans", size=12),
        margin=dict(l=80, r=80, t=50, b=50), height=480, paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_radar, use_container_width=True)

    # Radar auto-interpretation
    worst_cat = cat_avg.loc[(cat_avg["Q2 Mean"] - cat_avg["Q1 Mean"]).idxmax()]
    best_cat = cat_avg.loc[(cat_avg["Q2 Mean"] - cat_avg["Q1 Mean"]).idxmin()]
    st.markdown(f"""
    <div class="insight-box">
    <b>🔍 Interpretation:</b> The category with the largest gap between criticality and observation is
    <b>{worst_cat['Category']}</b> (Q2−Q1 = {worst_cat['Q2 Mean'] - worst_cat['Q1 Mean']:.2f}), meaning
    these conditions are seen as highly important but less present in practice. The smallest gap is in
    <b>{best_cat['Category']}</b> (Q2−Q1 = {best_cat['Q2 Mean'] - best_cat['Q1 Mean']:.2f}), where
    availability better matches perceived need.
    </div>
    """, unsafe_allow_html=True)

    # Grouped bar
    st.markdown('<div class="sec-head">Category Comparison — Bar Chart</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="explain-box">
    <b>What is this?</b> The same data as the radar but displayed as grouped bars for easier numeric comparison.
    Each category has three bars: blue (Q1, observed), red (Q2, critical), green (Q3, resolved).<br><br>
    <b>How to read it:</b> The gap between the red bar (Q2) and blue bar (Q1) is the unmet need. The green bar
    (Q3) shows how much of that need has been addressed. If the green bar is shorter than the red bar,
    significant gaps remain.
    </div>
    """, unsafe_allow_html=True)

    fig_bar_ov = go.Figure()
    for col, color, name in [
        ("Q1 Mean", COLORS["q1"], "Q1 — Observation"),
        ("Q2 Mean", COLORS["q2"], "Q2 — Criticality"),
        ("Q3 Mean", COLORS["q3"], "Q3 — Resolution"),
    ]:
        fig_bar_ov.add_trace(go.Bar(
            x=cat_avg["Category"], y=cat_avg[col], name=name, marker_color=color,
            text=cat_avg[col].round(2), textposition="outside",
        ))
    fig_bar_ov.update_layout(barmode="group", yaxis=dict(range=[0, 5.5]))
    st.plotly_chart(plotly_defaults(fig_bar_ov), use_container_width=True)


# ──────────────────────────────────────────────────────────────────
#  TAB 2 — GAP ANALYSIS
# ──────────────────────────────────────────────────────────────────
with tabs[2]:
    st.markdown('<div class="sec-head">Gap Analysis (Q2 − Q1)</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="explain-box">
    <b>What is this analysis?</b> The Gap measures the difference between how critical a condition is perceived
    to be (Q2) and how widely it has been observed in practice (Q1). It answers: <i>"Where is the greatest
    mismatch between what is needed and what exists?"</i><br><br>
    <b>Formula:</b> Gap = Q2 Mean − Q1 Mean<br><br>
    <b>How to read it:</b> Positive gaps mean the condition is more important than available — a deficit.
    Larger bars = bigger unmet needs. Negative gaps (rare) would mean a condition is more available than critical.
    The chart ranks all conditions from smallest to largest gap.<br><br>
    <b>⚠️ Critical eye:</b> Note that Q1 uses a 0–4 scale and Q2 uses a 0–5 scale, so some gap is structurally
    expected. Focus on <i>relative</i> ranking (which conditions have the biggest gaps compared to others)
    rather than absolute values.
    </div>
    """, unsafe_allow_html=True)

    gap_sorted = fdf.sort_values("Gap", ascending=True)
    bar_colors = [COLORS["q2"] if g > 0 else COLORS["q3"] for g in gap_sorted["Gap"]]
    fig_gap = go.Figure(go.Bar(
        y=gap_sorted["Main Idea"], x=gap_sorted["Gap"], orientation="h",
        marker_color=bar_colors, text=gap_sorted["Gap"].round(2), textposition="outside",
    ))
    fig_gap.update_layout(yaxis=dict(tickfont=dict(size=10)), xaxis_title="Gap (Q2 − Q1)")
    st.plotly_chart(plotly_defaults(fig_gap, height=max(420, len(gap_sorted) * 22)), use_container_width=True)

    # Auto-interpretation
    top3_gap = fdf.nlargest(3, "Gap")
    bot3_gap = fdf.nsmallest(3, "Gap")
    st.markdown(f"""
    <div class="warn-box">
    <b>⚠️ Largest gaps (highest unmet need):</b><br>
    {"<br>".join([f'• <b>{r["Main Idea"]}</b> — Gap = {r["Gap"]:.2f} (Q2={r["Q2 Mean"]:.2f}, Q1={r["Q1 Mean"]:.2f}). Partners see this as {interpret_q2(r["Q2 Mean"])} but it was {interpret_q1(r["Q1 Mean"])}.' for _, r in top3_gap.iterrows()])}
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="ok-box">
    <b>✅ Smallest gaps (best alignment):</b><br>
    {"<br>".join([f'• <b>{r["Main Idea"]}</b> — Gap = {r["Gap"]:.2f}. Availability is closer to matching its perceived importance.' for _, r in bot3_gap.iterrows()])}
    </div>
    """, unsafe_allow_html=True)

    # Top 10 bottlenecks table
    st.markdown('<div class="sec-head">Top 10 Bottleneck Gaps</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="explain-box">
    <b>What is this?</b> The 10 conditions with the largest Gap, shown with their Resolution Gap and System Stress.
    These are the most pressing areas where action is needed.
    </div>
    """, unsafe_allow_html=True)
    top10 = fdf.nlargest(10, "Gap")[["Category", "Sub Categories", "Main Idea", "Q1 Mean", "Q2 Mean", "Q3 Mean", "Gap", "Resolution Gap", "System Stress"]]
    st.dataframe(
        top10.style.format({c: "{:.2f}" for c in ["Q1 Mean", "Q2 Mean", "Q3 Mean", "Gap", "Resolution Gap", "System Stress"]}),
        use_container_width=True, hide_index=True,
    )

    # Resolution Gap
    st.markdown('<div class="sec-head">Resolution Gap (Q2 − Q3)</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="explain-box">
    <b>What is this?</b> The Resolution Gap measures how much of the critical need remains unaddressed.
    It compares criticality (Q2) with how well challenges have been overcome (Q3).<br><br>
    <b>Formula:</b> Resolution Gap = Q2 Mean − Q3 Mean<br><br>
    <b>How to read it:</b> Larger values mean the condition is critical but its challenges have not been
    sufficiently resolved. Unlike the Gap (Q2−Q1), this focuses on <i>response effectiveness</i> rather than availability.
    Both Q2 and Q3 use the same 0–5 scale, making this a directly comparable metric.
    </div>
    """, unsafe_allow_html=True)

    res_sorted = fdf.sort_values("Resolution Gap", ascending=True)
    fig_res = go.Figure(go.Bar(
        y=res_sorted["Main Idea"], x=res_sorted["Resolution Gap"], orientation="h",
        marker_color=COLORS["accent"], text=res_sorted["Resolution Gap"].round(2), textposition="outside",
    ))
    fig_res.update_layout(xaxis_title="Resolution Gap (Q2 − Q3)")
    st.plotly_chart(plotly_defaults(fig_res, height=max(420, len(res_sorted) * 22)), use_container_width=True)

    # System Stress scatter
    st.markdown('<div class="sec-head">System Stress Map</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="explain-box">
    <b>What is this?</b> A scatter plot combining Gap (x-axis) and Resolution Gap (y-axis) with bubble size
    proportional to System Stress. System Stress = Q2 − (Q1 + Q3)/2: it captures how much criticality
    exceeds the average of availability and resolution combined.<br><br>
    <b>How to read it:</b> Points in the <b>upper-right corner</b> are the most stressed — high gap AND
    poor resolution. These demand urgent, integrated interventions. Points near the origin are more stable.
    </div>
    """, unsafe_allow_html=True)

    fig_stress = px.scatter(
        fdf, x="Gap", y="Resolution Gap", size="System Stress",
        color="Category", hover_name="Main Idea", color_discrete_sequence=CAT_PALETTE, size_max=24,
    )
    fig_stress.update_layout(xaxis_title="Gap (Q2−Q1)", yaxis_title="Resolution Gap (Q2−Q3)")
    st.plotly_chart(plotly_defaults(fig_stress, 480), use_container_width=True)

    most_stressed = fdf.nlargest(3, "System Stress")
    st.markdown(f"""
    <div class="warn-box">
    <b>🔴 Most stressed conditions:</b><br>
    {"<br>".join([f'• <b>{r["Main Idea"]}</b> ({r["Category"]}) — Stress = {r["System Stress"]:.2f}. This condition is {interpret_q2(r["Q2 Mean"])} but {interpret_q1(r["Q1 Mean"])}, and gaps have been {interpret_q3(r["Q3 Mean"])}.' for _, r in most_stressed.iterrows()])}
    </div>
    """, unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────
#  TAB 3 — CATEGORIES
# ──────────────────────────────────────────────────────────────────
with tabs[3]:
    st.markdown('<div class="sec-head">Heatmap — Category × Dimension</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="explain-box">
    <b>What is this?</b> A heatmap showing average values for Q1, Q2, Q3, and Gap by category.
    Colors range from red (low) through yellow to green (high).<br><br>
    <b>How to read it:</b> Look for categories with high Q2 (dark green = very critical) but low Q1
    (red/yellow = not well observed). The Gap column directly shows this mismatch. Categories with
    uniformly high values across all columns are performing well; those with high Q2 but low Q1/Q3
    need attention.
    </div>
    """, unsafe_allow_html=True)

    heat_data = fdf.groupby("Category")[["Q1 Mean", "Q2 Mean", "Q3 Mean", "Gap"]].mean()
    fig_heat = go.Figure(go.Heatmap(
        z=heat_data.values, x=["Q1 Observation", "Q2 Criticality", "Q3 Resolution", "Gap"],
        y=heat_data.index, colorscale="RdYlGn",
        text=np.round(heat_data.values, 2), texttemplate="%{text}",
        textfont=dict(size=13, family="JetBrains Mono"),
    ))
    fig_heat.update_layout(yaxis=dict(autorange="reversed"))
    st.plotly_chart(plotly_defaults(fig_heat, 340), use_container_width=True)

    # Sub-category analysis
    st.markdown('<div class="sec-head">Sub-Category Breakdown</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="explain-box">
    <b>What is this?</b> Expand each category to see how its sub-categories compare on Q1, Q2, and Q3.
    This reveals which specific areas within each category are strongest or weakest.<br><br>
    <b>How to read it:</b> Within each category, compare the height of the red bars (Q2) to the blue (Q1)
    and green (Q3) bars. Sub-categories where red towers over blue and green are the internal priority areas.
    </div>
    """, unsafe_allow_html=True)

    for cat in sel_cats:
        with st.expander(f"📂  {cat}", expanded=False):
            cat_df = fdf[fdf["Category"] == cat]
            sub_avg = cat_df.groupby("Sub Categories")[["Q1 Mean", "Q2 Mean", "Q3 Mean", "Gap"]].mean().reset_index()
            fig_sub = go.Figure()
            for col, color, nm in [
                ("Q1 Mean", COLORS["q1"], "Q1 — Observation"),
                ("Q2 Mean", COLORS["q2"], "Q2 — Criticality"),
                ("Q3 Mean", COLORS["q3"], "Q3 — Resolution"),
            ]:
                fig_sub.add_trace(go.Bar(
                    x=sub_avg["Sub Categories"], y=sub_avg[col], name=nm, marker_color=color,
                    text=sub_avg[col].round(2), textposition="outside",
                ))
            fig_sub.update_layout(barmode="group", yaxis=dict(range=[0, 5.5]), title=cat)
            st.plotly_chart(plotly_defaults(fig_sub, 380), use_container_width=True)

            # Auto-interpret this category
            worst_sub = sub_avg.loc[sub_avg["Gap"].idxmax()]
            best_sub = sub_avg.loc[sub_avg["Gap"].idxmin()]
            st.markdown(f"""
            <div class="insight-box">
            <b>🔍 Within {cat}:</b> The sub-category with the largest gap is <b>{worst_sub['Sub Categories']}</b>
            (Gap = {worst_sub['Gap']:.2f}), while <b>{best_sub['Sub Categories']}</b> shows the best alignment
            (Gap = {best_sub['Gap']:.2f}).
            </div>
            """, unsafe_allow_html=True)

            display_cols = ["Sub Categories", "Main Idea", "Q1 Mean", "Q2 Mean", "Q3 Mean", "Gap"]
            st.dataframe(
                cat_df[display_cols].style.format({c: "{:.2f}" for c in display_cols if "Mean" in c or c == "Gap"}),
                use_container_width=True, hide_index=True,
            )


# ──────────────────────────────────────────────────────────────────
#  TAB 4 — TYPOLOGY
# ──────────────────────────────────────────────────────────────────
with tabs[4]:
    st.markdown('<div class="sec-head">Resilience Typology Classification</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="explain-box">
    <b>What is this analysis?</b> Each enabling condition is classified into one of four types based on its
    combination of Q1 (observation), Q2 (criticality), and Q3 (resolution). This helps prioritize action.<br><br>
    <b>The four types:</b><br>
    🟢 <b>Enabler</b> — Q1 high, Q2 high, Q3 high. These conditions are widely observed, highly critical, and gaps are
    well addressed. <i>These are strengths to protect.</i><br>
    🔴 <b>Bottleneck</b> — Q1 low, Q2 high, Q3 low. Critical but neither well observed nor addressed.
    <i>These are urgent barriers requiring immediate intervention.</i><br>
    🟡 <b>Emerging</b> — Q1 low, Q2 moderate-high, Q3 moderate. Awareness is growing and some effort is underway.
    <i>These need continued investment.</i><br>
    ⚪ <b>Latent</b> — Q1 low, Q2 low. Not yet critical or visible. <i>Monitor as contexts evolve.</i><br><br>
    <b>Current thresholds:</b> High ≥ {t_high} · Low < {t_low} (adjustable in sidebar)
    </div>
    """, unsafe_allow_html=True)

    col_t1, col_t2 = st.columns([1, 1])
    with col_t1:
        type_counts = fdf["Typology"].value_counts().reset_index()
        type_counts.columns = ["Typology", "Count"]
        fig_pie = px.pie(
            type_counts, values="Count", names="Typology", color="Typology",
            color_discrete_map=TYPE_COLORS, hole=0.45,
        )
        fig_pie.update_traces(textinfo="label+percent+value", textfont_size=12)
        st.plotly_chart(plotly_defaults(fig_pie, 400), use_container_width=True)

    with col_t2:
        st.markdown("""
        <div class="explain-box">
        <b>Scatter Plot:</b> Each dot is an enabling condition. The x-axis is Q1 (observation), y-axis is Q2
        (criticality), and dot size is Q3 (resolution). Colors match the typology. Dotted lines show the
        thresholds.<br><br>
        <b>How to read it:</b> Dots in the upper-left (high Q2, low Q1) with small size (low Q3) are
        bottlenecks. Dots in the upper-right with large size are enablers. Look at clustering patterns.
        </div>
        """, unsafe_allow_html=True)
        fig_typ_scatter = px.scatter(
            fdf, x="Q1 Mean", y="Q2 Mean", size="Q3 Mean", color="Typology",
            hover_name="Main Idea", color_discrete_map=TYPE_COLORS, size_max=20,
        )
        fig_typ_scatter.add_hline(y=t_high, line_dash="dot", line_color="#aaa", annotation_text="High")
        fig_typ_scatter.add_vline(x=t_high, line_dash="dot", line_color="#aaa")
        fig_typ_scatter.add_vline(x=t_low, line_dash="dot", line_color="#ccc", annotation_text="Low")
        fig_typ_scatter.update_layout(xaxis_title="Q1 — Observation (0–4)", yaxis_title="Q2 — Criticality (0–5)")
        st.plotly_chart(plotly_defaults(fig_typ_scatter, 400), use_container_width=True)

    # Auto-interpretation
    bottlenecks = fdf[fdf["Typology"] == "Bottleneck"]
    enablers = fdf[fdf["Typology"] == "Enabler"]

    if len(bottlenecks) > 0:
        bn_list = ", ".join(bottlenecks["Main Idea"].tolist()[:5])
        st.markdown(f"""<div class="warn-box"><b>🔴 {len(bottlenecks)} Bottleneck(s) identified:</b> {bn_list}.<br>
        These conditions are perceived as critical for success but are neither widely observed nor adequately resolved.
        They represent the most urgent intervention points.</div>""", unsafe_allow_html=True)
    if len(enablers) > 0:
        en_list = ", ".join(enablers["Main Idea"].tolist()[:5])
        st.markdown(f"""<div class="ok-box"><b>🟢 {len(enablers)} Enabler(s) identified:</b> {en_list}.<br>
        These are working well — observed widely, considered critical, and gaps effectively addressed.
        Protect and build upon these strengths.</div>""", unsafe_allow_html=True)

    # Classification table
    st.markdown('<div class="sec-head">Full Classification Table</div>', unsafe_allow_html=True)
    type_display = fdf[["Category", "Sub Categories", "Main Idea", "Q1 Mean", "Q2 Mean", "Q3 Mean", "Gap", "Typology"]].sort_values("Typology")

    def color_typology(val):
        colors = {"Enabler": "#d4edda", "Bottleneck": "#f8d7da", "Emerging": "#fff3cd", "Latent": "#e2e3e5"}
        return f"background-color: {colors.get(val, '')}"

    styled_types = type_display.style.format({c: "{:.2f}" for c in ["Q1 Mean", "Q2 Mean", "Q3 Mean", "Gap"]})
    try:
        styled_types = styled_types.map(color_typology, subset=["Typology"])
    except AttributeError:
        styled_types = styled_types.applymap(color_typology, subset=["Typology"])
    st.dataframe(styled_types, use_container_width=True, hide_index=True, height=500)

    # Typology by category
    st.markdown('<div class="sec-head">Typology Distribution by Category</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="explain-box">
    <b>What is this?</b> A stacked bar showing how many conditions of each type exist within each category.
    Categories dominated by red (Bottleneck) or yellow (Emerging) need the most attention.
    </div>
    """, unsafe_allow_html=True)

    cross = pd.crosstab(fdf["Category"], fdf["Typology"])
    fig_stack = go.Figure()
    for typ in cross.columns:
        fig_stack.add_trace(go.Bar(
            x=cross.index, y=cross[typ], name=typ, marker_color=TYPE_COLORS.get(typ, "#888"),
        ))
    fig_stack.update_layout(barmode="stack", yaxis_title="Count")
    st.plotly_chart(plotly_defaults(fig_stack, 380), use_container_width=True)


# ──────────────────────────────────────────────────────────────────
#  TAB 5 — VARIABILITY
# ──────────────────────────────────────────────────────────────────
with tabs[5]:
    st.markdown('<div class="sec-head">Variability Analysis</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="explain-box">
    <b>What is this analysis?</b> Variability measures how much partners <i>disagreed</i> in their assessments.
    Even if the mean is 3.5, responses could range from 1 to 5, signaling contested or context-dependent conditions.<br><br>
    <b>Key metric: Coefficient of Variation (CV)</b> = Standard Deviation / Mean. Higher CV = more disagreement
    relative to the average. We flag variables above the 75th percentile as "high variability."<br><br>
    <b>Why it matters:</b> High-variability conditions may require differentiated strategies across contexts
    rather than one-size-fits-all approaches. They may also indicate areas where partners have uneven
    experience or where the condition genuinely varies across member organizations.<br><br>
    <b>How to read the scatter:</b> Each dot is a condition. X-axis = mean value, Y-axis = CV.
    Points above the dotted red line show the highest disagreement. Large dots = higher standard deviation.
    </div>
    """, unsafe_allow_html=True)

    q_select = st.radio("Select dimension", ["Q1", "Q2", "Q3"], horizontal=True,
                        format_func=lambda x: {"Q1": "Q1 — Observation", "Q2": "Q2 — Criticality", "Q3": "Q3 — Resolution"}[x])
    sd_col = f"{q_select} Standard Deviation"
    cv_col = f"{q_select} Coefficient of Variation"
    mean_col = f"{q_select} Mean"

    if sd_col in fdf.columns and cv_col in fdf.columns:
        fig_var = px.scatter(
            fdf, x=mean_col, y=cv_col, size=sd_col, color="Category",
            hover_name="Main Idea", color_discrete_sequence=CAT_PALETTE, size_max=22,
            labels={mean_col: f"{q_select} Mean", cv_col: "Coefficient of Variation"},
        )
        cv_threshold = fdf[cv_col].quantile(0.75)
        fig_var.add_hline(y=cv_threshold, line_dash="dot", line_color="#e8573a",
                          annotation_text=f"75th pctl ({cv_threshold:.2f})")
        st.plotly_chart(plotly_defaults(fig_var, 500), use_container_width=True)

        # Auto-interpretation
        high_var_df = fdf[fdf[cv_col] >= cv_threshold].sort_values(cv_col, ascending=False)
        if len(high_var_df) > 0:
            top_var = high_var_df.head(3)
            st.markdown(f"""
            <div class="warn-box">
            <b>⚠️ Highest disagreement on {q_select}:</b><br>
            {"<br>".join([f'• <b>{r["Main Idea"]}</b> (CV = {r[cv_col]:.3f}, Mean = {r[mean_col]:.2f}). Partners gave very different ratings, suggesting this condition varies significantly across contexts or is perceived differently by different partners.' for _, r in top_var.iterrows()])}
            </div>
            """, unsafe_allow_html=True)

        st.markdown('<div class="sec-head">High-Variability Variables</div>', unsafe_allow_html=True)
        high_var = fdf[fdf[cv_col] >= cv_threshold][["Category", "Sub Categories", "Main Idea", mean_col, sd_col, cv_col]]
        high_var = high_var.sort_values(cv_col, ascending=False)
        st.dataframe(
            high_var.style.format({c: "{:.3f}" for c in [mean_col, sd_col, cv_col]}),
            use_container_width=True, hide_index=True,
        )
    else:
        st.info(f"Columns '{sd_col}' or '{cv_col}' not found in the dataset.")


# ──────────────────────────────────────────────────────────────────
#  TAB 6 — PRIORITY & ADAPTIVE CAPACITY
# ──────────────────────────────────────────────────────────────────
with tabs[6]:
    st.markdown("""
    <div class="explain-box">
    <b>This tab combines two complementary analyses:</b><br><br>
    <b>Priority Score</b> = Q2 × Gap. It identifies the most <i>urgent</i> conditions by combining how critical
    a factor is with how large its gap is. A high score means: "this matters a lot AND it's severely lacking."
    Use this to decide <i>what to fix first</i>.<br><br>
    <b>Adaptive Capacity Index (Efficiency)</b> = Q3 / Q2. It measures the system's response capacity —
    what proportion of the critical need is being effectively addressed. Values below 70% flag conditions
    where the system is failing to respond to its own perceived priorities. Use this to assess <i>how well
    the system responds to what it knows matters</i>.
    </div>
    """, unsafe_allow_html=True)

    col_p, col_a = st.columns(2)

    with col_p:
        st.markdown('<div class="sec-head">Priority Ranking</div>', unsafe_allow_html=True)
        prio = fdf.nlargest(15, "Priority Score")
        fig_prio = go.Figure(go.Bar(
            y=prio["Main Idea"], x=prio["Priority Score"], orientation="h",
            marker=dict(color=prio["Priority Score"], colorscale="OrRd", showscale=True,
                        colorbar=dict(title="Score")),
            text=prio["Priority Score"].round(2), textposition="outside",
        ))
        fig_prio.update_layout(yaxis=dict(autorange="reversed", tickfont=dict(size=10)), xaxis_title="Priority Score")
        st.plotly_chart(plotly_defaults(fig_prio, 520), use_container_width=True)

    with col_a:
        st.markdown('<div class="sec-head">Adaptive Capacity Index</div>', unsafe_allow_html=True)
        eff_sorted = fdf.sort_values("Efficiency", ascending=True)
        bar_c = ["#e8573a" if e < 0.7 else COLORS["q3"] for e in eff_sorted["Efficiency"]]
        fig_eff = go.Figure(go.Bar(
            y=eff_sorted["Main Idea"], x=eff_sorted["Efficiency"], orientation="h",
            marker_color=bar_c, text=eff_sorted["Efficiency"].apply(lambda v: f"{v:.0%}"), textposition="outside",
        ))
        fig_eff.add_vline(x=0.7, line_dash="dash", line_color="#e8573a", annotation_text="70% threshold")
        fig_eff.update_layout(yaxis=dict(autorange="reversed", tickfont=dict(size=10)), xaxis_title="Efficiency (Q3/Q2)")
        st.plotly_chart(plotly_defaults(fig_eff, 520), use_container_width=True)

    # Auto-interpretation
    top_prio = fdf.nlargest(3, "Priority Score")
    low_eff = fdf[fdf["Efficiency"] < 0.7].sort_values("Efficiency")

    st.markdown(f"""
    <div class="warn-box">
    <b>🎯 Top 3 Priorities for Action:</b><br>
    {"<br>".join([f'• <b>{r["Main Idea"]}</b> — Priority Score = {r["Priority Score"]:.2f}. This factor is {interpret_q2(r["Q2 Mean"])} but was {interpret_q1(r["Q1 Mean"])}. It requires urgent attention because it combines high perceived importance with a large gap in availability.' for _, r in top_prio.iterrows()])}
    </div>
    """, unsafe_allow_html=True)

    if len(low_eff) > 0:
        st.markdown(f"""
        <div class="warn-box">
        <b>⚠️ {len(low_eff)} condition(s) with Efficiency below 70%:</b><br>
        {"<br>".join([f'• <b>{r["Main Idea"]}</b> — Efficiency = {r["Efficiency"]:.0%}. Despite being {interpret_q2(r["Q2 Mean"])}, gaps have been {interpret_q3(r["Q3 Mean"])}. Only {r["Efficiency"]:.0%} of the perceived critical need is being resolved.' for _, r in low_eff.head(5).iterrows()])}
        </div>
        """, unsafe_allow_html=True)

    # Strategic Map
    st.markdown('<div class="sec-head">Priority vs Efficiency — Strategic Quadrant Map</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="explain-box">
    <b>What is this?</b> A strategic positioning map combining both analyses. Each dot is a condition.
    X-axis = Priority Score (urgency), Y-axis = Efficiency (adaptive capacity).<br><br>
    <b>How to read the quadrants:</b><br>
    • <b>Upper-left (low priority, high efficiency)</b> — ✅ Stable. Well managed, no urgent action needed.<br>
    • <b>Upper-right (high priority, high efficiency)</b> — 🔄 Responding. Critical and being addressed, maintain effort.<br>
    • <b>Lower-left (low priority, low efficiency)</b> — 👁️ Watch. Not urgent but response capacity is weak.<br>
    • <b>Lower-right (high priority, low efficiency)</b> — ⚠️ <b>Critical zone.</b> Highly urgent AND poorly addressed. Top priority.
    </div>
    """, unsafe_allow_html=True)

    fig_strat = px.scatter(
        fdf, x="Priority Score", y="Efficiency", color="Typology", hover_name="Main Idea",
        size="Gap", size_max=20, color_discrete_map=TYPE_COLORS,
    )
    fig_strat.add_hline(y=0.7, line_dash="dot", line_color="#e8573a", annotation_text="Low efficiency")
    med_prio = fdf["Priority Score"].median()
    fig_strat.add_vline(x=med_prio, line_dash="dot", line_color="#aaa", annotation_text="Median priority")
    fig_strat.add_annotation(x=fdf["Priority Score"].max() * 0.85, y=0.55, text="⚠️ Critical zone",
                             showarrow=False, font=dict(size=11, color="#e8573a"))
    prio_min = fdf["Priority Score"].min()
    fig_strat.add_annotation(x=prio_min + 0.3 if prio_min >= 0 else 0.3,
                             y=fdf["Efficiency"].max() * 0.95, text="✅ Stable",
                             showarrow=False, font=dict(size=11, color="#2ebd6e"))
    st.plotly_chart(plotly_defaults(fig_strat, 500), use_container_width=True)


# ──────────────────────────────────────────────────────────────────
#  TAB 7 — DATA EXPLORER
# ──────────────────────────────────────────────────────────────────
with tabs[7]:
    st.markdown('<div class="sec-head">Full Dataset Explorer</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="explain-box">
    Search, sort, and explore the full dataset. Use the keyword search to find specific conditions by name
    or statement text. Download the filtered or complete analysis dataset as CSV for further work.
    </div>
    """, unsafe_allow_html=True)

    search = st.text_input("🔎 Search by keyword (Main Idea / Statement)", "")
    if search:
        mask = (fdf["Main Idea"].str.contains(search, case=False, na=False)
                | fdf["Statement"].str.contains(search, case=False, na=False))
        explore_df = fdf[mask]
    else:
        explore_df = fdf

    st.dataframe(
        explore_df.style.format({c: "{:.2f}" for c in explore_df.select_dtypes("number").columns}),
        use_container_width=True, hide_index=True, height=600,
    )

    st.markdown("---")
    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        csv_buf = explore_df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download filtered data (CSV)", csv_buf, "resilience_filtered.csv", "text/csv")
    with col_dl2:
        full_csv = fdf.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download full analysis (CSV)", full_csv, "resilience_full_analysis.csv", "text/csv")

    # Q comparison scatter
    st.markdown('<div class="sec-head">Q1 vs Q2 vs Q3 — Pairwise Comparison</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="explain-box">
    <b>What is this?</b> A scatter plot comparing two dimensions at a time. The diagonal dotted line represents
    perfect equality. Points above the line indicate the Y-axis dimension exceeds the X-axis dimension; points
    below indicate the opposite.<br><br>
    <b>Example:</b> In "Q1 vs Q2", points above the diagonal mean criticality exceeds observation (positive gap).
    </div>
    """, unsafe_allow_html=True)

    scatter_mode = st.radio("View", ["Q1 vs Q2", "Q1 vs Q3", "Q2 vs Q3"], horizontal=True, key="scatter_comp")
    x_map = {"Q1 vs Q2": "Q1 Mean", "Q1 vs Q3": "Q1 Mean", "Q2 vs Q3": "Q2 Mean"}
    y_map = {"Q1 vs Q2": "Q2 Mean", "Q1 vs Q3": "Q3 Mean", "Q2 vs Q3": "Q3 Mean"}
    fig_comp = px.scatter(
        fdf, x=x_map[scatter_mode], y=y_map[scatter_mode],
        color="Category", hover_name="Main Idea", color_discrete_sequence=CAT_PALETTE, size_max=14,
    )
    min_v = min(fdf[x_map[scatter_mode]].min(), fdf[y_map[scatter_mode]].min()) - 0.2
    max_v = max(fdf[x_map[scatter_mode]].max(), fdf[y_map[scatter_mode]].max()) + 0.2
    fig_comp.add_trace(go.Scatter(
        x=[min_v, max_v], y=[min_v, max_v], mode="lines",
        line=dict(dash="dot", color="#ccc"), showlegend=False,
    ))
    fig_comp.update_layout(
        xaxis_title=x_map[scatter_mode].replace("Mean", "").strip(),
        yaxis_title=y_map[scatter_mode].replace("Mean", "").strip(),
    )
    st.plotly_chart(plotly_defaults(fig_comp, 460), use_container_width=True)


# ──────────────────────────────────────────────────────────────────
#  TAB 8 — GLOSSARY & SCALES
# ──────────────────────────────────────────────────────────────────
with tabs[8]:
    st.markdown("# 📖 Glossary, Scales & Survey Reference")
    st.markdown("")

    st.markdown("---")
    st.markdown("## 📋 Survey Questions")

    st.markdown("""
    <div class="q-ref">
    <b style="color:#4e6af0;">Q1 — Observation of Enabling Conditions</b><br>
    <i>"Based on your RtR Partner role, have you observed the following enabling conditions supporting
    the implementation of resilience actions across your network of members?"</i>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="q-ref">
    <b style="color:#e8573a;">Q2 — Critical Importance for Implementation Success</b><br>
    <i>"From your experience as a RtR partner, to what extent was this factor critical for the successful
    implementation of actions carried out by your member organizations?"</i>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="q-ref">
    <b style="color:#2ebd6e;">Q3 — Degree of Gap Resolution</b><br>
    <i>"From your experience as a RtR partner, to what extent was this gap or challenge faced by your
    member organizations successfully addressed or overcome during the implementation of their actions?"</i>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("## 📏 Response Scales")

    col_s1, col_s2, col_s3 = st.columns(3)

    with col_s1:
        st.markdown("#### Q1 Scale (0–4)")
        for k, v in Q1_SCALE.items():
            st.markdown(f"**{k}** — {v}")

    with col_s2:
        st.markdown("#### Q2 Scale (0–5)")
        for k, v in Q2_SCALE.items():
            st.markdown(f"**{k}** — {v}")

    with col_s3:
        st.markdown("#### Q3 Scale (0–5)")
        for k, v in Q3_SCALE.items():
            st.markdown(f"**{k}** — {v}")

    st.markdown("---")
    st.markdown("## 📐 Computed Metrics")

    metrics = {
        "Gap (Q2 − Q1)": "Measures the mismatch between perceived criticality and observed availability. A positive gap means the condition is considered more important than it is currently present. **Important note:** Q1 uses a 0–4 scale and Q2 uses a 0–5 scale, so some structural gap is expected. Focus on relative rankings rather than absolute values when comparing across conditions.",
        "Resolution Gap (Q2 − Q3)": "Measures how much of the critical need remains unaddressed. It compares criticality (Q2) with the degree to which challenges were overcome (Q3). Both use a 0–5 scale, making this a direct comparison. Larger values indicate conditions where the system is failing to respond to acknowledged priorities.",
        "System Stress = Q2 − (Q1 + Q3) / 2": "An integrated stress indicator that captures how much criticality exceeds the average of availability and resolution. Higher values indicate conditions under greater overall systemic pressure — where both the starting point (Q1) and the response effort (Q3) are insufficient relative to the perceived need (Q2).",
        "Priority Score = Q2 × Gap": "Combines criticality with gap size to produce an urgency ranking. Conditions that score high are both highly important AND severely lacking — these are where intervention will yield the greatest return. Use this to prioritize resource allocation.",
        "Efficiency = Q3 / Q2": "The ratio of gap resolution to criticality, interpreted as adaptive capacity. A value of 0.85 means 85% of the critical need is being addressed. Values below 0.70 (70%) are flagged as low, indicating the system is under-responding to its own recognized priorities.",
        "Coefficient of Variation (CV) = SD / Mean": "A standardized measure of disagreement among respondents. Higher CV means more divergent opinions relative to the average. Conditions with high CV may need context-specific rather than uniform strategies.",
    }

    for term, definition in metrics.items():
        st.markdown(f"**{term}**")
        st.markdown(f"<div style='color:#4a5068; margin-bottom:1rem; padding-left:1rem; border-left:3px solid #dde3ee;'>{definition}</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("## 🧬 Typology Definitions")

    typology_defs = {
        "🟢 Enabler": "Q1 ≥ High, Q2 ≥ High, Q3 ≥ High. The condition is widely observed, considered critical, and gaps have been effectively addressed. These are **strengths to protect and replicate**. Ask: What made this work? Can it be scaled to other conditions?",
        "🔴 Bottleneck": "Q1 < Low, Q2 ≥ High, Q3 < Low. The condition is critical but neither observed nor resolved. These are **urgent barriers** demanding immediate, targeted intervention. Ask: What is blocking this? Is it a capacity, governance, or resource constraint?",
        "🟡 Emerging": "Q1 < Low, Q2 ≥ Low. The condition is gaining importance and some effort exists, but progress is incomplete. These are **investment opportunities** — momentum exists but needs reinforcement. Ask: What would accelerate progress?",
        "⚪ Latent": "Q1 < Low, Q2 < Low. The condition is neither observed nor considered critical. These may not need immediate action but should be **monitored** as contexts evolve — what is latent today may become critical tomorrow.",
    }

    for term, definition in typology_defs.items():
        st.markdown(f"**{term}**")
        st.markdown(f"<div style='color:#4a5068; margin-bottom:1rem; padding-left:1rem; border-left:3px solid #dde3ee;'>{definition}</div>", unsafe_allow_html=True)
