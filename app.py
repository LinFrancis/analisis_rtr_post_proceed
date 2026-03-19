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
import scipy.stats as stats
from scipy.stats import norm

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
#  FUNCIONES PARA EL ANÁLISIS DE Q‑METHODOLOGY (MEJORADAS)
# ══════════════════════════════════════════════════════════════════

# --- Rotaciones ortogonales adicionales ---
def varimax(loadings, normalize=True, eps=1e-6):
    """Rotación Varimax (ortogonal)"""
    n_rows, n_cols = loadings.shape
    if n_cols < 2:
        return loadings, np.eye(n_cols)
    if normalize:
        h2 = np.sum(loadings**2, axis=1, keepdims=True)
        h2 = np.maximum(h2, eps)
        scaled_loadings = loadings / np.sqrt(h2)
    else:
        scaled_loadings = loadings
    rotmat = np.eye(n_cols)
    d = 0
    for _ in range(50):
        old_d = d
        L = np.dot(scaled_loadings, rotmat)
        B = np.dot(L.T, (L**3 - np.dot(L, np.diag(np.sum(L**2, axis=0)) / n_rows)))
        U, s, Vh = np.linalg.svd(B)
        rotmat = np.dot(U, Vh)
        d = np.sum(s)
        if d / old_d < 1 + eps and old_d != 0:
            break
    rotated = np.dot(loadings, rotmat)
    return rotated, rotmat

def quartimax(loadings, normalize=True, eps=1e-6):
    """Rotación Quartimax (ortogonal) - maximiza la varianza de las filas"""
    n_rows, n_cols = loadings.shape
    if n_cols < 2:
        return loadings, np.eye(n_cols)
    if normalize:
        h2 = np.sum(loadings**2, axis=1, keepdims=True)
        h2 = np.maximum(h2, eps)
        scaled_loadings = loadings / np.sqrt(h2)
    else:
        scaled_loadings = loadings
    rotmat = np.eye(n_cols)
    d = 0
    for _ in range(50):
        old_d = d
        L = np.dot(scaled_loadings, rotmat)
        # Quartimax: maximizar suma de cuartas potencias de las cargas
        B = np.dot(L.T, L**3)
        U, s, Vh = np.linalg.svd(B)
        rotmat = np.dot(U, Vh)
        d = np.sum(s)
        if d / old_d < 1 + eps and old_d != 0:
            break
    rotated = np.dot(loadings, rotmat)
    return rotated, rotmat

def equamax(loadings, normalize=True, eps=1e-6):
    """Rotación Equamax (ortogonal) - compromiso entre Varimax y Quartimax"""
    n_rows, n_cols = loadings.shape
    if n_cols < 2:
        return loadings, np.eye(n_cols)
    if normalize:
        h2 = np.sum(loadings**2, axis=1, keepdims=True)
        h2 = np.maximum(h2, eps)
        scaled_loadings = loadings / np.sqrt(h2)
    else:
        scaled_loadings = loadings
    rotmat = np.eye(n_cols)
    d = 0
    for _ in range(50):
        old_d = d
        L = np.dot(scaled_loadings, rotmat)
        # Equamax: combina criterios de Varimax y Quartimax
        B = np.dot(L.T, (L**3 - np.dot(L, np.diag(np.sum(L**2, axis=0)) / (2*n_rows))))
        U, s, Vh = np.linalg.svd(B)
        rotmat = np.dot(U, Vh)
        d = np.sum(s)
        if d / old_d < 1 + eps and old_d != 0:
            break
    rotated = np.dot(loadings, rotmat)
    return rotated, rotmat

def promax(loadings, power=3, normalize=True):
    """Rotación Promax (oblicua). power típico = 3 o 4."""
    n_rows, n_cols = loadings.shape
    if n_cols < 2:
        return loadings, np.eye(n_cols)
    # Primero rotación varimax para obtener una base ortogonal
    loadings_rot, rotmat_var = varimax(loadings, normalize=normalize)
    # Crear matriz objetivo: elevar las cargas al cubo (manteniendo signo)
    target = np.sign(loadings_rot) * (np.abs(loadings_rot) ** power)
    # Resolver para la matriz de transformación oblicua
    from scipy.linalg import lstsq
    Phi, _, _, _ = lstsq(loadings_rot, target)
    loadings_promax = np.dot(loadings, Phi)
    return loadings_promax, Phi


