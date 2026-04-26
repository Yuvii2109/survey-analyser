import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import base64
import io
import sys
import asyncio
import warnings
import os
import json
import re
from pathlib import Path
import requests

try:
    from google import genai
except Exception:
    genai = None

try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None

try:
    from fpdf import FPDF
    from fpdf.enums import XPos, YPos
except Exception:
    FPDF = None
    XPos = None
    YPos = None

@st.cache_resource
def install_playwright():
    """Forces the Streamlit server to download the Chromium binary and dependencies on boot."""
    os.system("playwright install chromium")

# ─────────────────────────────────────────────
#  WINDOWS EVENT LOOP FIX (MUST COME FIRST)
# ─────────────────────────────────────────────
if sys.platform == "win32":
    # Mute the Python 3.14+ deprecation warnings to keep the console clean
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=DeprecationWarning)
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        except AttributeError:
            pass # Failsafe just in case it gets fully removed in a future test build

from playwright.sync_api import sync_playwright
import plotly.io as pio
from plotly.offline import get_plotlyjs

APP_PAGE_CONFIG = dict(
    page_title="R-Cube Strategic Intelligence",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)


def load_local_env(env_path: str = ".env") -> None:
    if load_dotenv is not None:
        load_dotenv(env_path)
        return

    path = Path(env_path)
    if not path.exists():
        return

    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


load_local_env()

GENERATED_PDF_DIR = Path("generated_pdfs")
 
# ─────────────────────────────────────────────
#  CUSTOM CSS
# ─────────────────────────────────────────────
CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');
 
/* Reset & Base */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}
.stApp {
    background: #f8fafc;
    color: #0f172a;
}
 
