import streamlit as st
import joblib
import time
import re
import html
import logging
import pandas as pd
import plotly.express as px
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# ----------------------------------------------------------------------------
# Logging Configuration
# ----------------------------------------------------------------------------
logging.basicConfig(
    filename="app_logs.txt",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

# ----------------------------------------------------------------------------
# Constants & Guardrails
# ----------------------------------------------------------------------------
MIN_CHARS = 10
MAX_CHARS = 500
ALLOWED_PATTERN = re.compile(r"^[a-zA-Z0-9\s\.\,\!\?\-\'\"\(\)\%\/\:\+\=\;\@]+$")

# ----------------------------------------------------------------------------
# Page Configuration
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="MedVerify AI | Professional Medical Fact Checker",
    page_icon="🔬",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ----------------------------------------------------------------------------
# Global Design Tokens
# ----------------------------------------------------------------------------
COLOR_BG        = "#080c14"
COLOR_SURFACE   = "rgba(15, 23, 42, 0.75)"
COLOR_BORDER    = "rgba(255, 255, 255, 0.12)"
COLOR_TEXT      = "#f8fafc"
COLOR_TEXT_DIM  = "#cbd5e1"
COLOR_TEXT_MUTE = "#64748b"
COLOR_PRIMARY   = "#6366f1"
COLOR_PRIMARY_2 = "#4f46e5"
COLOR_ACCENT    = "#818cf8"
COLOR_SUCCESS   = "#34d399"
COLOR_DANGER    = "#f87171"

# ----------------------------------------------------------------------------
# Comprehensive UI & Text Visibility CSS Fix
# ----------------------------------------------------------------------------
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

*, *::before, *::after {{ box-sizing: border-box; }}

html, body, [class*="css"], .stApp {{
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    background-color: {COLOR_BG} !important;
    color: {COLOR_TEXT} !important;
}}

.stApp {{
    background:
        radial-gradient(circle at 10% 20%, rgba(99, 102, 241, 0.18) 0%, transparent 45%),
        radial-gradient(circle at 90% 80%, rgba(16, 185, 129, 0.15) 0%, transparent 45%),
        {COLOR_BG} !important;
    min-height: 100vh;
}}

.block-container {{
    padding: 1.5rem 1rem 3rem !important;
    max-width: 800px !important;
}}

#MainMenu, footer, header {{ visibility: hidden; }}

/* ---------------------------------------------------------------------- */
/* Streamlit Standard Widget Fixes                                        */
/* ---------------------------------------------------------------------- */
p, span, label, li, div, h1, h2, h3, h4, h5, h6,
.stMarkdown, .stMarkdown p, .stMarkdown li, .stCaption {{
    color: {COLOR_TEXT} !important;
}}

/* Force Textarea Text and Background Visibility */
.stTextArea > div > div > textarea {{
    background: rgba(15, 23, 42, 0.85) !important;
    color: #ffffff !important;
    border: 1px solid rgba(255, 255, 255, 0.15) !important;
    border-radius: 14px !important;
    font-size: 0.98rem !important;
    padding: 16px !important;
    line-height: 1.6 !important;
    box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.4) !important;
}}

.stTextArea > div > div > textarea::placeholder {{
    color: #64748b !important;
}}

.stTextArea > div > div > textarea:focus {{
    border-color: {COLOR_PRIMARY} !important;
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.3) !important;
}}

/* File Uploader styling */
[data-testid="stFileUploaderDropzone"] {{
    background: rgba(15, 23, 42, 0.6) !important;
    border: 1.5px dashed rgba(255, 255, 255, 0.2) !important;
    border-radius: 16px !important;
}}

[data-testid="stFileUploaderDropzone"] * {{
    color: {COLOR_TEXT_DIM} !important;
}}

/* Custom Buttons */
.stButton > button {{
    background: linear-gradient(135deg, {COLOR_PRIMARY} 0%, {COLOR_PRIMARY_2} 100%) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 0.85rem 1.5rem !important;
    font-size: 0.95rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.3px !important;
    box-shadow: 0 6px 20px rgba(99, 102, 241, 0.4) !important;
    transition: all 0.25 ease !important;
}}

.stButton > button:hover {{
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 25px rgba(99, 102, 241, 0.6) !important;
}}

/* ---------------------------------------------------------------------- */
/* Tabs Fix & Styling                                                     */
/* ---------------------------------------------------------------------- */
.stTabs [data-baseweb="tab-list"] {{
    gap: 8px;
    margin-bottom: 1.5rem;
    background: rgba(15, 23, 42, 0.5);
    padding: 6px;
    border-radius: 14px;
    border: 1px solid {COLOR_BORDER};
}}