@st.cache_data
def load_q_from_excel(file, question):
    """
    Extrae los datos de Q‑sort del archivo Excel ya cargado.
    Parámetros:
        file: archivo Excel subido (BytesIO)
        question: 'Q1', 'Q2' o 'Q3'
    Retorna:
        statements_df: DataFrame con columnas ['Statement', 'Category'] para cada afirmación
        q_data: DataFrame con índices = afirmaciones, columnas = participantes, valores = puntuaciones
    """
    # Leer DATASET para obtener las afirmaciones en orden y sus categorías
    df_dataset = pd.read_excel(file, sheet_name="DATASET")
    df_dataset.columns = df_dataset.columns.str.strip()
    statements_df = df_dataset[["Statement", "Category"]].dropna().copy()
    
    # Mapeo de pregunta a nombre de hoja
    sheet_map = {"Q1": "QUESTION 1", "Q2": "QUESTION 2", "Q3": "QUESTION 3"}
    sheet_name = sheet_map[question]
    
    # Leer la hoja de respuestas individuales con header=1 (fila 2 tiene nombres de partners)
    df_resp = pd.read_excel(file, sheet_name=sheet_name, header=1)
    # Las columnas esperadas: Category, Statement, Sub-category, luego los partners
    partner_cols = df_resp.columns[3:]
    df_partners = df_resp[partner_cols].copy()
    
    # Asegurar que el número de filas coincida con el número de afirmaciones
    df_partners = df_partners.iloc[:len(statements_df)]
    
    # Reemplazar "NR" por NaN y convertir a numérico
    df_partners = df_partners.replace("NR", np.nan)
    df_partners = df_partners.apply(pd.to_numeric, errors='coerce')
    
    # Establecer el índice como las afirmaciones
    df_partners.index = statements_df["Statement"].tolist()
    
    # Eliminar participantes (columnas) que tengan algún NaN
    participantes_validos = df_partners.columns[df_partners.isna().sum() == 0]
    df_clean = df_partners[participantes_validos]
    
    n_eliminados = len(df_partners.columns) - len(participantes_validos)
    if n_eliminados > 0:
        st.info(f"Se eliminaron {n_eliminados} participantes por tener valores faltantes (NR).")
    
    return statements_df, df_clean


def perform_q_analysis(q_data, n_factors=None, rotation='varimax'):
    """
    Realiza análisis factorial de Q.
    Parámetros:
        q_data: DataFrame (afirmaciones × participantes)
        n_factors: número de factores a extraer (None = automático por eigenvalue>1)
        rotation: método de rotación ('varimax', 'quartimax', 'equamax', 'promax', 'none')
    Retorna diccionario con resultados.
    """
    sorts = q_data.T  # shape: (n_participantes, n_afirmaciones)
    n_participants, n_statements = sorts.shape

    # 1. Matriz de correlación
    corr = np.corrcoef(sorts.values)
    if np.isnan(corr).any():
        st.warning("La matriz de correlación contiene NaN. Se imputarán con 0.")
        corr = np.nan_to_num(corr)

    # 2. Autovalores y autovectores
    eigenvals, eigenvecs = np.linalg.eigh(corr)
    idx = np.argsort(eigenvals)[::-1]
    eigenvals = eigenvals[idx]
    eigenvecs = eigenvecs[:, idx]

    # 3. Seleccionar número de factores
    if n_factors is None:
        n_factors = np.sum(eigenvals > 1.0)
        if n_factors < 1:
            n_factors = 1
    else:
        n_factors = min(int(n_factors), n_participants)

    # 4. Cargas no rotadas
    loadings_unrot = eigenvecs[:, :n_factors] * np.sqrt(eigenvals[:n_factors])

    # 5. Rotación
    if rotation == 'varimax' and n_factors > 1:
        loadings, rotmat = varimax(loadings_unrot)
    elif rotation == 'quartimax' and n_factors > 1:
        loadings, rotmat = quartimax(loadings_unrot)
    elif rotation == 'equamax' and n_factors > 1:
        loadings, rotmat = equamax(loadings_unrot)
    elif rotation == 'promax' and n_factors > 1:
        loadings, rotmat = promax(loadings_unrot)
    else:
        loadings = loadings_unrot
        rotmat = np.eye(n_factors)

    # 6. Puntuaciones factoriales (z‑scores)
    sorts_norm = (sorts - sorts.mean(axis=1).values[:, None]) / sorts.std(axis=1).values[:, None]
    sorts_norm = sorts_norm.fillna(0)

    weights = loadings
    z_scores = np.zeros((n_factors, n_statements))
    for f in range(n_factors):
        w = weights[:, f]
        denom = np.sum(w**2)
        if denom > 0:
            z_scores[f] = np.sum(w[:, None] * sorts_norm.values, axis=0) / denom
        else:
            z_scores[f] = 0

    # 7. Arrays de factores (valores de cuadrícula -5..+5)
    probs = np.linspace(0, 1, 12)[1:-1]
    cutoffs = norm.ppf(probs)
    factor_arrays = np.zeros_like(z_scores)
    for f in range(n_factors):
        z_std = (z_scores[f] - np.mean(z_scores[f])) / np.std(z_scores[f])
        bins = np.concatenate([[-np.inf], cutoffs, [np.inf]])
        labels = np.arange(-5, 6)
        factor_arrays[f] = labels[np.digitize(z_std, bins) - 1]

    # 8. Afirmaciones distintivas y de consenso
    distinctive = []
    consensus = []
    threshold = 1.0
    for i in range(n_statements):
        z_factors = z_scores[:, i]
        max_diff = np.max(z_factors) - np.min(z_factors)
        if max_diff < threshold:
            consensus.append(i)
        else:
            for f in range(n_factors):
                others = np.delete(z_factors, f)
                if abs(z_factors[f] - np.mean(others)) > threshold:
                    distinctive.append((f, i))

    explained_var = eigenvals[:n_factors] / n_participants * 100

    loadings_df = pd.DataFrame(loadings,
                               index=sorts.index,
                               columns=[f"Factor {i+1}" for i in range(n_factors)])
    z_df = pd.DataFrame(z_scores.T,
                        index=q_data.index,
                        columns=[f"Factor {i+1}" for i in range(n_factors)])
    array_df = pd.DataFrame(factor_arrays.T,
                            index=q_data.index,
                            columns=[f"Factor {i+1}" for i in range(n_factors)])

    results = {
        'n_factors': n_factors,
        'eigenvals': eigenvals,
        'explained_var': explained_var,
        'loadings': loadings_df,
        'z_scores': z_df,
        'factor_arrays': array_df,
        'distinctive': distinctive,
        'consensus': consensus,
        'n_participants': n_participants,
        'n_statements': n_statements,
        'correlation_matrix': corr,
    }
    return results


