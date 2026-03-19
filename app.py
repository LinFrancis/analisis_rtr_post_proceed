"""
╔══════════════════════════════════════════════════════════════════╗
║  RESILIENCE ENABLING CONDITIONS — DIAGNOSTIC TOOL              ║
║  Interactive Streamlit Dashboard for RtR Partner Surveys        ║
║  Analyses: Gap, Typology, Priority, Adaptive Capacity & more   ║
╚══════════════════════════════════════════════════════════════════╝
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
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

/* KPI cards */
.kpi-card {
    background: linear-gradient(135deg, #f8f9fc 0%, #eef1f8 100%);
    border: 1px solid #dde3ee;
    border-radius: 14px;
    padding: 1.3rem 1.5rem;
    text-align: center;
    box-shadow: 0 2px 12px rgba(60,70,100,0.06);
    transition: transform 0.2s;
}
.kpi-card:hover { transform: translateY(-2px); }
.kpi-val {
    font-family: 'JetBrains Mono', monospace;
    font-size: 2.1rem;
    font-weight: 700;
    margin: 0.2rem 0;
}
.kpi-label {
    font-size: 0.82rem;
    color: #5a6078;
    font-weight: 500;
    letter-spacing: 0.03em;
    text-transform: uppercase;
}
.kpi-sub {
    font-size: 0.75rem;
    color: #8892a8;
    margin-top: 0.15rem;
}

/* Section headers */
.sec-head {
    font-size: 1.15rem;
    font-weight: 700;
    color: #1a1f36;
    border-left: 4px solid #4e6af0;
    padding-left: 0.8rem;
    margin: 1.5rem 0 0.8rem 0;
}

/* Badge helpers */
.badge {
    display: inline-block;
    padding: 0.2rem 0.65rem;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 600;
}
.badge-green  { background: #d4edda; color: #155724; }
.badge-red    { background: #f8d7da; color: #721c24; }
.badge-yellow { background: #fff3cd; color: #856404; }
.badge-blue   { background: #d6e4f0; color: #1a4e79; }

/* Hide default streamlit footer */
footer { visibility: hidden; }

/* Tab styling */
.stTabs [data-baseweb="tab-list"] { gap: 4px; }
.stTabs [data-baseweb="tab"] {
    border-radius: 8px 8px 0 0;
    font-weight: 600;
    font-size: 0.85rem;
}
</style>
""", unsafe_allow_html=True)

# ── Color palette ────────────────────────────────────────────────
COLORS = {
    "q1": "#4e6af0",   # Availability  – blue
    "q2": "#e8573a",   # Criticality   – coral-red
    "q3": "#2ebd6e",   # Resolution    – green
    "accent": "#7c3aed",
    "bg": "#f8f9fc",
}
CAT_PALETTE = px.colors.qualitative.Set2
TYPE_COLORS = {
    "Enabler": "#2ebd6e",
    "Bottleneck": "#e8573a",
    "Emerging": "#f5a623",
    "Latent": "#8892a8",
}


# ══════════════════════════════════════════════════════════════════
#  DATA LOADING & PROCESSING
# ══════════════════════════════════════════════════════════════════

