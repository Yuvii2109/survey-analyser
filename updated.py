import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# ─────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="R-Cube Strategic Intelligence",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
#  CUSTOM CSS – Unified Editorial Theme
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

/* Reset & Base */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}
.stApp {
    background: #fdfcf9; /* Soft Ivory Background */
    color: #1a1c20;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #f4f2ee !important;
    border-right: 1px solid #e2e2e0;
}
[data-testid="stSidebar"] * { 
    color: #2d3138 !important; 
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 { 
    color: #1a1c20 !important; 
}

/* Main headings */
h1, h2, h3 { 
    font-family: 'Playfair Display', serif !important; 
    color: #1a1c20 !important; 
}

/* Hide Streamlit chrome & Adjust Top Padding */
#MainMenu, footer{ 
    visibility: hidden; 
}
.block-container { 
    padding-top: 4rem; 
    padding-bottom: 2rem; 
}

/* ── Large KPI Card (Top Section) ── */
.kpi-card-large {
    background: #ffffff;
    border: 1px solid #e8e8e6;
    box-shadow: 0 4px 12px rgba(0,0,0,0.03);
    border-radius: 12px;
    padding: 2rem 2.5rem;
    position: relative;
    overflow: hidden;
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: center;
}
.kpi-card-large::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 4px;
    background: #2e9c6e;
}
.kpi-large-label {
    font-family: 'DM Mono', monospace;
    font-size: 0.75rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: #6a6a65;
    margin-bottom: 0.5rem;
}
.kpi-large-value {
    font-family: 'Playfair Display', serif;
    font-size: 4.5rem;
    font-weight: 900;
    line-height: 1;
    margin-bottom: 0.5rem;
    color: #1e7d54;
}