# ══════════════════════════════════════════════════════════════════
#  DATA LOADING & PROCESSING (original)
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
#  TABS (ahora 10 pestañas)
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
    "🧩 Q‑Methodology",      # índice 8
    "📖 Glossary & Scales",  # índice 9
])

# ──────────────────────────────────────────────────────────────────
#  TAB 0 — INTRODUCTION (actualizada)
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
    <b>🧩 Q‑Methodology</b> — Performs factor analysis on individual partner responses to identify shared viewpoints (factors). You can select Q1, Q2, or Q3, filter by category, choose among several rotation methods (varimax, quartimax, equamax, promax, or none), and obtain factor loadings, z‑scores, factor arrays, and distinguishing/consensus statements.<br>
    <b>📖 Glossary & Scales</b> — Complete reference for all metrics, scales, and survey questions.
    </div>
    """, unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────
#  TABS 1 a 7 (originales) - deben estar completos con tu código original.
#  Por brevedad, aquí se indica el lugar, pero en el archivo final deben incluirse.
# ──────────────────────────────────────────────────────────────────
with tabs[1]:
    # (Código original de Overview)
    st.markdown("### Overview tab content (original)")
    # ... pega aquí tu código existente ...

with tabs[2]:
    # (Código original de Gap Analysis)
    st.markdown("### Gap Analysis tab content (original)")
    # ... pega aquí tu código existente ...

with tabs[3]:
    # (Código original de Categories)
    st.markdown("### Categories tab content (original)")
    # ... pega aquí tu código existente ...

with tabs[4]:
    # (Código original de Typology)
    st.markdown("### Typology tab content (original)")
    # ... pega aquí tu código existente ...

with tabs[5]:
    # (Código original de Variability)
    st.markdown("### Variability tab content (original)")
    # ... pega aquí tu código existente ...

with tabs[6]:
    # (Código original de Priority & Capacity)
    st.markdown("### Priority & Capacity tab content (original)")
    # ... pega aquí tu código existente ...

with tabs[7]:
    # (Código original de Data Explorer)
    st.markdown("### Data Explorer tab content (original)")
    # ... pega aquí tu código existente ...


# ──────────────────────────────────────────────────────────────────
#  TAB 8 — Q‑METHODOLOGY (CON FILTRO POR CATEGORÍA)
# ──────────────────────────────────────────────────────────────────
with tabs[8]:
    st.markdown('<div class="sec-head">🧩 Q‑Methodology Analysis</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="explain-box">
    <b>What is Q‑methodology?</b> Q‑methodology is a research technique used to systematically study subjective
    viewpoints. It combines qualitative and quantitative approaches to identify shared patterns of thinking
    among participants. In this context, we analyze how the RtR partners rank the enabling condition statements
    (the same 36 statements from the survey) according to a forced quasi‑normal distribution (from -5 to +5).
    By correlating and factor‑analyzing individual Q‑sorts, we uncover distinct factors (viewpoints) that
    represent different ways partners perceive the importance and performance of enabling conditions.
    <br><br>
    <b>⚠️ Note on small sample size:</b> With few participants, factor extraction should be conservative.
    The Kaiser criterion (eigenvalue > 1) may overestimate the number of factors; consider selecting fewer
    factors manually (1 or 2) and examine the loadings carefully.
    <br><br>
    <b>How to use this tab:</b> Select which question (Q1, Q2, or Q3) you want to analyze – each represents a
    different rating dimension (observation, criticality, resolution). The app will automatically extract
    the individual partner responses from the corresponding <b>QUESTION</b> sheet. Then you can filter by one or more
    categories to focus on specific thematic areas. Partners with incomplete data (any "NR" values) are excluded.
    You can then choose the number of factors to extract (or let the Kaiser criterion decide), select a rotation method,
    and run the analysis. The output includes factor loadings, z‑scores, factor arrays (the reconstructed Q‑sort for each factor),
    and lists of distinguishing and consensus statements.
    </div>
    """, unsafe_allow_html=True)

    # Inicializar session_state
    if 'q_data_full' not in st.session_state:
        st.session_state.q_data_full = None
        st.session_state.q_statements_df = None
        st.session_state.q_choice = None
        st.session_state.q_results = None
        st.session_state.q_categories = []

    # Selector de pregunta
    q_choice = st.radio("Select question for Q‑analysis", ["Q1", "Q2", "Q3"], horizontal=True,
                        format_func=lambda x: f"{x} – " + {"Q1": "Observation (0-4)", "Q2": "Criticality (0-5)", "Q3": "Resolution (0-5)"}[x])

    # Botón para cargar datos (solo si cambia la pregunta o no hay datos)
    if st.button("Load data", type="primary") or (st.session_state.q_data_full is not None and st.session_state.q_choice != q_choice):
        with st.spinner("Extracting data..."):
            try:
                statements_df, q_data_full = load_q_from_excel(uploaded, q_choice)
                if q_data_full.shape[1] == 0:
                    st.error("No complete participants found after removing missing values.")
                    st.session_state.q_data_full = None
                else:
                    st.session_state.q_data_full = q_data_full
                    st.session_state.q_statements_df = statements_df
                    st.session_state.q_choice = q_choice
                    st.session_state.q_results = None
                    st.success(f"Data loaded: {q_data_full.shape[1]} valid participants, {q_data_full.shape[0]} statements total.")
                    if q_data_full.shape[1] < 5:
                        st.warning("Very small sample size. Results should be interpreted with caution.")
            except Exception as e:
                st.error(f"Error loading data: {e}")
                st.session_state.q_data_full = None

    # Si hay datos cargados, mostrar opciones
    if st.session_state.q_data_full is not None:
        q_data_full = st.session_state.q_data_full
        statements_df = st.session_state.q_statements_df

        # Mostrar información de categorías disponibles
        all_cats_q = sorted(statements_df["Category"].unique())
        st.markdown("### Filter by category")
        selected_cats = st.multiselect("Select one or more categories", all_cats_q, default=all_cats_q, key="q_cats")
        if not selected_cats:
            st.warning("Please select at least one category.")
            st.stop()

        # Filtrar afirmaciones por categoría
        filtered_statements = statements_df[statements_df["Category"].isin(selected_cats)]["Statement"].tolist()
        q_data = q_data_full.loc[filtered_statements]
        if q_data.shape[0] < 2:
            st.error("After filtering, there are fewer than 2 statements. Cannot perform factor analysis.")
            st.stop()

        st.info(f"Analysis will use **{q_data.shape[0]} statements** from categories: {', '.join(selected_cats)}.")

        with st.expander("Preview filtered Q‑sort matrix (first few participants)"):
            st.dataframe(q_data.iloc[:, :5].head(10))

        col1, col2 = st.columns(2)
        with col1:
            auto_factors = st.checkbox("Select number of factors automatically (eigenvalue > 1)", value=True, key="auto_factors")
            if not auto_factors:
                n_factors = st.number_input("Number of factors to extract", min_value=1, max_value=min(10, q_data.shape[1]), value=2, key="n_factors")
            else:
                n_factors = None
        with col2:
            rotation = st.selectbox("Rotation method", ["varimax", "quartimax", "equamax", "promax", "none"], index=0, key="rotation")
            if rotation == "promax":
                st.caption("Promax is an oblique rotation (factors may be correlated).")

        if st.button("Run factor analysis", type="secondary"):
            with st.spinner("Performing factor analysis..."):
                try:
                    results = perform_q_analysis(q_data, n_factors=n_factors, rotation=rotation)
                    st.session_state.q_results = results
                except Exception as e:
                    st.error(f"Error during factor analysis: {e}")
                    st.session_state.q_results = None

        # Mostrar resultados si existen
        if st.session_state.q_results is not None:
            results = st.session_state.q_results
            st.markdown("---")
            st.markdown('<div class="sec-head">Factor Analysis Results</div>', unsafe_allow_html=True)

            # Scree plot
            fig_scree = go.Figure()
            fig_scree.add_trace(go.Bar(x=list(range(1, len(results['eigenvals'])+1)), y=results['eigenvals'],
                                        marker_color=COLORS['q1'], name="Eigenvalues"))
            fig_scree.add_hline(y=1, line_dash="dash", line_color="red", annotation_text="Kaiser >1")
            fig_scree.update_layout(xaxis_title="Factor", yaxis_title="Eigenvalue", title="Scree plot")
            st.plotly_chart(plotly_defaults(fig_scree, 400), use_container_width=True)

            st.markdown(f"**Number of factors retained:** {results['n_factors']}")
            st.markdown(f"**Variance explained by each factor:**")
            for i, var in enumerate(results['explained_var']):
                st.markdown(f"- Factor {i+1}: {var:.2f}%")

            # Factor loadings
            st.markdown('<div class="sec-head">Factor Loadings (participants × factors)</div>', unsafe_allow_html=True)
            loadings_disp = results['loadings'].copy()
            def highlight_high(val):
                color = 'background-color: #d4edda' if abs(val) > 0.5 else ''
                return color
            st.dataframe(loadings_disp.style.applymap(highlight_high).format("{:.3f}"),
                         use_container_width=True, height=400)

            # Z‑scores
            st.markdown('<div class="sec-head">Factor Z‑scores (per statement)</div>', unsafe_allow_html=True)
            st.dataframe(results['z_scores'].style.format("{:.3f}"), use_container_width=True)

            # Factor arrays
            st.markdown('<div class="sec-head">Factor Arrays (grid values -5 to +5)</div>', unsafe_allow_html=True)
            st.dataframe(results['factor_arrays'].style.format("{:.0f}"), use_container_width=True)

            # Distinguishing and consensus statements
            st.markdown('<div class="sec-head">Distinguishing and Consensus Statements</div>', unsafe_allow_html=True)

            statements_list = filtered_statements
            distinctive_by_factor = {f"Factor {i+1}": [] for i in range(results['n_factors'])}
            for (f, idx) in results['distinctive']:
                distinctive_by_factor[f"Factor {f+1}"].append(statements_list[idx])

            for factor, stmts in distinctive_by_factor.items():
                if stmts:
                    st.markdown(f"**{factor}** (distinguishing statements):")
                    for s in stmts:
                        st.markdown(f"- {s}")

            if results['consensus']:
                st.markdown("**Consensus statements** (all factors agree):")
                for idx in results['consensus']:
                    st.markdown(f"- {statements_list[idx]}")

            # Profile plot
            st.markdown('<div class="sec-head">Factor Z‑score Profiles</div>', unsafe_allow_html=True)
            fig_z = go.Figure()
            for i in range(results['n_factors']):
                fig_z.add_trace(go.Scatter(x=list(range(len(statements_list))),
                                            y=results['z_scores'].iloc[:, i],
                                            mode='lines+markers',
                                            name=f"Factor {i+1}"))
            fig_z.update_layout(xaxis_title="Statement index", yaxis_title="z‑score")
            st.plotly_chart(plotly_defaults(fig_z, 500), use_container_width=True)

            # Download results
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                results['loadings'].to_excel(writer, sheet_name='Loadings')
                results['z_scores'].to_excel(writer, sheet_name='Z_scores')
                results['factor_arrays'].to_excel(writer, sheet_name='Factor_arrays')
            st.download_button("⬇️ Download complete results (Excel)", output.getvalue(),
                               file_name="q_analysis_results.xlsx")


# ──────────────────────────────────────────────────────────────────
#  TAB 9 — GLOSSARY & SCALES (original)
# ──────────────────────────────────────────────────────────────────
with tabs[9]:
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