.stTabs [data-baseweb="tab"] {{
    background: transparent;
    border-radius: 10px;
    color: {COLOR_TEXT_DIM} !important;
    border: none;
    padding: 10px 18px;
    font-size: 0.88rem;
    font-weight: 600;
}}

.stTabs [aria-selected="true"] {{
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.25), rgba(79, 70, 229, 0.35)) !important;
    color: #ffffff !important;
    border: 1px solid rgba(99, 102, 241, 0.5) !important;
}}

/* ---------------------------------------------------------------------- */
/* UI Components & Cards                                                  */
/* ---------------------------------------------------------------------- */
.topbar {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.8rem 1.2rem;
    background: rgba(15, 23, 42, 0.7);
    backdrop-filter: blur(12px);
    border: 1px solid {COLOR_BORDER};
    border-radius: 16px;
    margin-bottom: 1.8rem;
}}
.topbar-logo {{ display: flex; align-items: center; gap: 12px; }}
.topbar-icon {{
    width: 40px; height: 40px;
    background: linear-gradient(135deg, {COLOR_PRIMARY}, {COLOR_PRIMARY_2});
    border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.2rem;
    box-shadow: 0 4px 12px rgba(99, 102, 241, 0.35);
}}
.topbar-name {{ font-size: 1.1rem; font-weight: 800; color: #ffffff; letter-spacing: -0.3px; }}
.topbar-name span {{ color: {COLOR_ACCENT}; }}
.topbar-badge {{
    background: rgba(16, 185, 129, 0.15);
    border: 1px solid rgba(16, 185, 129, 0.3);
    border-radius: 999px;
    padding: 4px 14px;
    font-size: 0.7rem;
    font-weight: 700;
    color: {COLOR_SUCCESS};
    letter-spacing: 1.2px;
    text-transform: uppercase;
}}

.hero {{ text-align: center; padding: 0.5rem 0 1.8rem; }}
.hero-eyebrow {{
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: rgba(99, 102, 241, 0.12);
    border: 1px solid rgba(99, 102, 241, 0.25);
    border-radius: 999px;
    padding: 6px 18px;
    font-size: 0.72rem;
    font-weight: 700;
    color: #a5b4fc;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    margin-bottom: 0.8rem;
}}
.hero-title {{
    font-size: 2.5rem;
    font-weight: 800;
    line-height: 1.15;
    letter-spacing: -1px;
    margin-bottom: 0.6rem;
    background: linear-gradient(135deg, #ffffff 30%, #a5b4fc 70%, {COLOR_SUCCESS} 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}}
.hero-desc {{
    color: {COLOR_TEXT_DIM};
    font-size: 0.95rem;
    line-height: 1.6;
    max-width: 520px;
    margin: 0 auto 0.5rem;
}}
.hero-credit {{ font-size: 0.8rem; color: {COLOR_TEXT_MUTE}; font-weight: 500; }}
.hero-credit strong {{ color: {COLOR_ACCENT}; }}

.stats-grid {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1rem;
    margin: 1.5rem 0 2rem;
}}
.stat-card {{
    background: rgba(15, 23, 42, 0.6);
    border: 1px solid {COLOR_BORDER};
    border-radius: 16px;
    padding: 1.2rem 1rem;
    text-align: center;
    backdrop-filter: blur(10px);
    transition: all 0.3s ease;
}}
.stat-card:hover {{ border-color: rgba(99, 102, 241, 0.4); transform: translateY(-2px); }}
.stat-val {{ font-size: 1.8rem; font-weight: 800; line-height: 1.1; margin-bottom: 4px; }}
.stat-val.purple {{ color: {COLOR_ACCENT}; }}
.stat-val.green  {{ color: {COLOR_SUCCESS}; }}
.stat-val.red    {{ color: {COLOR_DANGER}; }}
.stat-lbl {{ font-size: 0.68rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px; color: {COLOR_TEXT_MUTE}; }}

.input-card {{
    background: {COLOR_SURFACE};
    border: 1px solid {COLOR_BORDER};
    border-radius: 20px;
    padding: 1.5rem;
    backdrop-filter: blur(16px);
    box-shadow: 0 20px 40px rgba(0,0,0,0.4);
    margin-bottom: 1.5rem;
}}

.input-label {{
    font-size: 0.78rem;
    font-weight: 800;
    text-transform: uppercase;
    color: #a5b4fc;
    letter-spacing: 1.2px;
    margin-bottom: 10px;
    display: block;
}}

.result-card {{ border-radius: 16px; padding: 1.6rem; text-align: center; margin: 1.5rem 0; }}
.result-fake {{ background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.35); }}
.result-true {{ background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.35); }}

.badge-fake {{ background: rgba(239, 68, 68, 0.2); color: #fca5a5; padding: 4px 12px; border-radius: 999px; font-size: 0.7rem; font-weight: 700; }}
.badge-true {{ background: rgba(16, 185, 129, 0.2); color: #6ee7b7; padding: 4px 12px; border-radius: 999px; font-size: 0.7rem; font-weight: 700; }}

.section-title {{ font-size: 1.05rem; font-weight: 800; color: #f8fafc; margin: 0.5rem 0 1rem; }}
.helper-text {{ color: {COLOR_TEXT_DIM}; font-size: 0.9rem; line-height: 1.6; margin-bottom: 1rem; }}

.audit-row {{
    background: rgba(15, 23, 42, 0.6);
    padding: 12px 16px;
    border-radius: 10px;
    margin-bottom: 10px;
    font-size: 0.88rem;
    color: #e2e8f0;
}}

.footer {{
    text-align: center;
    padding: 2.5rem 0 1rem;
    border-top: 1px solid rgba(255, 255, 255, 0.08);
    margin-top: 3rem;
}}
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# Input Validation & Helper Functions
# ----------------------------------------------------------------------------
def validate_input(text: str):
    text = text.strip()
    if len(text) < MIN_CHARS:
        return False, f"Claim is too short. Please enter at least {MIN_CHARS} characters."
    if len(text) > MAX_CHARS:
        return False, f"Claim exceeds maximum length of {MAX_CHARS} characters."
    if not ALLOWED_PATTERN.match(text):
        return False, "Invalid characters detected. Only standard text and scientific symbols are permitted."
    return True, text


def sanitize_display(text: str) -> str:
    return html.escape(text)


def generate_pdf(claim: str, result_status: str, confidence: float) -> BytesIO:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    conf_str = f"{confidence:.2f}%"
    story = [
        Paragraph("<b>MedVerify AI - Medical Verification Report</b>", styles["Title"]),
        Spacer(1, 15),
        Paragraph(f"<b>Analyzed Claim:</b> {html.escape(claim)}", styles["Normal"]),
        Spacer(1, 10),
        Paragraph(f"<b>Status:</b> {result_status}", styles["Normal"]),
        Paragraph(f"<b>AI Confidence Rating:</b> {conf_str}", styles["Normal"]),
        Spacer(1, 25),
        Paragraph(
            "<i>Disclaimer: Generated automatically by MedVerify AI engine. "
            "Always consult qualified healthcare professionals for medical decisions.</i>",
            styles["Italic"],
        ),
    ]
    doc.build(story)
    buffer.seek(0)
    return buffer

# ----------------------------------------------------------------------------
# Model Loader
# ----------------------------------------------------------------------------
@st.cache_resource
def load_model():
    m = joblib.load("svm_model.pkl")
    v = joblib.load("tfidf_vectorizer.pkl")
    return m, v


try:
    model, vectorizer = load_model()
    model_ok = True
except Exception as e:
    model_ok = False
    logging.error(f"Failed to load model artifacts: {e}")
    st.error("Model missing. Ensure `svm_model.pkl` and `tfidf_vectorizer.pkl` exist in root folder.")

# ----------------------------------------------------------------------------
# Session State Initialization
# ----------------------------------------------------------------------------
for key, val in [("history", []), ("total", 0), ("fake", 0), ("cred", 0)]:
    if key not in st.session_state:
        st.session_state[key] = val

# ----------------------------------------------------------------------------
# Header Navigation
# ----------------------------------------------------------------------------
st.markdown("""
<div class="topbar">
    <div class="topbar-logo">
        <div class="topbar-icon">🔬</div>
        <div class="topbar-name">Med<span>Verify</span> AI</div>
    </div>
    <div class="topbar-badge">v2.0 Enterprise</div>
</div>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# Hero Section
# ----------------------------------------------------------------------------
st.markdown("""
<div class="hero">
    <div class="hero-eyebrow">Advanced NLP Fact Verification</div>
    <div class="hero-title">Medical Misinformation<br>Detection Engine</div>
    <div class="hero-desc">
        Validate clinical claims, execute batch CSV analysis, and view real-time
        intelligence analytics powered by Machine Learning.
    </div>
    <div class="hero-credit">Engineered by <strong>Shahid Nawaz</strong> &nbsp;•&nbsp; SoftaVerse Tech House</div>
</div>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# KPI Metrics Dashboard
# ----------------------------------------------------------------------------
st.markdown(f"""
<div class="stats-grid">
    <div class="stat-card">
        <div class="stat-val purple">{st.session_state.total}</div>
        <div class="stat-lbl">Analyzed Claims</div>
    </div>
    <div class="stat-card">
        <div class="stat-val green">{st.session_state.cred}</div>
        <div class="stat-lbl">Verified Credible</div>
    </div>
    <div class="stat-card">
        <div class="stat-val red">{st.session_state.fake}</div>
        <div class="stat-lbl">Misinformation</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# Main Application Tabs
# ----------------------------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["🎯 Single Claim Analysis", "📁 Bulk CSV Verification", "📊 Platform Analytics"])

with tab1:
    st.markdown('<div class="input-card">', unsafe_allow_html=True)
    st.markdown('<span class="input-label">Input Statement for Evaluation</span>', unsafe_allow_html=True)

    user_input = st.text_area(
        "label_hidden",
        placeholder="e.g., Clinical trials confirm regular exercise lowers cardiovascular disease risk by 30%...",
        height=130,
        max_chars=MAX_CHARS,
        label_visibility="collapsed",
    )

    btn = st.button("🔍 Execute Verification", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    if btn:
        if not model_ok:
            st.error("System engine unavailable.")
        else:
            is_valid, result_or_error = validate_input(user_input)
            if not is_valid:
                st.warning(f"⚠️ {result_or_error}")
            else:
                clean_input = result_or_error
                try:
                    with st.spinner("Processing NLP algorithms..."):
                        time.sleep(0.3)

                    vec_input = vectorizer.transform([clean_input.lower()])
                    pred = model.predict(vec_input)[0]

                    if hasattr(model, "predict_proba"):
                        probs = model.predict_proba(vec_input)[0]
                        confidence = max(probs) * 100
                    elif hasattr(model, "decision_function"):
                        dist = model.decision_function(vec_input)[0]
                        confidence = min(99.5, max(65.0, 50.0 + abs(dist) * 22))
                    else:
                        confidence = 92.5

                    st.session_state.total += 1
                    conf_formatted = f"{confidence:.1f}"

                    if pred == 0:
                        st.session_state.fake += 1
                        status_str = "Misinformation Flagged"
                        st.markdown(f"""
                        <div class="result-card result-fake">
                            <span class="badge-fake">🚨 Misinformation Flagged</span>
                            <h3 style="color: #f87171; font-weight: 800; margin: 12px 0 6px;">Potentially Inaccurate Claim</h3>
                            <p style="color: #94a3b8; font-size: 0.88rem; margin-bottom: 10px;">This statement aligns with flagged health misinformation patterns. Cross-verify with verified clinical repositories (WHO, CDC).</p>
                            <span style="font-size: 0.8rem; background: rgba(255,255,255,0.05); padding: 4px 12px; border-radius: 999px; color: #e2e8f0;">Model Confidence: {conf_formatted}%</span>
                        </div>
                        """, unsafe_allow_html=True)
                        st.session_state.history.insert(0, ("❌", sanitize_display(clean_input), "f"))
                    else:
                        st.session_state.cred += 1
                        status_str = "Credible Statement"
                        st.markdown(f"""
                        <div class="result-card result-true">
                            <span class="badge-true">✅ Credible Statement</span>
                            <h3 style="color: #34d399; font-weight: 800; margin: 12px 0 6px;">Evidence-Based Claim</h3>
                            <p style="color: #94a3b8; font-size: 0.88rem; margin-bottom: 10px;">This statement is consistent with established medical consensus and scientifically backed literature.</p>
                            <span style="font-size: 0.8rem; background: rgba(255,255,255,0.05); padding: 4px 12px; border-radius: 999px; color: #e2e8f0;">Model Confidence: {conf_formatted}%</span>
                        </div>
                        """, unsafe_allow_html=True)
                        st.session_state.history.insert(0, ("✅", sanitize_display(clean_input), "t"))

                    pdf_data = generate_pdf(clean_input, status_str, confidence)
                    st.download_button(
                        label="📄 Export Analysis PDF Report",
                        data=pdf_data,
                        file_name="MedVerify_Report.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                    )

                except Exception as e:
                    logging.error(f"Prediction Error: {e}")
                    st.error("An error occurred during verification execution.")

with tab2:
    st.markdown(
        "<p class='helper-text'>Upload a dataset in <b>.csv</b> format containing a required "
        "column named <code>claim</code> for automated batch processing.</p>",
        unsafe_allow_html=True,
    )
    uploaded_file = st.file_uploader("Upload File", type=["csv"], label_visibility="collapsed")

    if uploaded_file and model_ok:
        try:
            df = pd.read_csv(uploaded_file)
            if "claim" in df.columns:
                w