/* ── Standard KPI Cards ── */
.kpi-card {
    background: #ffffff;
    border: 1px solid #e8e8e6;
    box-shadow: 0 4px 12px rgba(0,0,0,0.03);
    border-radius: 12px;
    padding: 1.5rem 1.75rem;
    position: relative;
    overflow: hidden;
}
.kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
}
.kpi-card.growth::before { background: #2e9c6e; }

.kpi-label {
    font-family: 'DM Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: #6a6a65;
    margin-bottom: 0.5rem;
}
.kpi-value {
    font-family: 'Playfair Display', serif;
    font-size: 2.8rem;
    font-weight: 900;
    line-height: 1;
    margin-bottom: 0.3rem;
}
.kpi-value.growth { color: #1e7d54; }

.kpi-band {
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.05em;
    padding: 2px 8px;
    border-radius: 4px;
    display: inline-block;
    margin-top: 0.25rem;
}
.band-fragile     { background: #fff5f5; color: #e03131; border: 1px solid #ffc9c9; }
.band-emerging    { background: #fff9db; color: #f08c00; border: 1px solid #ffec99; }
.band-developing  { background: #ebfbee; color: #2b8a3e; border: 1px solid #b2f2bb; }
.band-strong      { background: #e7f5ff; color: #1971c2; border: 1px solid #a5d8ff; }
.band-benchmark   { background: #f8f0fc; color: #9c36b5; border: 1px solid #eebefa; }

/* ── Stage Bar ── */
.stage-bar-wrap {
    background: #ffffff;
    border: 1px solid #e8e8e6;
    border-radius: 12px;
    padding: 1.5rem;
}
.stage-row {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 1rem;
}
.stage-label {
    font-family: 'DM Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: #666660;
    width: 140px;
}
.stage-track {
    flex: 1;
    height: 8px;
    background: #f0f0ee;
    border-radius: 4px;
}
.stage-fill {
    height: 100%;
    border-radius: 4px;
}
.stage-val {
    font-family: 'DM Mono', monospace;
    font-size: 0.8rem;
    color: #4a4a48;
    width: 30px;
    text-align: right;
}

/* ── Status Badge ── */
.status-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.6rem;
    padding: 0.5rem 1.2rem;
    border-radius: 8px;
    font-family: 'DM Mono', monospace;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
}
.badge-benchmark  { background: #f8f0fc; border: 1px solid #9c36b5; color: #9c36b5; }
.badge-fragile    { background: #fff5f5; border: 1px solid #fa5252; color: #fa5252; }
.badge-efficient  { background: #ebfbee; border: 1px solid #2f9e44; color: #2f9e44; }
.badge-legacy     { background: #e7f5ff; border: 1px solid #1971c2; color: #1971c2; }
.badge-default    { background: #f8f9fa; border: 1px solid #dee2e6; color: #495057; }

.badge-desc {
    font-size: 0.85rem;
    color: #555550;
    margin-left: 10px;
}

/* ── Section headers ── */
.section-header {
    border-bottom: 1px solid #e2e2e0;
    margin-bottom: 1.5rem;
    padding-bottom: 0.5rem;
}
.section-number { 
    color: #a0a09a; 
    font-family: 'DM Mono', monospace; 
    margin-right: 10px; 
}
.section-title { 
    font-family: 'Playfair Display', serif; 
    font-size: 1.5rem; 
    font-weight: 700; 
    color: #1a1c20; 
}

/* ── Explanations & Focus Table ── */
.explain-wrap, .focus-wrap {
    background: #ffffff;
    border: 1px solid #e8e8e6;
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
}
.explain-head, .focus-title {
    font-family: 'Playfair Display', serif;
    font-size: 1.4rem;
    font-weight: 900;
    color: #1a1c20;
    margin-bottom: 0.5rem;
}
.explain-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
    margin-top: 1rem;
}
.explain-card {
    background: #fdfcf9;
    border: 1px solid #ecebe8;
    border-radius: 8px;
    padding: 1.25rem;
}
.explain-card h4 {
    margin: 0 0 0.5rem 0;
    font-family: 'DM Mono', monospace;
    font-size: 0.8rem;
    text-transform: uppercase;
}
.exp-rel h4 { color: #b08d20; }
.exp-reli h4 { color: #2a7a9e; }
.exp-repu h4 { color: #7e46b0; }

.focus-table {
    width: 100%;
    border-collapse: collapse;
    min-width: 600px;
}
.focus-table th,
.focus-table td {
    border: 1px solid #e2e2e0;
    padding: 1rem 0.8rem;
    vertical-align: top;
    font-size: 0.95rem;
    color: #3f403d;
    line-height: 1.5;
}
.focus-table th {
    background: #f4f2ee;
    font-family: 'DM Mono', monospace;
    font-size: 0.8rem;
    text-align: left;
}
.focus-stage {
    font-family: 'DM Mono', monospace;
    font-size: 0.8rem;
    font-weight: 700;
    background: #faf9f6;
}

hr { 
    border-color: #e2e2e0 !important; 
    margin: 2rem 0; 
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  CONSTANTS & PLOTLY THEME
# ─────────────────────────────────────────────
BAND_LABELS = {
    (0, 40):  ("Fragile",          "band-fragile"),
    (40, 60): ("Emerging",         "band-emerging"),
    (60, 75): ("Developing",       "band-developing"),
    (75, 90): ("Strong",           "band-strong"),
    (90, 101):("Benchmark",        "band-benchmark"),
}

PLOTLY_THEME = dict(
    paper_bgcolor="rgba(255,255,255,0)",
    plot_bgcolor="rgba(255,255,255,0)",
    font=dict(family="DM Sans", color="#2d3138", size=11),
    margin=dict(l=20, r=20, t=40, b=20),
)

# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────
def get_band(score):
    for (lo, hi), (label, css) in BAND_LABELS.items():
        if lo <= score < hi:
            return label, css
    return "Benchmark", "band-benchmark"

def score_to_color(score):
    if score < 40:  return "#e03131"
    if score < 60:  return "#f08c00"
    if score < 75:  return "#1971c2"
    if score < 90:  return "#2b8a3e"
    return "#9c36b5"

def get_strategic_profile(row):
    gi = row['Growth_Index']
    rel  = row['Relevance']
    reli = row['Reliability_Adj']
    repu = row['Reputability_Adj']

    if gi >= 85:
        return "🏆 Benchmark", "badge-benchmark", "Market leader setting the standard for peers."
    if rel > 70 and reli < 50:
        return "⚡ Fragile Starter", "badge-fragile", "Strong vision, but operational systems failing to match ambition."
    if reli > 70 and rel < 50:
        return "⚙️ Efficient Machine", "badge-efficient", "Consistent delivery, but at risk of becoming obsolete."
    if reli > 60 and repu > 60:
        return "📜 Legacy Builder", "badge-legacy", "Strong operations and building long-term authority."
    if gi < 40:
        return "🛑 Fragile Foundation", "badge-fragile", "Immediate intervention required in core foundations."
    
    return "🌱 Emerging", "badge-default", "Moving out of survival phase and stabilising operations."

# ─────────────────────────────────────────────
#  DATA PROCESSING (CACHED)
# ─────────────────────────────────────────────
@st.cache_data
def process_raw_data(df):
    q_cols = df.columns[8:28]
    df = df.rename(columns={q_cols[i]: f'Q{i+1}' for i in range(len(q_cols))})
    df.insert(0, 'UserID', [f"User {i+1}" for i in range(len(df))])
    
    response_map_lower = {
        "completely disagree": 1, 
        "disagree": 2,
        "don't know, can't say": 3, 
        "don't know ,can't say": 3,
        "don’t know, can’t say": 3,
        "agree": 4, 
        "completely agree": 5, 
    }
    
    for i in range(1, 21):
        col = f'Q{i}'
        if pd.api.types.is_numeric_dtype(df[col]):
            df[col] = df[col].fillna(3)
        else:
            df[col] = df[col].astype(str).str.lower().str.strip()
            df[col] = df[col].map(response_map_lower).fillna(3)
            
    return df

@st.cache_data
def calculate_metrics(df):
    df = df.copy()
    
    for i in [1, 2, 3, 4, 5]: 
        df[f'S{i}'] = (5 - df[f'Q{i}']) * 25
    for i in range(6, 21): 
        df[f'S{i}'] = (df[f'Q{i}'] - 1) * 25

    df['Relevance'] = df[['S1', 'S2', 'S5', 'S11', 'S13', 'S14']].mean(axis=1)
    df['Rel_Raw'] = df[['S3', 'S4', 'S6', 'S7', 'S8', 'S9', 'S10', 'S12', 'S14', 'S15']].mean(axis=1)
    df['Rep_Raw'] = df[['S16', 'S17', 'S18', 'S19', 'S20']].mean(axis=1)

    df['Reliability_Adj'] = df['Rel_Raw'] * (0.75 + 0.25 * df['Relevance'] / 100)
    min_floor = df[['Relevance', 'Reliability_Adj']].min(axis=1)
    df['Reputability_Adj'] = df['Rep_Raw'] * (0.60 + 0.40 * min_floor / 100)

    df['Foundation']    = df[[f'Q{i}' for i in range(1, 6)]].mean(axis=1)
    df['Growth']        = df[[f'Q{i}' for i in range(6, 11)]].mean(axis=1)
    df['Acceleration']  = df[[f'Q{i}' for i in range(11, 16)]].mean(axis=1)
    df['Legacy']        = df[[f'Q{i}' for i in range(16, 21)]].mean(axis=1)

    df['Growth_Index'] = (0.35 * df['Relevance'] + 0.40 * df['Reliability_Adj'] + 0.25 * df['Reputability_Adj'])
    return df

# ─────────────────────────────────────────────
#  CHART BUILDERS (LIGHT THEME OPTIMIZED)
# ─────────────────────────────────────────────
def top_distribution_chart(results, current_user):
    """Generates the wide distribution chart for the top section"""
    fig = go.Figure()
    df_sorted = results.sort_values('Growth_Index', ascending=False)
    
    # Highlight the selected user in brand green, others in neutral grey
    colors = ['#2e9c6e' if u == current_user else '#e8e8e6' for u in df_sorted['UserID']]
    
    fig.add_trace(go.Bar(
        x=df_sorted['UserID'], 
        y=df_sorted['Growth_Index'],
        marker=dict(color=colors, line=dict(width=0)),
        hovertemplate="<b>%{x}</b><br>Growth Index: %{y:.1f}<extra></extra>",
    ))
    
    # First apply the base theme
    fig.update_layout(**PLOTLY_THEME)
    
    # Then override with specific layout settings for this chart
    fig.update_layout(
        height=240,
        margin=dict(l=10, r=10, t=40, b=20), # Overrides the default theme margin
        xaxis=dict(showticklabels=False, title=dict(text="Cohort Ranking (Highest to Lowest)", font=dict(size=10, color='#8a8a84'))),
        yaxis=dict(range=[0, 100], gridcolor='#e2e2e0', zeroline=False),
        bargap=0.15,
        title=dict(text="GROWTH INDEX DISTRIBUTION", font=dict(size=11, family='DM Mono', color='#6a6a65', weight='bold'), x=0.01, y=0.95)
    )
    return fig

def sigmoid_growth_chart(row):
    """Shows the selected user's position on the Growth Index maturity curve."""
    value = float(row['Growth_Index'])
    curve_x = np.linspace(0, 100, 300)
    curve_y = 100 / (1 + np.exp(-0.10 * (curve_x - 50)))
    marker_y = 100 / (1 + np.exp(-0.10 * (value - 50)))
    marker_color = score_to_color(value)

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=curve_x,
        y=curve_y,
        mode='lines',
        line=dict(color='#2e9c6e', width=4, shape='spline'),
        hoverinfo='skip',
        name='Growth Curve',
    ))

    fig.add_trace(go.Scatter(
        x=[value],
        y=[marker_y],
        mode='markers+text',
        marker=dict(
            color=marker_color,
            size=16,
            line=dict(color='#ffffff', width=3),
        ),
        text=["You are here"],
        textposition='top center',
        textfont=dict(family='DM Mono', size=12, color='#1a1c20'),
        hovertemplate="<b>You are here</b><br>Growth Index: %{x:.1f}<extra></extra>",
        name='Current Position',
    ))

    fig.add_shape(
        type='line',
        x0=value,
        x1=value,
        y0=0,
        y1=marker_y,
        line=dict(color=marker_color, width=1.5, dash='dot'),
    )

    fig.update_layout(**PLOTLY_THEME)
    fig.update_layout(
        height=300,
        margin=dict(l=10, r=20, t=55, b=42),
        title=dict(
            text="GROWTH INDEX MATURITY CURVE",
            font=dict(size=11, family='DM Mono', color='#6a6a65', weight='bold'),
            x=0.01,
            y=0.95,
        ),
        showlegend=False,
        xaxis=dict(
            range=[0, 100],
            tickmode='array',
            tickvals=[0, 40, 60, 75, 90, 100],
            ticktext=['0', '40', '60', '75', '90', '100'],
            title=dict(text="Growth Index", font=dict(size=10, color='#8a8a84')),
            gridcolor='#ecebe8',
            zeroline=False,
        ),
        yaxis=dict(
            range=[0, 105],
            showticklabels=False,
            title='',
            gridcolor='#f2f1ee',
            zeroline=False,
        ),
    )

    fig.add_annotation(
        x=18,
        y=12,
        text="Foundation",
        showarrow=False,
        font=dict(family='DM Mono', size=10, color='#a0a09a'),
    )
    fig.add_annotation(
        x=82,
        y=92,
        text="Benchmark",
        showarrow=False,
        font=dict(family='DM Mono', size=10, color='#a0a09a'),
    )

    return fig

def radar_chart(row):
    cats = ['Foundation', 'Growth', 'Acceleration', 'Legacy']
    vals = [row[c] for c in cats]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=vals + [vals[0]], 
        theta=cats + [cats[0]], 
        fill='toself',
        fillcolor='rgba(58, 143, 181, 0.2)', 
        line=dict(color='#3a8fb5', width=3),
        name='Profile', 
        hovertemplate='%{theta}: %{r:.2f}<extra></extra>',
    ))
    
    bench = [4, 4, 4, 4]
    fig.add_trace(go.Scatterpolar(
        r=bench + [bench[0]], 
        theta=cats + [cats[0]],
        line=dict(color='rgba(160, 160, 154, 0.5)', width=2, dash='dash'),
        mode='lines', 
        name='Benchmark', 
        hoverinfo='skip',
    ))
    
    fig.update_layout(
        **PLOTLY_THEME,
        polar=dict(
            bgcolor='rgba(255,255,255,0.6)',
            radialaxis=dict(visible=True, range=[0, 5], color='#6a6a65', gridcolor='#e2e2e0', tickfont=dict(size=10)),
            angularaxis=dict(color='#2d3138', gridcolor='#e2e2e0', tickfont=dict(size=12, weight='bold')),
        ), 
        showlegend=False, 
        height=320,
    )
    return fig

def gauge_chart(value, title, color):
    fig = go.Figure(go.Indicator(
        mode="gauge+number", 
        value=value,
        number=dict(font=dict(family="Playfair Display", size=42, color=color), valueformat=".1f"),
        gauge=dict(
            axis=dict(range=[0, 100], tickwidth=0, visible=False),
            bar=dict(color=color, thickness=0.7), 
            bgcolor='#f0f0ee', 
            borderwidth=0,
            steps=[
                dict(range=[0, 40],  color='rgba(250, 82, 82, 0.1)'),
                dict(range=[40, 60], color='rgba(240, 140, 0, 0.1)'),
                dict(range=[60, 75], color='rgba(43, 138, 62, 0.1)'),
                dict(range=[75, 90], color='rgba(25, 113, 194, 0.1)'),
                dict(range=[90, 100],color='rgba(156, 54, 181, 0.1)'),
            ],
            threshold=dict(line=dict(color='#2d3138', width=3), thickness=0.8, value=75),
        ),
    ))
    
    fig.update_layout(
        **PLOTLY_THEME, 
        height=220, 
        title=dict(text=title, font=dict(size=12, family='DM Mono', color='#6a6a65', weight='bold'), x=0.5, y=0.9)
    )
    return fig

# ─────────────────────────────────────────────
#  HTML COMPONENTS
# ─────────────────────────────────────────────
def kpi_card(label, value, card_cls, val_cls):
    band_label, band_css = get_band(value)
    return f"""
    <div class="kpi-card {card_cls}">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value {val_cls}">{value:.0f}</div>
        <span class="kpi-band {band_css}">{band_label}</span>
    </div>
    """

def section_header(num, title):
    return f"""
    <div class="section-header">
        <span class="section-number">{num}</span>
        <span class="section-title">{title}</span>
    </div>
    """

def stage_bar_html(row):
    stages = [
        ("Foundation", row['Foundation'], 5, "#d4af37"), 
        ("Growth", row['Growth'], 5, "#3a8fb5"), 
        ("Acceleration", row['Acceleration'], 5, "#9b5fcf"), 
        ("Legacy", row['Legacy'], 5, "#2e9c6e")
    ]
    
    bars = ""
    for label, val, max_val, color in stages:
        pct = (val / max_val) * 100
        bars += f'<div class="stage-row"><span class="stage-label">{label}</span><div class="stage-track"><div class="stage-fill" style="width:{pct:.1f}%; background:{color};"></div></div><span class="stage-val">{val:.2f}</span></div>'
        
    return f'<div class="stage-bar-wrap">{bars}</div>'

def score_explanation_html():
    return """
    <div class="explain-wrap">
        <div class="explain-head">Maturity Benchmarks</div>
        <div style="font-size: 0.95rem; color: #555550;">Core pillars of the R-Cube Framework</div>
        <div class="explain-grid">
            <div class="explain-card exp-rel">
                <h4>Relevance</h4>
                <ul style="font-size: 0.9rem; line-height: 1.5; color: #4a4a48; margin-top: 0.5rem; padding-left: 1.2rem;">
                    <li>The school meets the immediate needs of parents and students.</li>
                    <li>The focus is on curriculum alignment, compliance, visibility, and initial trust-building.</li>
                    <li>The school has a unique value proposition that differentiates from other schools.</li>
                </ul>
            </div>
            <div class="explain-card exp-reli">
                <h4>Reliability (Adj)</h4>
                <ul style="font-size: 0.9rem; line-height: 1.5; color: #4a4a48; margin-top: 0.5rem; padding-left: 1.2rem;">
                    <li>Parents and the community trust that the school delivers consistently year after year.</li>
                    <li>This means strong academic outcomes, defined SOPs, teacher stability, and structured parent engagement.</li>
                    <li>The school innovates and has created a system that can be scaled by empowering middle leaders, embedding technology, and maintaining quality across larger student numbers.</li>
                </ul>
            </div>
            <div class="explain-card exp-repu">
                <h4>Reputability (Adj)</h4>
                <ul style="font-size: 0.9rem; line-height: 1.5; color: #4a4a48; margin-top: 0.5rem; padding-left: 1.2rem;">
                    <li>The school is recognized at state, national, or international levels.</li>
                    <li>The school engages in legacy-building initiatives such as research, publications, alumni networks, awards, and collaborations.</li>
                    <li>Parents choose the school because it is seen as a benchmark of excellence.</li>
                </ul>
            </div>
        </div>
    </div>
    """

def growth_stage_focus_html():
    return """
    <div class="focus-wrap">
        <div class="focus-title">Strategic Growth Focus Matrix</div>
        <table class="focus-table">
            <thead>
                <tr>
                    <th>Stage</th>
                    <th>Promoter Focus</th>
                    <th>School Leader Focus</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td class="focus-stage">Foundation (0-40)</td>
                    <td>Capital allocation, infrastructure setup, core hiring (Principal, Admins), initial marketing.</td>
                    <td>Defining standard operating procedures (SOPs), establishing basic discipline, and ensuring safety and compliance.</td>
                </tr>
                <tr>
                    <td class="focus-stage">Growth (41-75)</td>
                    <td>Governance, brand positioning, and scaling resources for middle management.</td>
                    <td>Driving academic excellence, teacher professional development, parent engagement, and embedding technology.</td>
                </tr>
                <tr>
                    <td class="focus-stage">Acceleration (76-100)</td>
                    <td>Strategic alliances, expansion, innovation funding, and legacy planning.</td>
                    <td>Thought leadership, curriculum innovation, empowering student-led initiatives, and building an alumni network.</td>
                </tr>
            </tbody>
        </table>
    </div>
    """

# ─────────────────────────────────────────────
#  SIDEBAR & APP LOGIC
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='padding: 0.5rem 0 1.5rem 0;'>
        <div style='font-family: Playfair Display, serif; font-size: 1.5rem; font-weight: 900; color: #1a1c20; line-height: 1.1;'>
            R-Cube<br>Strategic Intelligence
        </div>
        <div style='font-family: DM Mono, monospace; font-size: 0.6rem; letter-spacing: 0.2em; color: #6a6a65; text-transform: uppercase; margin-top: 0.4rem;'>
            Screening Metric v2
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("Upload Response CSV", type=["csv"])
    
    st.markdown("---")
    st.markdown("""
    <div style='font-family: DM Mono, monospace; font-size: 0.6rem; color: #6a6a65; letter-spacing: 0.1em; text-transform: uppercase;'>
        Scoring Model
    </div>
    <div style='font-size: 0.8rem; color: #4a4a48; margin-top: 0.5rem; line-height: 1.6;'>
        <b style='color:#b08d20;'>Relevance</b> — Q1,2,5,11,13,14<br>
        <b style='color:#2a7a9e;'>Reliability</b> — Q3,4,6-10,12,14,15<br>
        <b style='color:#7e46b0;'>Reputability</b> — Q16–20<br><br>
        GI = 0.35·R + 0.40·Rel + 0.25·Rep
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  MAIN DASHBOARD
# ─────────────────────────────────────────────
if not uploaded_file:
    st.markdown("""
    <div style='display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 70vh; text-align: center; padding: 2rem;'>
        <div style='font-family: Playfair Display, serif; font-size: 3.5rem; font-weight: 900; color: #1a1c20; line-height: 1.1; max-width: 700px;'>
            R-Cube Strategic<br>Command Centre
        </div>
        <div style='font-family: DM Sans, sans-serif; font-size: 1.1rem; color: #4a4a48; margin-top: 1rem; max-width: 480px; line-height: 1.7;'>
            Upload your response CSV to generate per-school strategic profiles, maturity-adjusted R-scores, and competitive benchmarking.
        </div>
        <div style='margin-top: 2.5rem; font-family: DM Mono, monospace; font-size: 0.75rem; letter-spacing: 0.15em; text-transform: uppercase; color: #2d3138; border: 1px solid #c8c8c4; padding: 0.75rem 1.5rem; border-radius: 8px; background: #ffffff;'>
            ← Upload CSV in sidebar to begin
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    raw = pd.read_csv(uploaded_file)
    raw = process_raw_data(raw)
    results = calculate_metrics(raw)

    with st.sidebar:
        st.markdown("---")
        user_choice = st.selectbox("Select User Report", results['UserID'].tolist())
        avg_gi = results['Growth_Index'].mean()
        rank = int(results['Growth_Index'].rank(ascending=False)[results['UserID'] == user_choice].values[0])
        
        st.markdown(f"""
        <div style='margin-top: 1.5rem;'>
            <div style='font-family: DM Mono, monospace; font-size: 0.6rem; color: #6a6a65; letter-spacing: 0.1em; text-transform: uppercase;'>Cohort Avg GI</div>
            <div style='font-family: Playfair Display, serif; font-size: 1.6rem; font-weight: 900; color: #1a1c20;'>{avg_gi:.1f}</div>
        </div>
        <div style='margin-top: 1rem;'>
            <div style='font-family: DM Mono, monospace; font-size: 0.6rem; color: #6a6a65; letter-spacing: 0.1em; text-transform: uppercase;'>Current Rank</div>
            <div style='font-family: Playfair Display, serif; font-size: 1.6rem; font-weight: 900; color: #b08d20;'>#{rank} / {len(results)}</div>
        </div>
        """, unsafe_allow_html=True)

    row = results[results['UserID'] == user_choice].iloc[0]
    label, badge_cls, desc = get_strategic_profile(row)

    # Header
    st.markdown(f"""
    <div style='margin-top: 1rem; margin-bottom: 2.5rem;'>
        <div style='font-family: DM Mono, monospace; font-size: 0.7rem; color: #6a6a65; letter-spacing: 0.15em; text-transform: uppercase; margin-bottom: 0.3rem;'>
            Individual Strategic Report
        </div>
        <div style='font-family: Playfair Display, serif; font-size: 2.8rem; font-weight: 900; color: #1a1c20; line-height: 1.1; margin-bottom: 0.8rem;'>
            {user_choice}
        </div>
        <div style='display: flex; align-items: center; gap: 10px; flex-wrap: wrap;'>
            <span class='status-badge {badge_cls}'>{label}</span>
            <span class='badge-desc'>{desc}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── HERO SECTION: Large Growth Index Card & Distribution Graph ──
    col1, col2 = st.columns([1, 2.5])
    
    with col1: 
        band_label, band_css = get_band(row['Growth_Index'])
        st.markdown(f"""
        <div class="kpi-card-large">
            <div class="kpi-large-label">Growth Index</div>
            <div class="kpi-large-value">{row['Growth_Index']:.0f}</div>
            <div><span class="kpi-band {band_css}">{band_label}</span></div>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.plotly_chart(sigmoid_growth_chart(row), width='stretch')
    
    st.markdown("<br>", unsafe_allow_html=True)

    # Gauges Section
    st.markdown(section_header("01", "R-Cube Maturity Gauges"), unsafe_allow_html=True)
    g1, g2, g3 = st.columns(3)
    with g1: st.plotly_chart(gauge_chart(row['Relevance'], "RELEVANCE", "#d4af37"), width='stretch')
    with g2: st.plotly_chart(gauge_chart(row['Reliability_Adj'], "RELIABILITY (ADJ)", "#3a8fb5"), width='stretch')
    with g3: st.plotly_chart(gauge_chart(row['Reputability_Adj'], "REPUTABILITY (ADJ)", "#9b5fcf"), width='stretch')
    
    st.markdown(score_explanation_html(), unsafe_allow_html=True)
    st.markdown(growth_stage_focus_html(), unsafe_allow_html=True)

    # Stage Profile & Radar
    st.markdown(section_header("02", "Growth Stage Profile"), unsafe_allow_html=True)
    col_a, col_b = st.columns([1.2, 1])
    with col_a: st.markdown(stage_bar_html(row), unsafe_allow_html=True)
    with col_b: st.plotly_chart(radar_chart(row), width='stretch')

    # Footer
    st.markdown("""
    <hr>
    <div style='margin-top: 2rem; font-family: DM Mono, monospace; font-size: 0.65rem; color: #888880; letter-spacing: 0.1em; text-transform: uppercase; text-align: center;'>
        R-Cube Screening Metric · Strategic Intelligence
    </div>
    """, unsafe_allow_html=True)