@st.cache_data
def load_data(file) -> pd.DataFrame:
    """Read the DATASET sheet and return a clean DataFrame."""
    df = pd.read_excel(file, sheet_name="DATASET")
    # Strip whitespace from column names
    df.columns = df.columns.str.strip()
    # Ensure core numeric columns
    for col in ["Q1 Mean", "Q2 Mean", "Q3 Mean"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def compute_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Add derived analytical columns."""
    d = df.copy()
    d["Gap"] = d["Q2 Mean"] - d["Q1 Mean"]
    d["Resolution Gap"] = d["Q2 Mean"] - d["Q3 Mean"]
    d["System Stress"] = d["Q2 Mean"] - (d["Q1 Mean"] + d["Q3 Mean"]) / 2
    d["Priority Score"] = d["Q2 Mean"] * d["Gap"]
    d["Efficiency"] = np.where(d["Q2 Mean"] != 0, d["Q3 Mean"] / d["Q2 Mean"], np.nan)
    return d


def classify_typology(row, t_high, t_low):
    """Classify each variable into a resilience typology."""
    q1, q2, q3 = row["Q1 Mean"], row["Q2 Mean"], row["Q3 Mean"]
    if q1 >= t_high and q2 >= t_high and q3 >= t_high:
        return "Enabler"
    if q1 < t_low and q2 < t_low:
        return "Latent"
    if q1 < t_low and q2 >= t_high and q3 < t_low:
        return "Bottleneck"
    if q1 < t_low and q2 >= t_low:
        return "Emerging"
    # Fallback heuristic
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
    """Apply consistent styling to all Plotly charts."""
    fig.update_layout(
        font=dict(family="DM Sans, sans-serif", size=12),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(248,249,252,1)",
        margin=dict(l=40, r=30, t=50, b=40),
        height=height,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_xaxes(gridcolor="#eaecf2", zeroline=False)
    fig.update_yaxes(gridcolor="#eaecf2", zeroline=False)
    return fig


def kpi_html(value, label, sublabel="", color="#4e6af0"):
    return f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-val" style="color:{color}">{value}</div>
        <div class="kpi-sub">{sublabel}</div>
    </div>"""


# ══════════════════════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("## 🌍 Resilience Diagnostic")
    st.markdown("---")
    uploaded = st.file_uploader("Upload Excel file", type=["xlsx", "xls"])
    st.markdown("---")

    # Thresholds
    st.markdown("### ⚙️ Classification Thresholds")
    t_high = st.slider("High threshold", 1.0, 5.0, 3.2, 0.1, help="Values ≥ this are considered HIGH")
    t_low = st.slider("Low threshold", 1.0, 5.0, 2.8, 0.1, help="Values < this are considered LOW")

    if t_low >= t_high:
        st.warning("Low threshold should be < High threshold")


# ══════════════════════════════════════════════════════════════════
#  MAIN APP
# ══════════════════════════════════════════════════════════════════

if uploaded is None:
    st.markdown("""
    <div style="text-align:center; padding:5rem 2rem;">
        <h1 style="font-size:2.6rem; font-weight:700; color:#1a1f36;">
            🌍 Resilience Enabling Conditions
        </h1>
        <h3 style="color:#5a6078; font-weight:400;">Diagnostic Analysis Tool</h3>
        <p style="color:#8892a8; max-width:520px; margin:1.5rem auto; line-height:1.7;">
            Upload your survey Excel file using the sidebar to begin.<br>
            The app will read the <b>DATASET</b> sheet and generate interactive
            analyses across seven diagnostic dimensions.
        </p>
        <div style="display:flex; gap:1rem; justify-content:center; flex-wrap:wrap; margin-top:2rem;">
            <span class="badge badge-blue">Gap Analysis</span>
            <span class="badge badge-green">Typology</span>
            <span class="badge badge-red">Bottlenecks</span>
            <span class="badge badge-yellow">Priority Ranking</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
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

# Apply filters
fdf = df[df["Category"].isin(sel_cats) & df["Sub Categories"].isin(sel_subs)].copy()

if fdf.empty:
    st.error("No data matches the selected filters. Please adjust your selections.")
    st.stop()

# Classify typology
fdf["Typology"] = fdf.apply(lambda r: classify_typology(r, t_high, t_low), axis=1)

# ══════════════════════════════════════════════════════════════════
#  TABS
# ══════════════════════════════════════════════════════════════════

tabs = st.tabs([
    "📊 Overview",
    "🔻 Gap Analysis",
    "📁 Categories",
    "🧬 Typology",
    "📈 Variability",
    "🎯 Priority & Capacity",
    "🗂 Data Explorer",
    "📖 Glossary",
])

# ──────────────────────────────────────────────────────────────────
#  TAB 0 — OVERVIEW
# ──────────────────────────────────────────────────────────────────
with tabs[0]:
    st.markdown('<div class="sec-head">Global Averages</div>', unsafe_allow_html=True)

    avg_q1 = fdf["Q1 Mean"].mean()
    avg_q2 = fdf["Q2 Mean"].mean()
    avg_q3 = fdf["Q3 Mean"].mean()
    avg_gap = fdf["Gap"].mean()
    avg_eff = fdf["Efficiency"].mean()

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.markdown(kpi_html(f"{avg_q1:.2f}", "Q1 Availability", "Enabling conditions", COLORS["q1"]), unsafe_allow_html=True)
    k2.markdown(kpi_html(f"{avg_q2:.2f}", "Q2 Criticality", "Importance", COLORS["q2"]), unsafe_allow_html=True)
    k3.markdown(kpi_html(f"{avg_q3:.2f}", "Q3 Resolution", "Gap addressed", COLORS["q3"]), unsafe_allow_html=True)
    k4.markdown(kpi_html(f"{avg_gap:.2f}", "Avg Gap", "Q2 − Q1", COLORS["accent"]), unsafe_allow_html=True)
    k5.markdown(kpi_html(f"{avg_eff:.0%}", "Avg Efficiency", "Q3 / Q2", "#1a1f36"), unsafe_allow_html=True)

    st.markdown("")

    # Radar by Category
    st.markdown('<div class="sec-head">Radar by Category</div>', unsafe_allow_html=True)
    cat_avg = fdf.groupby("Category")[["Q1 Mean", "Q2 Mean", "Q3 Mean"]].mean().reset_index()

    fig_radar = go.Figure()
    cats_list = cat_avg["Category"].tolist()
    for col, color, name in [
        ("Q1 Mean", COLORS["q1"], "Q1 Availability"),
        ("Q2 Mean", COLORS["q2"], "Q2 Criticality"),
        ("Q3 Mean", COLORS["q3"], "Q3 Resolution"),
    ]:
        vals = cat_avg[col].tolist()
        vals.append(vals[0])  # close polygon
        fig_radar.add_trace(go.Scatterpolar(
            r=vals,
            theta=cats_list + [cats_list[0]],
            name=name,
            line=dict(color=color, width=2.5),
            fill="toself",
            fillcolor=f"rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},0.08)",
        ))
    fig_radar.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 5], tickfont=dict(size=10)),
            angularaxis=dict(tickfont=dict(size=10)),
        ),
        font=dict(family="DM Sans", size=12),
        margin=dict(l=80, r=80, t=50, b=50),
        height=480,
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_radar, use_container_width=True)

    # Grouped bar overview
    st.markdown('<div class="sec-head">Category Comparison — Bar Chart</div>', unsafe_allow_html=True)
    fig_bar_ov = go.Figure()
    for col, color, name in [
        ("Q1 Mean", COLORS["q1"], "Q1 Availability"),
        ("Q2 Mean", COLORS["q2"], "Q2 Criticality"),
        ("Q3 Mean", COLORS["q3"], "Q3 Resolution"),
    ]:
        fig_bar_ov.add_trace(go.Bar(
            x=cat_avg["Category"], y=cat_avg[col],
            name=name, marker_color=color,
            text=cat_avg[col].round(2), textposition="outside",
        ))
    fig_bar_ov.update_layout(barmode="group", yaxis=dict(range=[0, 5]))
    st.plotly_chart(plotly_defaults(fig_bar_ov), use_container_width=True)

# ──────────────────────────────────────────────────────────────────
#  TAB 1 — GAP ANALYSIS
# ──────────────────────────────────────────────────────────────────
with tabs[1]:
    st.markdown('<div class="sec-head">Gap Analysis (Q2 − Q1)</div>', unsafe_allow_html=True)
    st.caption("The gap measures the difference between perceived criticality and current availability of enabling conditions.")

    gap_sorted = fdf.sort_values("Gap", ascending=True)

    # Color bars by sign
    bar_colors = [COLORS["q2"] if g > 0 else COLORS["q3"] for g in gap_sorted["Gap"]]
    fig_gap = go.Figure(go.Bar(
        y=gap_sorted["Main Idea"],
        x=gap_sorted["Gap"],
        orientation="h",
        marker_color=bar_colors,
        text=gap_sorted["Gap"].round(2),
        textposition="outside",
    ))
    fig_gap.update_layout(yaxis=dict(tickfont=dict(size=10)), xaxis_title="Gap (Q2 − Q1)")
    st.plotly_chart(plotly_defaults(fig_gap, height=max(420, len(gap_sorted) * 22)), use_container_width=True)

    # Top 10 bottlenecks
    st.markdown('<div class="sec-head">Top 10 Bottleneck Gaps</div>', unsafe_allow_html=True)
    top10 = fdf.nlargest(10, "Gap")[["Category", "Sub Categories", "Main Idea", "Q1 Mean", "Q2 Mean", "Q3 Mean", "Gap", "Resolution Gap", "System Stress"]]
    st.dataframe(
        top10.style.format({c: "{:.2f}" for c in ["Q1 Mean", "Q2 Mean", "Q3 Mean", "Gap", "Resolution Gap", "System Stress"]}),
        use_container_width=True, hide_index=True,
    )

    # Resolution Gap chart
    st.markdown('<div class="sec-head">Resolution Gap (Q2 − Q3)</div>', unsafe_allow_html=True)
    res_sorted = fdf.sort_values("Resolution Gap", ascending=True)
    fig_res = go.Figure(go.Bar(
        y=res_sorted["Main Idea"],
        x=res_sorted["Resolution Gap"],
        orientation="h",
        marker_color=COLORS["accent"],
        text=res_sorted["Resolution Gap"].round(2),
        textposition="outside",
    ))
    fig_res.update_layout(xaxis_title="Resolution Gap (Q2 − Q3)")
    st.plotly_chart(plotly_defaults(fig_res, height=max(420, len(res_sorted) * 22)), use_container_width=True)

    # System Stress scatter
    st.markdown('<div class="sec-head">System Stress Map</div>', unsafe_allow_html=True)
    fig_stress = px.scatter(
        fdf, x="Gap", y="Resolution Gap", size="System Stress",
        color="Category", hover_name="Main Idea",
        color_discrete_sequence=CAT_PALETTE,
        size_max=24,
    )
    fig_stress.update_layout(xaxis_title="Gap (Q2−Q1)", yaxis_title="Resolution Gap (Q2−Q3)")
    st.plotly_chart(plotly_defaults(fig_stress, 480), use_container_width=True)

# ──────────────────────────────────────────────────────────────────
#  TAB 2 — CATEGORIES
# ──────────────────────────────────────────────────────────────────
with tabs[2]:
    st.markdown('<div class="sec-head">Heatmap — Category × Dimension</div>', unsafe_allow_html=True)

    heat_data = fdf.groupby("Category")[["Q1 Mean", "Q2 Mean", "Q3 Mean", "Gap"]].mean()
    fig_heat = go.Figure(go.Heatmap(
        z=heat_data.values,
        x=["Q1 Availability", "Q2 Criticality", "Q3 Resolution", "Gap"],
        y=heat_data.index,
        colorscale="RdYlGn",
        text=np.round(heat_data.values, 2),
        texttemplate="%{text}",
        textfont=dict(size=13, family="JetBrains Mono"),
    ))
    fig_heat.update_layout(yaxis=dict(autorange="reversed"))
    st.plotly_chart(plotly_defaults(fig_heat, 340), use_container_width=True)

    # Sub-category analysis per category
    st.markdown('<div class="sec-head">Sub-Category Breakdown</div>', unsafe_allow_html=True)

    for cat in sel_cats:
        with st.expander(f"📂  {cat}", expanded=False):
            cat_df = fdf[fdf["Category"] == cat]
            sub_avg = cat_df.groupby("Sub Categories")[["Q1 Mean", "Q2 Mean", "Q3 Mean", "Gap"]].mean().reset_index()

            fig_sub = go.Figure()
            for col, color, nm in [
                ("Q1 Mean", COLORS["q1"], "Q1"),
                ("Q2 Mean", COLORS["q2"], "Q2"),
                ("Q3 Mean", COLORS["q3"], "Q3"),
            ]:
                fig_sub.add_trace(go.Bar(
                    x=sub_avg["Sub Categories"], y=sub_avg[col],
                    name=nm, marker_color=color,
                    text=sub_avg[col].round(2), textposition="outside",
                ))
            fig_sub.update_layout(barmode="group", yaxis=dict(range=[0, 5]), title=cat)
            st.plotly_chart(plotly_defaults(fig_sub, 380), use_container_width=True)

            # Detail table
            display_cols = ["Sub Categories", "Main Idea", "Q1 Mean", "Q2 Mean", "Q3 Mean", "Gap"]
            st.dataframe(
                cat_df[display_cols].style.format({c: "{:.2f}" for c in display_cols if "Mean" in c or c == "Gap"}),
                use_container_width=True, hide_index=True,
            )

# ──────────────────────────────────────────────────────────────────
#  TAB 3 — TYPOLOGY
# ──────────────────────────────────────────────────────────────────
with tabs[3]:
    st.markdown('<div class="sec-head">Resilience Typology Classification</div>', unsafe_allow_html=True)
    st.caption(f"Thresholds — High: ≥ {t_high}  |  Low: < {t_low}  (adjust in sidebar)")

    col_t1, col_t2 = st.columns([1, 1])

    # Pie chart
    with col_t1:
        type_counts = fdf["Typology"].value_counts().reset_index()
        type_counts.columns = ["Typology", "Count"]
        fig_pie = px.pie(
            type_counts, values="Count", names="Typology",
            color="Typology",
            color_discrete_map=TYPE_COLORS,
            hole=0.45,
        )
        fig_pie.update_traces(textinfo="label+percent+value", textfont_size=12)
        st.plotly_chart(plotly_defaults(fig_pie, 400), use_container_width=True)

    # Scatter triangle: Q1 vs Q2 colored by typology
    with col_t2:
        fig_typ_scatter = px.scatter(
            fdf, x="Q1 Mean", y="Q2 Mean", size="Q3 Mean",
            color="Typology", hover_name="Main Idea",
            color_discrete_map=TYPE_COLORS,
            size_max=20,
        )
        fig_typ_scatter.add_hline(y=t_high, line_dash="dot", line_color="#aaa", annotation_text="High")
        fig_typ_scatter.add_vline(x=t_high, line_dash="dot", line_color="#aaa")
        fig_typ_scatter.add_vline(x=t_low, line_dash="dot", line_color="#ccc", annotation_text="Low")
        fig_typ_scatter.update_layout(xaxis_title="Q1 Availability", yaxis_title="Q2 Criticality")
        st.plotly_chart(plotly_defaults(fig_typ_scatter, 400), use_container_width=True)

    # Classification table
    st.markdown('<div class="sec-head">Classification Table</div>', unsafe_allow_html=True)
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

    # Typology by category breakdown
    st.markdown('<div class="sec-head">Typology Distribution by Category</div>', unsafe_allow_html=True)
    cross = pd.crosstab(fdf["Category"], fdf["Typology"])
    fig_stack = go.Figure()
    for typ in cross.columns:
        fig_stack.add_trace(go.Bar(
            x=cross.index, y=cross[typ], name=typ,
            marker_color=TYPE_COLORS.get(typ, "#888"),
        ))
    fig_stack.update_layout(barmode="stack", yaxis_title="Count")
    st.plotly_chart(plotly_defaults(fig_stack, 380), use_container_width=True)

# ──────────────────────────────────────────────────────────────────
#  TAB 4 — VARIABILITY
# ──────────────────────────────────────────────────────────────────
with tabs[4]:
    st.markdown('<div class="sec-head">Variability Analysis</div>', unsafe_allow_html=True)
    st.caption("High variability (Coefficient of Variation) signals disagreement among respondents.")

    q_select = st.radio("Select dimension", ["Q1", "Q2", "Q3"], horizontal=True)
    sd_col = f"{q_select} Standard Deviation"
    cv_col = f"{q_select} Coefficient of Variation"
    mean_col = f"{q_select} Mean"

    if sd_col in fdf.columns and cv_col in fdf.columns:
        # Mean vs CV scatter
        fig_var = px.scatter(
            fdf, x=mean_col, y=cv_col,
            size=sd_col, color="Category",
            hover_name="Main Idea",
            color_discrete_sequence=CAT_PALETTE,
            size_max=22,
            labels={mean_col: f"{q_select} Mean", cv_col: "Coefficient of Variation"},
        )
        cv_threshold = fdf[cv_col].quantile(0.75)
        fig_var.add_hline(y=cv_threshold, line_dash="dot", line_color="#e8573a",
                          annotation_text=f"75th pctl ({cv_threshold:.2f})")
        st.plotly_chart(plotly_defaults(fig_var, 500), use_container_width=True)

        # Flag high-variability items
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
#  TAB 5 — PRIORITY & ADAPTIVE CAPACITY
# ──────────────────────────────────────────────────────────────────
with tabs[5]:
    col_p, col_a = st.columns(2)

    # Priority ranking
    with col_p:
        st.markdown('<div class="sec-head">Priority Ranking</div>', unsafe_allow_html=True)
        st.caption("Priority Score = Q2 × Gap.  Higher = more urgent.")
        prio = fdf.nlargest(15, "Priority Score")
        fig_prio = go.Figure(go.Bar(
            y=prio["Main Idea"],
            x=prio["Priority Score"],
            orientation="h",
            marker=dict(
                color=prio["Priority Score"],
                colorscale="OrRd",
                showscale=True,
                colorbar=dict(title="Score"),
            ),
            text=prio["Priority Score"].round(2),
            textposition="outside",
        ))
        fig_prio.update_layout(yaxis=dict(autorange="reversed", tickfont=dict(size=10)), xaxis_title="Priority Score")
        st.plotly_chart(plotly_defaults(fig_prio, 520), use_container_width=True)

    # Adaptive Capacity
    with col_a:
        st.markdown('<div class="sec-head">Adaptive Capacity Index</div>', unsafe_allow_html=True)
        st.caption("Efficiency = Q3 / Q2.  Values < 0.70 flagged as low.")
        eff_sorted = fdf.sort_values("Efficiency", ascending=True)
        bar_c = ["#e8573a" if e < 0.7 else COLORS["q3"] for e in eff_sorted["Efficiency"]]
        fig_eff = go.Figure(go.Bar(
            y=eff_sorted["Main Idea"],
            x=eff_sorted["Efficiency"],
            orientation="h",
            marker_color=bar_c,
            text=eff_sorted["Efficiency"].apply(lambda v: f"{v:.0%}"),
            textposition="outside",
        ))
        fig_eff.add_vline(x=0.7, line_dash="dash", line_color="#e8573a", annotation_text="Threshold 0.70")
        fig_eff.update_layout(yaxis=dict(autorange="reversed", tickfont=dict(size=10)), xaxis_title="Efficiency (Q3/Q2)")
        st.plotly_chart(plotly_defaults(fig_eff, 520), use_container_width=True)

    # Scatter: Priority vs Efficiency
    st.markdown('<div class="sec-head">Priority vs Efficiency — Strategic Map</div>', unsafe_allow_html=True)
    fig_strat = px.scatter(
        fdf, x="Priority Score", y="Efficiency",
        color="Typology", hover_name="Main Idea",
        size="Gap", size_max=20,
        color_discrete_map=TYPE_COLORS,
    )
    fig_strat.add_hline(y=0.7, line_dash="dot", line_color="#e8573a", annotation_text="Low efficiency")
    med_prio = fdf["Priority Score"].median()
    fig_strat.add_vline(x=med_prio, line_dash="dot", line_color="#aaa", annotation_text="Median priority")
    # Quadrant labels
    fig_strat.add_annotation(x=fdf["Priority Score"].max() * 0.85, y=0.55, text="⚠️ Critical", showarrow=False, font=dict(size=11, color="#e8573a"))
    fig_strat.add_annotation(x=fdf["Priority Score"].min() * 1.5, y=fdf["Efficiency"].max() * 0.95, text="✅ Stable", showarrow=False, font=dict(size=11, color="#2ebd6e"))
    st.plotly_chart(plotly_defaults(fig_strat, 500), use_container_width=True)

# ──────────────────────────────────────────────────────────────────
#  TAB 6 — DATA EXPLORER
# ──────────────────────────────────────────────────────────────────
with tabs[6]:
    st.markdown('<div class="sec-head">Full Dataset Explorer</div>', unsafe_allow_html=True)

    search = st.text_input("🔎 Search by keyword (Main Idea / Statement)", "")
    if search:
        mask = (
            fdf["Main Idea"].str.contains(search, case=False, na=False)
            | fdf["Statement"].str.contains(search, case=False, na=False)
        )
        explore_df = fdf[mask]
    else:
        explore_df = fdf

    st.dataframe(
        explore_df.style.format({c: "{:.2f}" for c in explore_df.select_dtypes("number").columns}),
        use_container_width=True, hide_index=True, height=600,
    )

    st.markdown("---")
    col_dl1, col_dl2 = st.columns(2)

    # Download filtered CSV
    with col_dl1:
        csv_buf = explore_df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download filtered data (CSV)", csv_buf, "resilience_filtered.csv", "text/csv")

    # Download full analysis
    with col_dl2:
        full_csv = fdf.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download full analysis (CSV)", full_csv, "resilience_full_analysis.csv", "text/csv")

    # Q1 vs Q2 vs Q3 comparison triangle
    st.markdown('<div class="sec-head">Q1 vs Q2 vs Q3 — Comparison Scatter</div>', unsafe_allow_html=True)
    scatter_mode = st.radio("View", ["Q1 vs Q2", "Q1 vs Q3", "Q2 vs Q3"], horizontal=True, key="scatter_comp")
    x_map = {"Q1 vs Q2": "Q1 Mean", "Q1 vs Q3": "Q1 Mean", "Q2 vs Q3": "Q2 Mean"}
    y_map = {"Q1 vs Q2": "Q2 Mean", "Q1 vs Q3": "Q3 Mean", "Q2 vs Q3": "Q3 Mean"}
    fig_comp = px.scatter(
        fdf, x=x_map[scatter_mode], y=y_map[scatter_mode],
        color="Category", hover_name="Main Idea",
        color_discrete_sequence=CAT_PALETTE,
        size_max=14,
    )
    # Diagonal reference line
    min_v = min(fdf[x_map[scatter_mode]].min(), fdf[y_map[scatter_mode]].min()) - 0.2
    max_v = max(fdf[x_map[scatter_mode]].max(), fdf[y_map[scatter_mode]].max()) + 0.2
    fig_comp.add_trace(go.Scatter(
        x=[min_v, max_v], y=[min_v, max_v],
        mode="lines", line=dict(dash="dot", color="#ccc"), showlegend=False,
    ))
    st.plotly_chart(plotly_defaults(fig_comp, 460), use_container_width=True)

# ──────────────────────────────────────────────────────────────────
#  TAB 7 — GLOSSARY
# ──────────────────────────────────────────────────────────────────
with tabs[7]:
    st.markdown('<div class="sec-head">📖 Glossary of Terms</div>', unsafe_allow_html=True)
    st.markdown("")

    glossary = {
        "Q1 — Availability of Enabling Conditions": "Measures the extent to which essential enabling conditions (governance, finance, knowledge, partnerships) are currently present and accessible for resilience actions. Higher values indicate stronger foundational conditions.",
        "Q2 — Critical Importance": "Measures how critical or important each enabling condition is perceived to be for achieving resilience objectives. Higher values indicate factors considered essential by respondents.",
        "Q3 — Degree of Gap Resolution": "Measures the extent to which identified gaps between availability and importance have been addressed or resolved. Higher values indicate greater progress in closing gaps.",
        "Gap (Q2 − Q1)": "The difference between perceived criticality (Q2) and current availability (Q1). Positive values indicate conditions considered important but insufficiently present — a demand-supply deficit for resilience.",
        "Resolution Gap (Q2 − Q3)": "The difference between perceived criticality (Q2) and the degree of resolution (Q3). Reflects how much of the critical need remains unaddressed despite efforts.",
        "System Stress": "Defined as Q2 − (Q1 + Q3) / 2. Captures the overall tension in the system: how much criticality exceeds the average of availability and resolution capacity. Higher values indicate conditions under greater systemic pressure.",
        "Priority Score (Q2 × Gap)": "Combines criticality with gap magnitude to identify the most actionable priorities. A high score means the condition is both highly important and severely lacking — demanding urgent attention.",
        "Efficiency (Q3 / Q2)": "The ratio of resolution capacity to criticality. Values below 0.70 indicate that less than 70% of the critical need is being addressed, flagging low adaptive capacity.",
        "Typology — Enabler": "Conditions where availability (Q1), criticality (Q2), and resolution (Q3) are all high. These are strengths to protect and build upon.",
        "Typology — Bottleneck": "Conditions with low availability (Q1), high criticality (Q2), and low resolution (Q3). These represent the most critical barriers requiring immediate intervention.",
        "Typology — Emerging": "Conditions with low availability but moderate-to-high criticality and resolution. These are areas where awareness is growing and initial efforts are underway but more investment is needed.",
        "Typology — Latent": "Conditions with low availability and low criticality. These may not require immediate attention but should be monitored as contexts evolve.",
        "Coefficient of Variation (CV)": "The ratio of the standard deviation to the mean. Higher values indicate greater disagreement or variability among respondents, signaling contested or context-dependent conditions.",
    }

    for term, definition in glossary.items():
        st.markdown(f"**{term}**")
        st.markdown(f"<div style='color:#4a5068; margin-bottom:1rem; padding-left:1rem; border-left:3px solid #dde3ee;'>{definition}</div>", unsafe_allow_html=True)