/* Sidebar */
[data-testid="stSidebar"] {
    background: #ffffff !important;
    border-right: 1px solid #e2e8f0;
}
[data-testid="stSidebar"] * { color: #334155 !important; }
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 { color: #0f172a !important; }
 
/* Main headings */
h1, h2, h3 { font-family: 'Playfair Display', serif !important; color: #0f172a !important; }
 
/* Hide Streamlit chrome */
#MainMenu, footer{ visibility: hidden; }
.block-container { padding-top: 2rem; padding-bottom: 2rem; }
 
/* ── KPI Cards ── */
.kpi-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    border-radius: 12px;
    padding: 1.5rem 1.75rem;
    position: relative;
    overflow: hidden;
}
.kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 4px;
}
.kpi-card.relevance::before  { background: #d97706; }
.kpi-card.reliability::before { background: #2563eb; }
.kpi-card.reputability::before { background: #7c3aed; }
.kpi-card.growth::before { background: #059669; }
.kpi-card.growth { text-align: center; }
.kpi-card.growth .kpi-label,
.kpi-card.growth .kpi-value,
.kpi-card.growth .kpi-band {
    margin-left: auto;
    margin-right: auto;
}
 
.kpi-label { font-family: 'DM Mono', monospace; font-size: 0.65rem; letter-spacing: 0.2em; text-transform: uppercase; color: #64748b; margin-bottom: 0.5rem; }
.kpi-value { font-family: 'Playfair Display', serif; font-size: 5.2rem; font-weight: 900; line-height: 1; margin-bottom: 0.3rem; }
.kpi-value.relevance  { color: #b45309; }
.kpi-value.reliability { color: #1d4ed8; }
.kpi-value.reputability { color: #6d28d9; }
.kpi-value.growth { color: #047857; }
 
.kpi-band { font-size: 0.72rem; font-weight: 600; letter-spacing: 0.05em; padding: 2px 8px; border-radius: 4px; display: inline-block; margin-top: 0.25rem; }
.band-fragile     { background: #fef2f2; color: #dc2626; }
.band-emerging    { background: #fffbeb; color: #d97706; }
.band-developing  { background: #f0fdf4; color: #16a34a; }
.band-strong      { background: #eff6ff; color: #2563eb; }
.band-benchmark   { background: #faf5ff; color: #9333ea; }
 
/* ── Stage Bar ── */
.stage-bar-wrap { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 1.5rem; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02); height: 100%; }
.stage-profile-offset { margin-top: 44px; }
.stage-row { display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem; }
.stage-label { font-family: 'DM Mono', monospace; font-size: 0.65rem; letter-spacing: 0.15em; text-transform: uppercase; color: #475569; width: 130px; }
.stage-track { flex: 1; height: 8px; background: #f1f5f9; border-radius: 4px; }
.stage-fill { height: 100%; border-radius: 4px; }
.stage-val { font-family: 'DM Mono', monospace; font-size: 0.8rem; color: #0f172a; font-weight: 600; }
 
/* ── Status Badge ── */
.status-badge { display: inline-flex; align-items: center; gap: 0.6rem; padding: 0.7rem 1.45rem; border-radius: 10px; font-family: 'DM Mono', monospace; font-size: 0.95rem; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; }
.badge-benchmark  { background: #faf5ff; border: 1px solid #c084fc; color: #7e22ce; }
.badge-fragile    { background: #fef2f2; border: 1px solid #f87171; color: #b91c1c; }
.badge-efficient  { background: #f0fdf4; border: 1px solid #4ade80; color: #15803d; }
.badge-legacy     { background: #f0fdfa; border: 1px solid #2dd4bf; color: #0f766e; }
.badge-default    { background: #f8fafc; border: 1px solid #cbd5e1; color: #334155; }
.badge-desc { font-size: 1.05rem; color: #0f172a; font-weight: 700; }
.status-row { display: flex; align-items: center; flex-wrap: nowrap; gap: 0.8rem; margin-top: 1.25rem; }
 
/* ── Section headers ── */
.section-header { border-bottom: 2px solid #e2e8f0; padding-bottom: 0.5rem; margin-bottom: 1.5rem; }
.section-number { color: #94a3b8; font-family: 'DM Mono', monospace; font-weight: 600; }
.section-title { color: #0f172a; font-family: 'Playfair Display', serif; font-weight: 700; font-size: 1.5rem; margin-left: 0.5rem; }
 
/* ── Score Explanation ── */
.explain-wrap { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 14px; padding: 1.5rem; margin-bottom: 1rem; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02); }
.explain-head { font-family: 'Playfair Display', serif; font-size: 1.6rem; font-weight: 900; color: #0f172a; line-height: 1.2; margin-bottom: 0.3rem; }
.explain-sub { font-family: 'DM Mono', monospace; font-size: 0.66rem; letter-spacing: 0.14em; text-transform: uppercase; color: #64748b; margin-bottom: 1.2rem; }
.explain-grid { display: grid; grid-template-columns: repeat(3, minmax(180px, 1fr)); gap: 1rem; }
.explain-card { background: #f8fafc; border: 1px solid #f1f5f9; border-radius: 10px; padding: 1rem; }
.explain-card h4 { margin: 0 0 0.6rem 0; font-family: 'DM Mono', monospace; letter-spacing: 0.08em; font-size: 0.75rem; text-transform: uppercase; font-weight: 600; }
.exp-rel h4 { color: #d97706; }
.exp-reli h4 { color: #2563eb; }
.exp-repu h4 { color: #7c3aed; }
.explain-card ul { margin: 0; padding-left: 1rem; color: #334155; font-size: 0.9rem; line-height: 1.6; }
@media (max-width: 980px) { .explain-grid { grid-template-columns: 1fr; } }

/* ── Growth Stage Focus Table ── */
.focus-wrap { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 14px; padding: 1.5rem; margin-bottom: 1rem; overflow-x: auto; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02); }
.focus-title { font-family: 'Playfair Display', serif; font-size: 1.5rem; font-weight: 900; color: #0f172a; margin-bottom: 1rem; }
.focus-table { width: 100%; border-collapse: collapse; min-width: 860px; }
.focus-table th, .focus-table td { border: 1px solid #e2e8f0; padding: 0.75rem; vertical-align: top; color: #334155; line-height: 1.4; font-size: 0.9rem; }
.focus-table th { background: #f8fafc; font-family: 'DM Mono', monospace; font-size: 0.75rem; letter-spacing: 0.08em; text-transform: uppercase; color: #0f172a; }
.focus-stage { font-family: 'DM Mono', monospace; font-size: 0.75rem; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; white-space: nowrap; background: #f1f5f9; }

/* Divider */
hr { border-color: #e2e8f0 !important; }
"""

# ─────────────────────────────────────────────
#  CONSTANTS
# ─────────────────────────────────────────────
RESPONSE_MAP = {
    "Completely disagree": 1, "Disagree": 2,
    "Don't Know, Can't Say": 3, "don't know ,can't say": 3,
    "Don’t Know, Can’t Say": 3,  # Added to handle CSV export typography
    "Agree": 4, "Completely agree": 5, "Completely Agree": 5,
}
 
BAND_LABELS = {
    (0, 40):  ("Fragile",          "band-fragile"),
    (40, 60): ("Emerging",         "band-emerging"),
    (60, 75): ("Developing",       "band-developing"),
    (75, 90): ("Strong",           "band-strong"),
    (90, 101):("Benchmark",        "band-benchmark"),
}

PLOTLY_THEME = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="DM Sans", color="#334155", size=11),
    margin=dict(l=20, r=20, t=40, b=20),
)
 
# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────
def get_band(score):
    for (lo, hi), (label, css) in BAND_LABELS.items():
        if lo <= score < hi: return label, css
    return "Benchmark", "band-benchmark"

def fig_to_html(fig, w, h):
    """Converts a Plotly figure to an embeddable HTML string."""
    fig.update_layout(width=w, height=h, margin=dict(l=0, r=0, t=30, b=0)) # Tighten margins
    return fig.to_html(full_html=False, include_plotlyjs=False)

def fig_to_b64(fig, w, h):
    """Converts a Plotly figure to a base64 encoded PNG string."""
    img_bytes = fig.to_image(format="png", width=w, height=h, scale=2)
    return base64.b64encode(img_bytes).decode('utf-8')

def get_strategic_profile(row):
    gi = row['Growth_Index']
    rel  = row['Relevance']
    reli = row['Reliability_Adj']
    repu = row['Reputability_Adj']
 
    if gi >= 85: return "🏆 Benchmark Institution", "badge-benchmark", "Market leader and legacy institution setting the standard for peers."
    if rel > 70 and reli < 50: return "⚡ Fragile Starter", "badge-fragile", "Strong vision and relevance, but operational systems are failing to match ambition."
    if reli > 70 and rel < 50: return "⚙️ Efficient Machine", "badge-efficient", "Consistent delivery and strong systems, but at risk of becoming obsolete."
    if reli > 60 and repu > 60: return "📜 Legacy Builder", "badge-legacy", "Strong operational systems and actively building long-term market authority."
    if gi < 40: return "🛑 Fragile Foundation", "badge-fragile", "Immediate intervention required — core foundations are critically weak."
    return "🌱 Emerging", "badge-default", "Moving out of survival phase and stabilising core operations."
 
# ─────────────────────────────────────────────
#  SCORING ENGINE
# ─────────────────────────────────────────────
def calculate_metrics(df):
    df = df.copy()
    for i in [1, 2, 3, 4, 5]:
        df[f'S{i}'] = (5 - df[f'Q{i}']) * 25
    for i in range(6, 21):
        df[f'S{i}'] = (df[f'Q{i}'] - 1) * 25
 
    df['Relevance'] = df[['S1', 'S2', 'S5', 'S11', 'S13', 'S14']].mean(axis=1)
    df['Rel_Raw'] = df[['S3', 'S4', 'S6', 'S7', 'S8', 'S9', 'S10', 'S12', 'S14', 'S15']].mean(axis=1)
    df['Rep_Raw'] = df[['S16', 'S17', 'S18', 'S19', 'S20']].mean(axis=1)
 
    df['Reliability_Adj']   = df['Rel_Raw'] * (0.75 + 0.25 * df['Relevance'] / 100)
    min_floor               = df[['Relevance', 'Reliability_Adj']].min(axis=1)
    df['Reputability_Adj']  = df['Rep_Raw'] * (0.60 + 0.40 * min_floor / 100)
 
    df['Foundation']    = df[[f'Q{i}' for i in range(1, 6)]].mean(axis=1)
    df['Growth']        = df[[f'Q{i}' for i in range(6, 11)]].mean(axis=1)
    df['Acceleration']  = df[[f'Q{i}' for i in range(11, 16)]].mean(axis=1)
    df['Legacy']        = df[[f'Q{i}' for i in range(16, 21)]].mean(axis=1)
 
    df['Growth_Index'] = (0.35 * df['Relevance'] + 0.40 * df['Reliability_Adj'] + 0.25 * df['Reputability_Adj'])
    return df


def prepare_results(raw):
    raw = raw.copy()
    q_cols = raw.columns[8:28]
    raw = raw.rename(columns={q_cols[i]: f'Q{i+1}' for i in range(len(q_cols))})

    if 'name' in raw.columns:
        raw_names = raw['name'].fillna("Unknown").astype(str).tolist()
    else:
        try:
            raw_names = raw.iloc[:, 29].fillna("Unknown").astype(str).tolist()
        except IndexError:
            raw_names = [f"User {i+1}" for i in range(len(raw))]

    display_names = [name.title().strip() for name in raw_names]

    unique_ids = []
    seen = {}
    for name in display_names:
        if name in seen:
            seen[name] += 1
            unique_ids.append(f"{name} ({seen[name]})")
        else:
            seen[name] = 1
            unique_ids.append(name)

    raw.insert(0, 'UserID', unique_ids)
    raw.insert(1, 'Display_Name', display_names)

    for i in range(1, 21):
        raw[f'Q{i}'] = raw[f'Q{i}'].map(RESPONSE_MAP).fillna(3)

    return calculate_metrics(raw)


def find_column_name(df, candidates):
    normalized = {str(col).strip().lower(): col for col in df.columns}
    for candidate in candidates:
        match = normalized.get(candidate.strip().lower())
        if match is not None:
            return match
    return None


def build_pdf_filename(name):
    safe_name = "_".join(str(name or "Participant").split())
    return f"RCube_Report_{safe_name}.pdf"


def get_row_contact_details(raw, results, user_id):
    match = results[results["UserID"] == user_id]
    if match.empty:
        return {"email": "", "name": user_id}

    result_index = match.index[0]
    source_row = raw.iloc[result_index]
    email_col = find_column_name(raw, ["email", "email address", "email_address", "mail"])
    name_col = find_column_name(raw, ["name", "full name", "full_name", "participant name"])

    email = ""
    if email_col is not None:
        value = source_row[email_col]
        email = "" if pd.isna(value) else str(value).strip()
    elif len(source_row) > 2:
        value = source_row.iloc[2]
        email = "" if pd.isna(value) else str(value).strip()

    display_name = match.iloc[0]["Display_Name"]
    if name_col is not None:
        value = source_row[name_col]
        name = display_name if pd.isna(value) else str(value).strip()
    elif len(source_row) > 29:
        value = source_row.iloc[29]
        name = display_name if pd.isna(value) else str(value).strip()
    else:
        name = display_name

    return {"email": email, "name": name}


def ensure_generated_pdf_dir(library_key=None):
    GENERATED_PDF_DIR.mkdir(exist_ok=True)
    if library_key:
        path = GENERATED_PDF_DIR / library_key
        path.mkdir(exist_ok=True)
        return path
    return GENERATED_PDF_DIR


def build_library_key(file_name, file_bytes):
    import hashlib

    digest = hashlib.sha1(file_bytes).hexdigest()[:12]
    safe_name = "".join(ch if ch.isalnum() else "-" for ch in str(file_name or "uploaded-list").lower()).strip("-")
    safe_name = safe_name[:40] or "uploaded-list"
    return f"{safe_name}-{digest}"


def get_library_paths(library_key):
    library_dir = ensure_generated_pdf_dir(library_key)
    return library_dir, library_dir / "index.json"


def load_generated_pdf_library(library_key):
    _, index_path = get_library_paths(library_key)
    if not index_path.exists():
        return {}

    try:
        records = json.loads(index_path.read_text())
    except Exception:
        return {}

    library = {}
    for user_id, record in records.items():
        file_path = record.get("file_path", "")
        if file_path and Path(file_path).exists():
            library[user_id] = record
    return library


def persist_generated_pdf_library(library, library_key):
    serializable = {}
    for user_id, record in library.items():
        serializable[user_id] = {
            "file_name": record["file_name"],
            "file_path": record["file_path"],
            "email": record.get("email", ""),
            "name": record.get("name", user_id),
        }
    _, index_path = get_library_paths(library_key)
    index_path.write_text(json.dumps(serializable, indent=2))


def save_generated_pdf_record(user_id, file_name, pdf_bytes, library_key, email="", name=""):
    library_dir, _ = get_library_paths(library_key)
    file_path = library_dir / file_name
    file_path.write_bytes(pdf_bytes)
    return {
        "file_name": file_name,
        "file_path": str(file_path.resolve()),
        "email": email,
        "name": name or user_id,
    }


def clear_generated_pdf_library(library_key):
    library_dir, index_path = get_library_paths(library_key)
    if library_dir.exists():
        for item in library_dir.iterdir():
            if item.is_file():
                item.unlink()
    index_path.write_text("{}")


def render_generated_pdf_library(container):
    with container.container():
        if not st.session_state.generated_pdfs:
            st.info("No PDFs have been generated yet for this uploaded list.")
            return

        st.markdown(section_header("04", "Generated PDFs"), unsafe_allow_html=True)
        st.caption(f"Saved for this uploaded list: {len(st.session_state.generated_pdfs)}")
        for pdf_user, pdf_info in st.session_state.generated_pdfs.items():
            label_col, download_col, send_col = st.columns([1.4, 1, 1])
            with label_col:
                st.markdown(
                    f"""
                    <div class="explain-wrap" style="margin-bottom: 0.75rem;">
                        <div class="explain-sub">Generated Report</div>
                        <div style="font-size:1rem; color:#0f172a; font-weight:700;">{pdf_user}</div>
                        <div style="font-size:0.9rem; color:#64748b; margin-top:0.35rem;">{pdf_info['file_name']}</div>
                        <div style="font-size:0.85rem; color:#64748b; margin-top:0.25rem;">{pdf_info.get('email', 'No email found')}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with download_col:
                st.download_button(
                    label="Download Report",
                    data=Path(pdf_info["file_path"]).read_bytes(),
                    file_name=pdf_info["file_name"],
                    mime="application/pdf",
                    use_container_width=True,
                    key=f"download_{pdf_user}",
                )
            with send_col:
                send_disabled = not pdf_info.get("email")
                if st.button(
                    "Send Email",
                    use_container_width=True,
                    key=f"send_{pdf_user}",
                    disabled=send_disabled,
                ):
                    try:
                        from send_pending_reports import send_email_with_attachment

                        response = send_email_with_attachment(
                            email=pdf_info["email"],
                            name=pdf_info.get("name", pdf_user),
                            file_name=pdf_info["file_name"],
                            file_bytes=Path(pdf_info["file_path"]).read_bytes(),
                        )
                        if response.status_code in (200, 201):
                            st.success(f"Sent {pdf_user} to {pdf_info['email']}")
                        else:
                            st.error(
                                f"Failed for {pdf_user} ({response.status_code}): {response.text[:200]}"
                            )
                    except Exception as e:
                        st.error(f"Send failed for {pdf_user}: {e}")


PRE_ASSESSMENT_KEY = {
    "Mental health is best understood as:": "emotional, social, and psychological well-being",
    "Which is a common source of stress for students today?": "academic demands, peer pressure, and family expectations",
    "Which is the clearest early warning sign a teacher may observe?": "showing sudden withdrawal over several days",
    "A student who is usually cheerful has become quiet, avoids friends, and has stopped submitting work. What should the teacher do first?": "watch the pattern and speak privately",
    "Which classroom practice is most likely to improve emotional safety?": "using respectful language and encouragement",
    "Before a test, a student says, \"I know I will not do well.\" What is the most helpful immediate teacher response?": "guide the student to begin with familiar questions",
    "Which approach is most appropriate while talking to parents about a concern?": "sharing observations and inviting partnership",
    "Which action should a teacher avoid when concerned about a student?": "deciding on a diagnosis from classroom signs",
    "Which assessment practice is most likely to reduce student stress?": "offering clear success criteria in advance",
    "One student is irritable, one is withdrawn, and one frequently reports headaches before tests. What is the best interpretation?": "they are showing possible signs of stress",
    "A teacher notices repeated emotional distress even after classroom support. What is the best next step?": "move the concern through school support channels",
    "Which statement best reflects a mentally healthy school culture?": "academic progress depends on emotional safety",
}

POST_ASSESSMENT_KEY = {
    "Good mental health in students is best reflected when they:": "manage emotions and function reasonably well",
    "Which description best matches burnout?": "exhaustion, detachment, and reduced motivation",
    "Which factor is most closely linked to healthy student development in school?": "consistent adult support and connection",
    "A student who usually participates well has stopped answering and avoids eye contact. What is the most appropriate first response?": "observe carefully and check in privately",
    "Which classroom practice best supports student emotional safety?": "acknowledging effort in a respectful way",
    "A teacher wants to speak to parents about a student's recent change in behaviour. Which opening is best?": "We have noticed some changes and want to support together.",
    "Which is the best example of a healthy teacher response to student stress?": "acknowledging the feeling and offering calm guidance",
    "Which assessment practice best supports student well-being?": "giving clear criteria and calm instructions",
    "A teacher notices one student becomes restless before tests, one becomes silent during group work, and one often says, \"I cannot do this.\" What is the best next move?": "respond to each pattern with appropriate support",
    "A school wants to become more mentally healthy. Which change is likely to have the strongest everyday effect?": "combining supportive teaching with referral systems",
    "A teacher has supported a student in class, checked in privately, and still sees persistent distress. What should the teacher conclude?": "the concern may need referral support",
    "Which statement best reflects the spirit of the workshop?": "teachers support mental health through daily practice",
}


def normalize_string(s):
    return re.sub(r"[^a-zA-Z0-9]", "", str(s)).lower()


def get_matched_column(df, question):
    q_clean = normalize_string(question)[:25]
    for col in df.columns:
        if q_clean in normalize_string(col):
            return col
    return None


@st.cache_data(ttl=300)
def fetch_google_sheet_data(url):
    try:
        if "export?format=csv" not in url:
            match = re.search(r"/d/([a-zA-Z0-9-_]+)", url)
            if match:
                doc_id = match.group(1)
                url = f"https://docs.google.com/spreadsheets/d/{doc_id}/export?format=csv"
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        return pd.read_csv(io.StringIO(response.text))
    except Exception as e:
        st.error(f"Failed to fetch data from Google Sheets: {e}")
        return None


def filter_out_unicode_responses(df):
    if df is None or df.empty:
        return df
    filtered = df.copy()
    keep_mask = pd.Series(True, index=filtered.index)
    for idx, col in enumerate(list(filtered.columns)):
        series = filtered.iloc[:, idx]
        if series.dtype == object:
            keep_mask &= series.apply(
                lambda x: pd.isna(x) or all(ord(c) < 128 for c in str(x))
            )
    return filtered.loc[keep_mask].copy()


@st.cache_data(ttl=3600, show_spinner=False)
def build_dynamic_answer_mapping(df, base_answer_key, current_api_key):
    if genai is None or not current_api_key:
        return {question: [concept] for question, concept in base_answer_key.items()}

    client = genai.Client(api_key=current_api_key)
    dynamic_key = {}
    payload_to_grade = {}

    for question, correct_concept in base_answer_key.items():
        matched_col = get_matched_column(df, question)
        if not matched_col:
            dynamic_key[question] = [correct_concept]
            continue
        unique_responses = []
        for val in df[matched_col].dropna().astype(str):
            for v in val.split(","):
                candidate = v.strip()
                if candidate and candidate not in unique_responses:
                    unique_responses.append(candidate)
        payload_to_grade[question] = {
            "correct_concept": correct_concept,
            "user_responses": unique_responses,
        }

    prompt = (
        "You are a survey grading assistant. For each question, identify which user responses "
        "mean the same thing as the correct concept. Return raw JSON only.\n\n"
        f"{json.dumps(payload_to_grade, ensure_ascii=False)}"
    )

    try:
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        text = response.text.strip()
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            text = match.group(0)
        approved_answers_dict = json.loads(text)
        for question, correct_concept in base_answer_key.items():
            approved = approved_answers_dict.get(question, [])
            dynamic_key[question] = [correct_concept] + (approved if isinstance(approved, list) else [])
    except Exception:
        for question, correct_concept in base_answer_key.items():
            dynamic_key.setdefault(question, [correct_concept])

    return dynamic_key


def apply_grid(fig):
    fig.update_layout(
        plot_bgcolor="white",
        xaxis=dict(showgrid=True, gridwidth=1, gridcolor="LightGray", zeroline=True, zerolinecolor="LightGray"),
        yaxis=dict(showgrid=True, gridwidth=1, gridcolor="LightGray", zeroline=True, zerolinecolor="LightGray"),
    )
    return fig


def get_question_metrics(df, dynamic_answer_key, base_answer_key):
    metrics = []
    total_responses = len(df)
    for i, (question, correct_answers) in enumerate(dynamic_answer_key.items()):
        matched_col = get_matched_column(df, question)
        accuracy = 0
        hover_str = f"<b>{question}</b><br><br><b>Target Concept:</b> <span style='color:#2ca02c;'>{base_answer_key.get(question, 'N/A')}</span>"
        if matched_col:
            correct_count = df[matched_col].astype(str).apply(
                lambda x: 1 if any(ans.lower() in x.lower() for ans in correct_answers) else 0
            ).sum()
            accuracy = (correct_count / total_responses) * 100 if total_responses > 0 else 0
        metrics.append(
            {
                "Question": question,
                "Question_Short": f"Q{i+1}",
                "Accuracy (%)": accuracy,
                "Hover_Data": hover_str,
            }
        )
    return pd.DataFrame(metrics)


def get_participant_scores(df, dynamic_answer_key):
    scores = []
    for _, row in df.iterrows():
        correct = 0
        for question, correct_answers in dynamic_answer_key.items():
            matched_col = get_matched_column(df, question)
            if matched_col and pd.notna(row[matched_col]):
                if any(ans.lower() in str(row[matched_col]).lower() for ans in correct_answers):
                    correct += 1
        scores.append(correct)
    return scores


def generate_graded_dataframe(df, dynamic_answer_key):
    graded_data = []
    for index, row in df.iterrows():
        participant_data = {"Participant_ID": f"Participant {index + 1}"}
        total_score = 0
        for i, (question, correct_answers) in enumerate(dynamic_answer_key.items()):
            q_short = f"Q{i+1}"
            matched_col = get_matched_column(df, question)
            is_correct = 0
            if matched_col and pd.notna(row[matched_col]):
                if any(ans.lower() in str(row[matched_col]).lower() for ans in correct_answers):
                    is_correct = 1
            participant_data[q_short] = is_correct
            total_score += is_correct
        participant_data["Total_Score"] = total_score
        graded_data.append(participant_data)
    return pd.DataFrame(graded_data)


def normalize_phone(value):
    digits = re.sub(r"\D", "", str(value or ""))
    if len(digits) > 10:
        digits = digits[-10:]
    return digits


def find_phone_column(df):
    return find_column_name(
        df,
        [
            "phone",
            "phone number",
            "mobile",
            "mobile number",
            "contact number",
            "whatsapp number",
        ],
    )


def find_name_column_for_comparison(df):
    return find_column_name(df, ["name", "full name", "participant name", "teacher name"])


def generate_individual_graded_dataframe(df, dynamic_answer_key):
    graded_df = generate_graded_dataframe(df, dynamic_answer_key)
    phone_col = find_phone_column(df)
    name_col = find_name_column_for_comparison(df)

    graded_df["Phone"] = (
        df[phone_col].apply(normalize_phone) if phone_col is not None else pd.Series([""] * len(df))
    )
    graded_df["Name"] = (
        df[name_col].fillna("Participant").astype(str).str.strip()
        if name_col is not None
        else pd.Series([f"Participant {i + 1}" for i in range(len(df))])
    )
    return graded_df


def generate_gemini_insights(pre_data, post_data, current_api_key):
    if genai is None or not current_api_key:
        return "Gemini is not configured. Add `GEMINI_API_KEY` to use AI insights."

    client = genai.Client(api_key=current_api_key)
    prompt = """
You are a Senior AI Data Analyst evaluating a teacher mental health training program.
Generate a highly skimmable professional report using these exact markdown headers:

### Attendee-Facing Highlights (Public)
### Presenter Internal Record: Data Trajectory (Private)
### Deep Dive: Critical Knowledge Gaps (Private)
### Strategic Action Plan (Private)
"""
    if pre_data:
        prompt += f"\nPre-Webinar Accuracy:\n{pre_data}\n"
    if post_data:
        prompt += f"\nPost-Webinar Accuracy:\n{post_data}\n"
    try:
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        return response.text
    except Exception as e:
        return f"Error generating insights: {e}"


def create_insights_pdf(report_text):
    if FPDF is None:
        return None
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, "Teacher Mental Health Training - Insights Report", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.ln(10)
    replacements = {"**": "", "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"', "\u2013": "-", "\u2014": "-", "\u2022": "-", "*": "-", "\t": " "}
    clean_text = report_text
    for old, new in replacements.items():
        clean_text = clean_text.replace(old, new)
    clean_text = clean_text.encode("latin-1", "ignore").decode("latin-1")
    pdf.set_font("helvetica", "", 12)
    for line in clean_text.split("\n"):
        line = line.strip()
        if not line or set(line) <= {"-", "_", " "}:
            pdf.ln(4)
            continue
        if line.startswith("### "):
            pdf.ln(4)
            pdf.set_font("helvetica", "B", 14)
            pdf.write(10, line.replace("### ", "") + "\n")
            pdf.set_font("helvetica", "", 12)
        else:
            pdf.write(8, line + "\n")
    return bytes(pdf.output())


def render_comparison_report():
    st.title("Pre/Post Comparison Report")
    st.markdown("Compare pre and post survey responses for each individual, matched by phone number.")

    api_key = os.getenv("GEMINI_API_KEY")
    with st.sidebar:
        st.markdown("---")
        st.markdown("`Comparison Inputs`")
        pre_file = st.file_uploader(
            "Upload Pre Survey CSV",
            type=["csv"],
            key="comparison_pre_csv",
        )
        post_file = st.file_uploader(
            "Upload Post Survey CSV",
            type=["csv"],
            key="comparison_post_csv",
        )
        generate_comparison_report = st.button(
            "Generate Comparison Report",
            type="primary",
            use_container_width=True,
        )
        st.markdown("---")
        st.markdown("`Comparison Status`")
        st.caption(f"Gemini: {'Configured' if api_key else 'Missing'}")
        st.caption(f"Pre CSV: {'Uploaded' if pre_file is not None else 'Waiting'}")
        st.caption(f"Post CSV: {'Uploaded' if post_file is not None else 'Waiting'}")

    if generate_comparison_report:
        st.session_state["comparison_process_clicked"] = True

    if not st.session_state.get("comparison_process_clicked", False):
        return

    if pre_file is None and post_file is None:
        st.warning("Upload at least one CSV file for pre or post survey data.")
        return

    pre_df = post_df = None
    pre_raw_count = post_raw_count = 0

    with st.spinner("Reading uploaded CSV files..."):
        if pre_file is not None:
            pre_source_df = pd.read_csv(io.BytesIO(pre_file.getvalue()))
            pre_raw_count = len(pre_source_df)
            pre_df = filter_out_unicode_responses(pre_source_df)
        if post_file is not None:
            post_source_df = pd.read_csv(io.BytesIO(post_file.getvalue()))
            post_raw_count = len(post_source_df)
            post_df = filter_out_unicode_responses(post_source_df)

    status_col1, status_col2 = st.columns(2)
    with status_col1:
        st.caption(
            f"Pre CSV rows: raw {pre_raw_count}, usable {0 if pre_df is None else len(pre_df)}"
        )
    with status_col2:
        st.caption(
            f"Post CSV rows: raw {post_raw_count}, usable {0 if post_df is None else len(post_df)}"
        )

    if pre_file is None or post_file is None:
        st.warning("Upload both pre and post CSV files to generate an individual comparison report.")
        return

    if pre_df is None or pre_df.empty:
        st.warning("The uploaded pre CSV has no usable rows after cleaning.")
        return

    if post_df is None or post_df.empty:
        st.warning("The uploaded post CSV has no usable rows after cleaning.")
        return

    with st.spinner("Analyzing pre and post survey responses..."):
        dynamic_pre_key = build_dynamic_answer_mapping(pre_df, PRE_ASSESSMENT_KEY, api_key)
        dynamic_post_key = build_dynamic_answer_mapping(post_df, POST_ASSESSMENT_KEY, api_key)
        pre_graded_df = generate_individual_graded_dataframe(pre_df, dynamic_pre_key)
        post_graded_df = generate_individual_graded_dataframe(post_df, dynamic_post_key)

    matched_phones = sorted(
        {
            phone
            for phone in pre_graded_df["Phone"].tolist()
            if phone and phone in set(post_graded_df["Phone"].tolist())
        }
    )

    if not matched_phones:
        st.error("No matching individuals were found between pre and post CSVs using phone number.")
        return

    participant_options = []
    for phone in matched_phones:
        pre_row = pre_graded_df[pre_graded_df["Phone"] == phone].iloc[0]
        name = pre_row["Name"] or "Participant"
        participant_options.append(f"{name} ({phone})")

    selected_participant = st.selectbox("Select Individual Comparison Report", participant_options)
    selected_phone = re.search(r"\((\d+)\)$", selected_participant).group(1)
    pre_row = pre_graded_df[pre_graded_df["Phone"] == selected_phone].iloc[0]
    post_row = post_graded_df[post_graded_df["Phone"] == selected_phone].iloc[0]
    participant_name = pre_row["Name"] or post_row["Name"] or "Participant"

    st.header(participant_name)
    stat1, stat2, stat3 = st.columns(3)
    stat1.metric("Phone", selected_phone)
    stat2.metric("Pre Score", f"{int(pre_row['Total_Score'])} / 12")
    stat3.metric("Post Score", f"{int(post_row['Total_Score'])} / 12", delta=int(post_row["Total_Score"] - pre_row["Total_Score"]))

    question_rows = []
    for i in range(1, 13):
        q_key = f"Q{i}"
        question_rows.append(
            {
                "Question": q_key,
                "Pre": int(pre_row[q_key]),
                "Post": int(post_row[q_key]),
            }
        )
    comparison_df = pd.DataFrame(question_rows)
    comparison_long = comparison_df.melt(id_vars="Question", value_vars=["Pre", "Post"], var_name="Survey", value_name="Correct")
    fig_compare = px.bar(
        comparison_long,
        x="Question",
        y="Correct",
        color="Survey",
        barmode="group",
        color_discrete_map={"Pre": "#1f77b4", "Post": "#2ca02c"},
        title="Pre/Post Individual Question Comparison",
    )
    fig_compare.update_yaxes(range=[0, 1], tickvals=[0, 1], ticktext=["Incorrect", "Correct"])
    st.plotly_chart(apply_grid(fig_compare), width="stretch")

    detail_df = pd.DataFrame(
        {
            "Question": [f"Q{i}" for i in range(1, 13)],
            "Pre": [int(pre_row[f"Q{i}"]) for i in range(1, 13)],
            "Post": [int(post_row[f"Q{i}"]) for i in range(1, 13)],
        }
    )
    st.subheader("Question Detail")
    st.dataframe(detail_df, width="stretch")

    insights_text = (
        f"### Individual Comparison Summary\n"
        f"- Participant: {participant_name}\n"
        f"- Phone: {selected_phone}\n"
        f"- Pre score: {int(pre_row['Total_Score'])}/12\n"
        f"- Post score: {int(post_row['Total_Score'])}/12\n"
        f"- Improvement: {int(post_row['Total_Score'] - pre_row['Total_Score'])}\n\n"
        f"### Question-by-Question Shift\n"
        + "\n".join(
            f"- Q{i}: Pre {int(pre_row[f'Q{i}'])}, Post {int(post_row[f'Q{i}'])}"
            for i in range(1, 13)
        )
    )

    st.subheader("Report Summary")
    st.markdown(insights_text)
    insights_pdf = create_insights_pdf(insights_text)
    if insights_pdf:
        st.download_button(
            "Download Individual Comparison Report (PDF)",
            insights_pdf,
            f"{participant_name.replace(' ', '_')}_comparison_report.pdf",
            "application/pdf",
            use_container_width=True,
        )

# ─────────────────────────────────────────────
#  CHART BUILDERS
# ─────────────────────────────────────────────
def radar_chart(row):
    cats  = ['Foundation', 'Growth', 'Acceleration', 'Legacy']
    vals  = [row[c] for c in cats]
 
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=vals + [vals[0]], theta=cats + [cats[0]], fill='toself',
        fillcolor='rgba(37, 99, 235, 0.15)', line=dict(color='#2563eb', width=2),
        name='Profile', hovertemplate='%{theta}: %{r:.2f}<extra></extra>',
    ))
    bench = [4, 4, 4, 4]
    fig.add_trace(go.Scatterpolar(
        r=bench + [bench[0]], theta=cats + [cats[0]], line=dict(color='#94a3b8', width=1.5, dash='dash'),
        mode='lines', name='Benchmark ref', hoverinfo='skip',
    ))
    fig.update_layout(
        **PLOTLY_THEME,
        polar=dict(
            bgcolor='rgba(248, 250, 252, 0.8)',
            radialaxis=dict(visible=True, range=[0, 5], color='#64748b', gridcolor='#e2e8f0', tickfont=dict(size=9, color='#64748b')),
            angularaxis=dict(color='#475569', gridcolor='#e2e8f0'),
        ), showlegend=False, height=320,
    )
    return fig
 
def gauge_chart(value, title, color):
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=value,
        number=dict(font=dict(family="Playfair Display", size=36, color=color), suffix="", valueformat=".1f"),
        gauge=dict(
            axis=dict(range=[0, 100], tickwidth=0, tickcolor='rgba(0,0,0,0)', visible=False),
            bar=dict(color=color, thickness=0.65), bgcolor='rgba(0,0,0,0)', borderwidth=0,
            steps=[
                dict(range=[0, 40],  color='rgba(220, 38, 38, 0.1)'), dict(range=[40, 60], color='rgba(217, 119, 6, 0.1)'),
                dict(range=[60, 75], color='rgba(37, 99, 235, 0.1)'), dict(range=[75, 90], color='rgba(5, 150, 105, 0.1)'),
                dict(range=[90, 100],color='rgba(124, 58, 237, 0.1)'),
            ],
            threshold=dict(line=dict(color='#94a3b8', width=2), thickness=0.8, value=75),
        ),
    ))
    fig.update_layout(**PLOTLY_THEME, height=200, title=dict(text=title, font=dict(size=11, family='DM Mono', color='#475569', weight="bold"), x=0.5, y=0.95))
    return fig

def sigmoid_position_chart(value):
    x = np.linspace(0, 100, 400); k = 0.12
    y = 1 / (1 + np.exp(-k * (x - 50))); y_val = 1 / (1 + np.exp(-k * (value - 50)))

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=y, mode="lines", line=dict(color="#cbd5e1", width=3), hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=[value], y=[y_val], mode="markers", marker=dict(size=16, color="#059669", line=dict(color="#ffffff", width=3)), hovertemplate="Growth Index: %{x:.1f}<extra></extra>"))
    fig.add_annotation(
        x=value, y=y_val, text="<b>You are here</b>", showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=1.5,
        arrowcolor="#059669", ax=65, ay=-35, font=dict(size=12, color="#059669", family="DM Sans"),
        bgcolor="rgba(255,255,255,0.9)", bordercolor="#059669", borderwidth=1,
    )
    fig.update_layout(
        paper_bgcolor=PLOTLY_THEME["paper_bgcolor"], plot_bgcolor=PLOTLY_THEME["plot_bgcolor"], font=PLOTLY_THEME["font"],
        height=238, margin=dict(l=30, r=10, t=12, b=28), xaxis=dict(range=[0, 100], title="Growth Index", gridcolor="#e2e8f0", zeroline=False),
        yaxis=dict(range=[0, 1], title="Maturity Momentum", gridcolor="#f1f5f9", zeroline=False, tickvals=[0, 0.25, 0.5, 0.75, 1.0], ticktext=["0", "0.25", "0.5", "0.75", "1.0"]),
        showlegend=False,
    )
    return fig

# ─────────────────────────────────────────────
#  HTML COMPONENTS
# ─────────────────────────────────────────────
def kpi_card(label, value, card_cls, val_cls):
    band_label, band_css = get_band(value)
    return f"""<div class="kpi-card {card_cls}"><div class="kpi-label">{label}</div><div class="kpi-value {val_cls}">{value:.0f}</div><span class="kpi-band {band_css}">{band_label}</span></div>"""
 
def section_header(num, title): 
    return f"""<div class="section-header"><span class="section-number">{num}</span><span class="section-title">{title}</span></div>"""
 
def stage_bar_html(row):
    stages = [
        ("Foundation Pressure",   row['Foundation'],   5, "#d97706"), 
        ("Growth Stability",      row['Growth'],       5, "#2563eb"), 
        ("Acceleration Readiness",row['Acceleration'], 5, "#7c3aed"), 
        ("Legacy Strength",       row['Legacy'],       5, "#059669")
    ]
    bars = ""
    for label, val, max_val, color in stages:
        pct = (val / max_val) * 100
        bars += f'<div class="stage-row"><span class="stage-label">{label}</span><div class="stage-track"><div class="stage-fill" style="width:{pct:.1f}%; background:{color};"></div></div><span class="stage-val">{val:.2f}</span></div>'
    return f'<div class="stage-bar-wrap stage-profile-offset">{bars}</div>'

def score_explanation_html():
    return (
        '<div class="explain-wrap"><div class="explain-head">How Your Scores Are Calculated</div><div class="explain-sub"></div><div class="explain-grid">'
        '<div class="explain-card exp-rel"><h4>Relevance</h4><ul><li>Meets immediate needs of parents and students.</li><li>Focus on curriculum alignment, compliance, visibility.</li><li>Creates a unique value proposition that differentiates.</li></ul></div>'
        '<div class="explain-card exp-reli"><h4>Reliability</h4><ul><li>Community trusts consistent delivery year after year.</li><li>Strong outcomes, defined SOPs, parent engagement.</li><li>Innovates and creates scalable systems.</li></ul></div>'
        '<div class="explain-card exp-repu"><h4>Reputability</h4><ul><li>Recognized at state, national, or international levels.</li><li>Engages in legacy-building initiatives.</li><li>Seen as a benchmark of excellence.</li></ul></div>'
        '</div></div>'
    )

def growth_stage_focus_html():
    return (
        '<div class="focus-wrap">'
        '<div class="focus-title">Growth Stages and Focus</div>'
        '<table class="focus-table">'
        '<thead>'
        '<tr>'
        '<th></th>'
        '<th>Management</th>'
        '<th>School Leader</th>'
        '<th>Faculty</th>'
        '</tr>'
        '</thead>'
        '<tbody>'
        '<tr>'
        '<td class="focus-stage">Foundation</td>'
        '<td>Focus on capital investment, brand positioning, community outreach, and long-term vision.</td>'
        '<td>Establish operational systems (admissions, timetable, discipline, communication).</td>'
        '<td>Adapt to school culture, set academic benchmarks, and engage parents directly.</td>'
        '</tr>'
        '<tr>'
        '<td class="focus-stage">Growth</td>'
        '<td>Shift from firefighting to governance - set clear policies, delegate authority, monitor performance.</td>'
        '<td>Drive academic quality, teacher mentoring, and parent engagement.</td>'
        '<td>Deliver consistent results; adopt professional development and modern pedagogy.</td>'
        '</tr>'
        '<tr>'
        '<td class="focus-stage">Acceleration</td>'
        '<td>Provide strategic investments for innovation; build alliances (universities, corporates, international partners).</td>'
        '<td>Shift to transformational leadership - focusing on culture, innovation, teacher empowerment, and visibility.</td>'
        '<td>Move from "teaching" to "mentoring and innovating"; collaborate on curriculum enrichment, research, and competitions.</td>'
        '</tr>'
        '<tr>'
        '<td class="focus-stage">Consolidation</td>'
        '<td>Focus on sustainability, diversification, succession planning, and creating a legacy.</td>'
        '<td>Become ambassadors and thought leaders in education forums; groom next-line leaders.</td>'
        '<td>Engage in advanced professional development, research, publications, and innovation in pedagogy.</td>'
        '</tr>'
        '</tbody>'
        '</table>'
        '</div>'
    )

# ─────────────────────────────────────────────
#  PLAYWRIGHT PDF GENERATOR ENGINE (SYNCHRONOUS & SINGLE PAGE)
# ─────────────────────────────────────────────
def generate_user_pdf_playwright(row):
    """Generates a high-fidelity, perfectly scaled single-page PDF using Playwright natively."""
    
    # 1. Generate HTML strings instead of Base64 images
    sig_html = fig_to_html(sigmoid_position_chart(row['Growth_Index']), 650, 260)
    g1_html = fig_to_html(gauge_chart(row['Relevance'], "RELEVANCE", "#d97706"), 220, 160)
    g2_html = fig_to_html(gauge_chart(row['Reliability_Adj'], "RELIABILITY", "#2563eb"), 220, 160)
    g3_html = fig_to_html(gauge_chart(row['Reputability_Adj'], "REPUTABILITY", "#7c3aed"), 220, 160)
    rad_html = fig_to_html(radar_chart(row), 450, 360)
    
    label, badge_cls, desc = get_strategic_profile(row)
    pdf_css = CUSTOM_CSS.replace(
        "@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');",
        "",
    )
    plotly_js = get_plotlyjs()
    
    # 2. Inject the HTML directly (No <img> tags needed!)
    pdf_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <script type="text/javascript">{plotly_js}</script>
        <style>
            {pdf_css}
            html, body {{ margin: 0 !important; padding: 0 !important; background: #ffffff; }}
            .pdf-container {{ padding: 50px; width: 100%; box-sizing: border-box; }}
            * {{ page-break-inside: avoid !important; page-break-before: auto !important; page-break-after: auto !important; }}
            .kpi-row {{ display: flex; gap: 20px; margin-bottom: 25px; align-items: stretch; }}
            .kpi-col {{ flex: 1; display: flex; flex-direction: column; }}
            .chart-col {{ flex: 1.5; display: flex; justify-content: center; align-items: center; border: 1px solid #e2e8f0; border-radius: 12px; }}
            .gauge-row {{ display: flex; justify-content: space-around; margin-top: 15px; margin-bottom: 25px; width: 100%; }}
            .gauge-item {{ width: 32%; }}
        </style>
    </head>
    <body>
        <div class="pdf-container">
            <div class="sub-title" style="font-family: 'DM Mono', monospace; font-size: 0.75rem; color: #64748b; letter-spacing: 0.2em; text-transform: uppercase;">Your Strategic Report</div>
            <h1 style="margin-top: 5px; margin-bottom: 15px;">{row['Display_Name']}</h1>
            
            <div class="status-row" style="margin-bottom: 35px;">
                <span class="status-badge {badge_cls}">{label}</span>
                <span class="badge-desc">{desc}</span>
            </div>
            
            <div class="kpi-row">
                <div class="kpi-col">
                    <div class="kpi-card growth" style="height: 100%; display:flex; flex-direction:column; justify-content:center;">
                        <div class="kpi-label">Growth Index</div>
                        <div class="kpi-value growth">{row['Growth_Index']:.1f}</div>
                    </div>
                </div>
                <div class="chart-col">
                    {sig_html}
                </div>
            </div>
            
            <div class="section-header" style="margin-top: 40px;">
                <span class="section-number">01</span><span class="section-title">R-Cube Maturity Gauges</span>
            </div>
            
            <div class="gauge-row">
                <div class="gauge-item">{g1_html}</div>
                <div class="gauge-item">{g2_html}</div>
                <div class="gauge-item">{g3_html}</div>
            </div>
            
            <div style="margin-top: 20px; margin-bottom: 40px;">{score_explanation_html()}</div>

            <div class="section-header">
                <span class="section-number">02</span><span class="section-title">Growth Stage Profile</span>
            </div>
            
            <div class="kpi-row" style="align-items: center;">
                <div class="kpi-col">{stage_bar_html(row)}</div>
                <div class="chart-col">{rad_html}</div>
            </div>
            
            <div style="margin-top: 20px;">{growth_stage_focus_html()}</div>
            
            <div style="margin-top: 50px; text-align: center; font-family: 'DM Mono', monospace; font-size: 10px; color: #94a3b8; text-transform: uppercase; border-top: 1px solid #e2e8f0; padding-top: 20px;">
                R-Cube Strategic Intelligence · Edxso Analytics · Confidential Report
            </div>
        </div>
    </body>
    </html>
    """
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage", "--single-process"]
        )
        context = browser.new_context()
        page = context.new_page()
        
        page.set_content(pdf_html, wait_until="load")
        
        # Hard wait 2 seconds to let Plotly drawing animations finish
        page.wait_for_timeout(2000) 
        
        exact_height = page.evaluate("document.documentElement.scrollHeight")
        adjusted_height = exact_height + 50

        pdf_bytes = page.pdf(
            width="1100px",
            height=f"{adjusted_height}px",
            print_background=True,
            margin={"top": "0", "right": "0", "bottom": "0", "left": "0"}
        )
        browser.close()
        return pdf_bytes

def run_app():
    install_playwright()
    st.set_page_config(**APP_PAGE_CONFIG)
    st.markdown(f"<style>{CUSTOM_CSS}</style>", unsafe_allow_html=True)
    if "generated_pdfs" not in st.session_state:
        st.session_state.generated_pdfs = {}
    if "pdf_batch_log" not in st.session_state:
        st.session_state.pdf_batch_log = []
    if "email_batch_log" not in st.session_state:
        st.session_state.email_batch_log = []
    if "current_screen" not in st.session_state:
        st.session_state.current_screen = "report"
    if "pdf_progress" not in st.session_state:
        st.session_state.pdf_progress = {"current": 0, "total": 0, "message": "", "active": False}

    with st.sidebar:
        st.markdown("""
        <div style='padding: 0.5rem 0 1.5rem 0;'>
            <div style='font-family: Playfair Display, serif; font-size: 1.5rem; font-weight: 900; color: #0f172a; line-height: 1.1;'>
                R-Cube<br>Strategic Intelligence
            </div>
            <div style='font-family: DM Mono, monospace; font-size: 0.65rem; letter-spacing: 0.2em; color: #64748b; text-transform: uppercase; margin-top: 0.4rem;'>
                Screening Metric v2
            </div>
        </div>
        """, unsafe_allow_html=True)

        report_mode = st.selectbox(
            "Report Type",
            ["Single Report", "Pre/Post Comparison"],
        )

        if report_mode == "Single Report":
            uploaded_file = st.file_uploader("Upload Response CSV", type=["csv"])
        else:
            uploaded_file = None

    if report_mode == "Pre/Post Comparison":
        render_comparison_report()
        return

    if not uploaded_file:
        st.markdown("""
        <div style='display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 70vh; text-align: center; padding: 2rem;'>
            <div style='font-family: Playfair Display, serif; font-size: 3.5rem; font-weight: 900; color: #0f172a; line-height: 1.1; max-width: 700px;'>
                R-Cube Strategic<br>Command Centre
            </div>
            <div style='font-family: DM Sans, sans-serif; font-size: 1.1rem; color: #475569; margin-top: 1rem; max-width: 480px; line-height: 1.7;'>
                Upload your response CSV to generate per-user strategic profiles, maturity-adjusted R-scores, and stage diagnostics.
            </div>
            <div style='margin-top: 2.5rem; font-family: DM Mono, monospace; font-size: 0.7rem; font-weight: 600; letter-spacing: 0.2em; text-transform: uppercase; color: #334155; border: 1px dashed #cbd5e1; background: #ffffff; padding: 0.75rem 1.5rem; border-radius: 8px;'>
                ← Upload CSV in sidebar to begin
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    uploaded_file_bytes = uploaded_file.getvalue()
    current_library_key = build_library_key(uploaded_file.name, uploaded_file_bytes)
    if st.session_state.get("current_library_key") != current_library_key:
        st.session_state.current_library_key = current_library_key
        st.session_state.generated_pdfs = load_generated_pdf_library(current_library_key)
        st.session_state.pdf_batch_log = []
        st.session_state.pdf_progress = {"current": 0, "total": 0, "message": "", "active": False}

    raw = pd.read_csv(io.BytesIO(uploaded_file_bytes))
    results = prepare_results(raw)
    status_col = find_column_name(raw, ["status", "mail status", "email status"])
    pending_count = (
        raw[status_col].astype(str).str.strip().eq("Pending").sum()
        if status_col is not None
        else len(raw)
    )
    with st.sidebar:
        st.markdown("---")
        user_choice = st.selectbox("Select User Report", results['UserID'].tolist())

        st.markdown("`PDF Actions`")
        generate_single_pdf = st.button(
            "Compile Selected PDF",
            type="primary",
            use_container_width=True,
        )
        generate_all_pdfs = st.button("Generate PDFs For All Rows", use_container_width=True)
        clear_generated_pdfs = st.button("Clear Generated PDF List", use_container_width=True)

        st.markdown("`Email Actions`")
        st.caption(f"Pending email rows: {pending_count}")
        send_pending_emails = st.button("Send Pending Emails", use_container_width=True)

        st.markdown(f"""
        <div style='font-family: DM Mono, monospace; font-size: 0.6rem; color: #64748b; letter-spacing: 0.1em; text-transform: uppercase; margin-top: 1rem;'>Cohort Size</div>
        <div style='font-family: Playfair Display, serif; font-size: 2rem; font-weight: 900; color: #0f172a;'>{len(results)}</div>
        """, unsafe_allow_html=True)

        avg_gi = results['Growth_Index'].mean()
        rank = int(results['Growth_Index'].rank(ascending=False)[results['UserID'] == user_choice].values[0])
        st.markdown(f"""
        <div style='margin-top: 1rem;'><div style='font-family: DM Mono, monospace; font-size: 0.6rem; color: #64748b; letter-spacing: 0.1em; text-transform: uppercase;'>Cohort Avg GI</div><div style='font-family: Playfair Display, serif; font-size: 1.6rem; font-weight: 900; color: #0f172a;'>{avg_gi:.1f}</div></div>
        <div style='margin-top: 1rem;'><div style='font-family: DM Mono, monospace; font-size: 0.6rem; color: #64748b; letter-spacing: 0.1em; text-transform: uppercase;'>Current Rank</div><div style='font-family: Playfair Display, serif; font-size: 1.6rem; font-weight: 900; color: #059669;'>#{rank} / {len(results)}</div></div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("""
        <div style='font-family: DM Mono, monospace; font-size: 0.6rem; color: #475569; letter-spacing: 0.1em; text-transform: uppercase;'>
        Scoring Model
        </div>
        <div style='font-size: 0.78rem; color: #64748b; margin-top: 0.5rem; line-height: 1.6;'>
        <b style='color:#d97706;'>Relevance</b> — Q1,2,5,11,13,14<br>
        <b style='color:#2563eb;'>Reliability</b> — Q3,4,6-10,12,14,15<br>
        <b style='color:#7c3aed;'>Reputability</b> — Q16–20<br><br>
        <span style='background: #f1f5f9; padding: 2px 4px; border-radius:4px; color:#0f172a;'>GI = 0.35·R + 0.40·Rel + 0.25·Rep</span>
        </div>
        """, unsafe_allow_html=True)

    row = results[results['UserID'] == user_choice].iloc[0]
    label, badge_cls, desc = get_strategic_profile(row)
    if generate_single_pdf:
        st.session_state.current_screen = "report"
    if generate_all_pdfs or clear_generated_pdfs:
        st.session_state.current_screen = "pdf"
    if send_pending_emails:
        st.session_state.current_screen = "email"

    screen_to_label = {
        "report": "Report",
        "pdf": "PDF Library",
        "email": "Email Delivery",
    }
    label_to_screen = {label: screen for screen, label in screen_to_label.items()}
    selected_label = st.segmented_control(
        "View",
        options=["Report", "PDF Library", "Email Delivery"],
        default=screen_to_label[st.session_state.current_screen],
        selection_mode="single",
    )
    st.session_state.current_screen = label_to_screen[selected_label]

    if st.session_state.current_screen == "report":
        st.markdown(f"""
        <div style='margin-bottom: 0.5rem; margin-top: 2rem;'>
            <div style='font-family: DM Mono, monospace; font-size: 0.7rem; color: #64748b; letter-spacing: 0.2em; text-transform: uppercase; margin-bottom: 0.3rem;'>
                Individual Strategic Report
            </div>
            <div style='font-family: Playfair Display, serif; font-size: 2.8rem; font-weight: 900; color: #0f172a; line-height: 1.1; margin-bottom: 0.6rem;'>
                {row['Display_Name']}
            </div>
        </div>
        """, unsafe_allow_html=True)

        k_left, k_right = st.columns([1, 1.45])
        with k_left:
            st.markdown(kpi_card("Growth Index", row['Growth_Index'], "growth", "growth"), unsafe_allow_html=True)
        with k_right:
            st.plotly_chart(sigmoid_position_chart(row['Growth_Index']), width='stretch')

        st.markdown(f"""<div class="status-row"><span class="status-badge {badge_cls}">{label}</span><span class="badge-desc">{desc}</span></div><br>""", unsafe_allow_html=True)
        st.markdown(section_header("01", "R-Cube Maturity Gauges"), unsafe_allow_html=True)
        g1, g2, g3 = st.columns(3)
        with g1:
            st.plotly_chart(gauge_chart(row['Relevance'], "RELEVANCE", "#d97706"), width='stretch')
        with g2:
            st.plotly_chart(gauge_chart(row['Reliability_Adj'], "RELIABILITY (ADJ)", "#2563eb"), width='stretch')
        with g3:
            st.plotly_chart(gauge_chart(row['Reputability_Adj'], "REPUTABILITY (ADJ)", "#7c3aed"), width='stretch')

        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown(score_explanation_html(), unsafe_allow_html=True)
        st.markdown(section_header("02", "Growth Stage Profile"), unsafe_allow_html=True)
        col_a, col_b = st.columns([1, 1])
        with col_a:
            st.markdown(stage_bar_html(row), unsafe_allow_html=True)
        with col_b:
            st.plotly_chart(radar_chart(row), width='stretch')
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown(growth_stage_focus_html(), unsafe_allow_html=True)
        st.markdown("<hr>", unsafe_allow_html=True)

        if generate_single_pdf:
            with st.spinner("Spinning up Playwright rendering engine..."):
                try:
                    st.session_state.pdf_progress = {
                        "current": 1,
                        "total": 1,
                        "message": f"Generating selected PDF: {row['Display_Name']}",
                        "active": True,
                    }
                    pdf_bytes = generate_user_pdf_playwright(row)
                    file_name = build_pdf_filename(user_choice)
                    contact = get_row_contact_details(raw, results, user_choice)
                    st.session_state.generated_pdfs[user_choice] = save_generated_pdf_record(
                        user_choice,
                        file_name,
                        pdf_bytes,
                        st.session_state.current_library_key,
                        email=contact["email"],
                        name=contact["name"],
                    )
                    persist_generated_pdf_library(
                        st.session_state.generated_pdfs,
                        st.session_state.current_library_key,
                    )
                    st.session_state.pdf_progress = {
                        "current": 1,
                        "total": 1,
                        "message": f"Generated selected PDF: {row['Display_Name']}",
                        "active": False,
                    }
                    st.success("PDF rendered successfully!")
                    st.download_button(
                        label="⬇️ Download PDF",
                        data=pdf_bytes,
                        file_name=file_name,
                        mime="application/pdf",
                        use_container_width=True,
                    )
                except Exception as e:
                    st.session_state.pdf_progress = {
                        "current": 0,
                        "total": 1,
                        "message": f"Selected PDF failed: {e}",
                        "active": False,
                    }
                    st.error(f"Render failed: {e}")

    elif st.session_state.current_screen == "pdf":
        pdf_progress_panel = st.empty()
        pdf_status_panel = st.empty()
        pdf_log_panel = st.empty()
        generated_list_panel = st.empty()
        st.markdown(section_header("03", "PDF Library"), unsafe_allow_html=True)
        st.markdown(
            """
            <div class="explain-wrap">
                <div class="explain-sub">Batch Generator</div>
                <div style="color:#334155; line-height:1.7;">
                    Generate a reusable list of PDFs from the uploaded CSV. This section does not send email.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption(f"Rows available in uploaded CSV: {len(results)}")
        if st.session_state.pdf_progress["total"]:
            progress_total = max(st.session_state.pdf_progress["total"], 1)
            progress_current = min(st.session_state.pdf_progress["current"], progress_total)
            pdf_progress_panel.progress(
                progress_current / progress_total,
                text=f"Generating PDFs: {progress_current}/{progress_total}",
            )
            if st.session_state.pdf_progress["message"]:
                if st.session_state.pdf_progress["active"]:
                    pdf_status_panel.info(st.session_state.pdf_progress["message"])
                else:
                    pdf_status_panel.success(st.session_state.pdf_progress["message"])

        if clear_generated_pdfs:
            st.session_state.generated_pdfs = {}
            st.session_state.pdf_batch_log = []
            st.session_state.pdf_progress = {"current": 0, "total": 0, "message": "", "active": False}
            clear_generated_pdf_library(st.session_state.current_library_key)
            st.success("Cleared generated PDF list.")

        if generate_all_pdfs:
            total_reports = len(results)
            existing_user_ids = {
                user_id for user_id in st.session_state.generated_pdfs.keys()
                if user_id in set(results["UserID"].tolist())
            }
            pending_reports = [
                report_row for _, report_row in results.iterrows()
                if report_row["UserID"] not in existing_user_ids
            ]
            batch_log = []
            generated_count = len(existing_user_ids)

            if not pending_reports:
                st.session_state.pdf_progress = {
                    "current": total_reports,
                    "total": total_reports,
                    "message": f"All {total_reports} PDFs are already generated for this uploaded list.",
                    "active": False,
                }
                pdf_progress_panel.progress(1.0, text=f"Generating PDFs: {total_reports}/{total_reports}")
                pdf_status_panel.success(st.session_state.pdf_progress["message"])

            for offset, report_row in enumerate(pending_reports, start=1):
                position = len(existing_user_ids) + offset
                current_name = report_row["Display_Name"]
                st.session_state.pdf_progress = {
                    "current": position,
                    "total": total_reports,
                    "message": f"Generating {position}/{total_reports}: {current_name}",
                    "active": True,
                }
                pdf_progress_panel.progress(position / total_reports, text=f"Generating PDFs: {position}/{total_reports}")
                pdf_status_panel.info(st.session_state.pdf_progress["message"])
                try:
                    pdf_bytes = generate_user_pdf_playwright(report_row)
                    pdf_user = report_row["UserID"]
                    contact = get_row_contact_details(raw, results, pdf_user)
                    st.session_state.generated_pdfs[pdf_user] = save_generated_pdf_record(
                        pdf_user,
                        build_pdf_filename(report_row["Display_Name"]),
                        pdf_bytes,
                        st.session_state.current_library_key,
                        email=contact["email"],
                        name=contact["name"],
                    )
                    persist_generated_pdf_library(
                        st.session_state.generated_pdfs,
                        st.session_state.current_library_key,
                    )
                    generated_count += 1
                    batch_log.append(f"{position}/{total_reports} generated: {current_name}")
                    render_generated_pdf_library(generated_list_panel)
                except Exception as e:
                    batch_log.append(f"{position}/{total_reports} failed: {current_name} ({e})")

            st.session_state.pdf_batch_log = batch_log
            st.session_state.pdf_progress = {
                "current": total_reports,
                "total": total_reports,
                "message": f"Generated {generated_count}/{total_reports} PDF(s).",
                "active": False,
            }
            pdf_progress_panel.progress(1.0, text=f"Generating PDFs: {total_reports}/{total_reports}")
            pdf_status_panel.success(st.session_state.pdf_progress["message"])

        if st.session_state.pdf_batch_log:
            with pdf_log_panel.container():
                for line in st.session_state.pdf_batch_log[-10:]:
                    st.write(f"- {line}")

        render_generated_pdf_library(generated_list_panel)

    elif st.session_state.current_screen == "email":
        email_progress_panel = st.empty()
        email_status_panel = st.empty()
        email_log_panel = st.empty()
        st.markdown(section_header("05", "Email Delivery"), unsafe_allow_html=True)
        st.markdown(
            """
            <div class="explain-wrap">
                <div class="explain-sub">Batch Sender</div>
                <div style="color:#334155; line-height:1.7;">
                    Send PDFs directly as email attachments for every row in the uploaded CSV where the status is <b>Pending</b>.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption(f"Pending rows available: {pending_count}")

        if send_pending_emails:
            with st.spinner("Generating PDFs and sending emails..."):
                try:
                    from send_pending_reports import send_pending_reports_from_dataframe

                    total_targets = pending_count
                    email_progress = email_progress_panel.progress(
                        0,
                        text=f"Sending emails: 0/{total_targets}" if total_targets else "Sending emails: 0/0",
                    )

                    def update_email_progress(current, total, name, phase):
                        total = max(total, 1)
                        phase_label = {
                            "sending": "Sending",
                            "sent": "Sent",
                            "error": "Failed",
                        }.get(phase, "Sending")
                        email_status_panel.info(f"{current}/{total}: {phase_label} {name}")
                        email_progress.progress(current / total, text=f"Sending emails: {current}/{total}")

                    run_log = send_pending_reports_from_dataframe(raw, progress_callback=update_email_progress)
                    success_count = sum(1 for item in run_log if item["status"] == "success")
                    error_count = sum(1 for item in run_log if item["status"] == "error")
                    st.session_state.email_batch_log = [item["message"] for item in run_log]

                    if success_count:
                        st.success(f"Sent {success_count} email(s).")
                    if error_count:
                        st.error(f"{error_count} email(s) failed.")
                    if not success_count and not error_count and run_log:
                        st.info(run_log[0]["message"])
                    email_status_panel.success(f"Completed email run: {success_count} sent, {error_count} failed.")
                except Exception as e:
                    st.error(f"Email sending failed: {e}")

        if st.session_state.email_batch_log:
            with email_log_panel.container():
                for line in st.session_state.email_batch_log[-10:]:
                    st.write(f"- {line}")

    st.markdown("""<div style='margin-top: 1rem; padding-top: 1.5rem; border-top: 1px solid #e2e8f0; font-family: DM Mono, monospace; font-size: 0.6rem; color: #94a3b8; letter-spacing: 0.15em; text-transform: uppercase; text-align: center;'>R-Cube Screening Metric · EDXSO Strategic Intelligence · Screening Tool</div>""", unsafe_allow_html=True)


if __name__ == "__main__":
    run_app()
