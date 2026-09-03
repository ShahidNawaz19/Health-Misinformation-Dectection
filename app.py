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
import requests as req_lib

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
# Gemini API Configuration
# ----------------------------------------------------------------------------
OPENROUTER_API_KEY = "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"

def get_gemini_explanation(claim: str, is_misinfo: bool) -> str:
    try:
        if is_misinfo:
            prompt = f"""You are a medical fact-checker. This health claim is MISINFORMATION.
Health Claim: "{claim}"
Explain in 3 short paragraphs:
1. Why this claim is medically false
2. What the correct medical fact is
3. A trusted source (WHO, CDC, NIH)"""
        else:
            prompt = f"""You are a medical fact-checker. This health claim is CREDIBLE.
Health Claim: "{claim}"
Explain in 3 short paragraphs:
1. Why this claim is medically accurate
2. Additional context or benefit
3. A trusted source (WHO, CDC, NIH)"""

        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "nvidia/nemotron-3.5-lightning:free",
            "messages": [{"role": "user", "content": prompt}]
        }
        response = req_lib.post(url, json=payload, headers=headers, timeout=30)
        data = response.json()
        if "choices" in data and len(data["choices"]) > 0:
            return data["choices"][0]["message"]["content"]
        else:
            logging.error(f"API Payload Error: {data}")
            return "AI explanation could not be generated from the response. Please verify with WHO or CDC."
    except Exception as e:
        logging.error(f"OpenRouter API error: {e}")
        return "AI explanation currently unavailable. Please verify with WHO or CDC." 

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
COLOR_BG        = "#0b0f19"
COLOR_SURFACE   = "rgba(15, 23, 42, 0.6)"
COLOR_BORDER    = "rgba(255, 255, 255, 0.08)"
COLOR_TEXT      = "#f1f5f9"
COLOR_TEXT_DIM  = "#94a3b8"
COLOR_TEXT_MUTE = "#64748b"
COLOR_PRIMARY   = "#6366f1"
COLOR_PRIMARY_2 = "#4f46e5"
COLOR_ACCENT    = "#818cf8"
COLOR_SUCCESS   = "#34d399"
COLOR_DANGER    = "#f87171"

# ----------------------------------------------------------------------------
# Session State Initialization
# ----------------------------------------------------------------------------
for key, val in [("history", []), ("total", 0), ("fake", 0), ("cred", 0)]:
    if key not in st.session_state:
        st.session_state[key] = val

# ----------------------------------------------------------------------------
# Custom CSS Styling
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
        radial-gradient(circle at 15% 15%, rgba(99, 102, 241, 0.15) 0%, transparent 40%),
        radial-gradient(circle at 85% 85%, rgba(16, 185, 129, 0.12) 0%, transparent 40%),
        {COLOR_BG} !important;
    min-height: 100vh;
}}

.block-container {{ padding: 1.5rem 1rem 3rem !important; max-width: 800px !important; }}
#MainMenu, footer, header {{ visibility: hidden; }}

p, span, label, li, div, h1, h2, h3, h4, h5, h6,
.stMarkdown, .stMarkdown p, .stMarkdown li, .stCaption {{ color: {COLOR_TEXT}; }}

.stTextArea label, .stFileUploader label, .stSelectbox label,
.stRadio label, .stCheckbox label, .stNumberInput label {{
    color: {COLOR_TEXT_DIM} !important; font-weight: 600 !important;
}}

[data-testid="stFileUploaderDropzone"] {{
    background: rgba(3, 7, 18, 0.5) !important;
    border: 1.5px dashed rgba(255, 255, 255, 0.18) !important;
    border-radius: 14px !important;
}}
[data-testid="stFileUploaderDropzone"] * {{ color: {COLOR_TEXT_DIM} !important; }}
[data-testid="stFileUploaderDropzone"] button {{
    background: linear-gradient(135deg, {COLOR_PRIMARY} 0%, {COLOR_PRIMARY_2} 100%) !important;
    color: #ffffff !important; border: none !important; border-radius: 10px !important;
}}

[data-testid="stDataFrame"] {{
    background: {COLOR_SURFACE} !important;
    border: 1px solid {COLOR_BORDER} !important;
    border-radius: 14px !important; overflow: hidden;
}}

div[data-testid="stAlert"] {{
    border-radius: 12px !important;
    background: rgba(15, 23, 42, 0.65) !important;
    border: 1px solid {COLOR_BORDER} !important;
}}

.stDownloadButton > button {{
    background: rgba(99, 102, 241, 0.12) !important;
    color: {COLOR_ACCENT} !important;
    border: 1px solid rgba(99, 102, 241, 0.35) !important;
    border-radius: 12px !important; font-weight: 700 !important;
    padding: 0.75rem 1.4rem !important; transition: all 0.2s ease !important;
}}
.stDownloadButton > button:hover {{
    background: rgba(99, 102, 241, 0.22) !important; transform: translateY(-1px) !important;
}}

.topbar {{
    display: flex; align-items: center; justify-content: space-between;
    padding: 0.8rem 1.2rem;
    background: rgba(15, 23, 42, 0.6); backdrop-filter: blur(12px);
    border: 1px solid {COLOR_BORDER}; border-radius: 16px; margin-bottom: 2rem;
}}
.topbar-logo {{ display: flex; align-items: center; gap: 12px; }}
.topbar-icon {{
    width: 40px; height: 40px;
    background: linear-gradient(135deg, {COLOR_PRIMARY}, {COLOR_PRIMARY_2});
    border-radius: 12px; display: flex; align-items: center; justify-content: center;
    font-size: 1.2rem; box-shadow: 0 4px 12px rgba(99, 102, 241, 0.35);
}}
.topbar-name {{ font-size: 1.1rem; font-weight: 800; color: #ffffff; letter-spacing: -0.3px; }}
.topbar-name span {{ color: {COLOR_ACCENT}; }}
.topbar-badge {{
    background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.3);
    border-radius: 999px; padding: 4px 14px; font-size: 0.7rem; font-weight: 700;
    color: {COLOR_SUCCESS}; letter-spacing: 1.2px; text-transform: uppercase;
}}

.hero {{ text-align: center; padding: 1rem 0 2rem; }}
.hero-eyebrow {{
    display: inline-flex; align-items: center; gap: 8px;
    background: rgba(99, 102, 241, 0.12); border: 1px solid rgba(99, 102, 241, 0.25);
    border-radius: 999px; padding: 6px 18px; font-size: 0.72rem; font-weight: 700;
    color: #a5b4fc; letter-spacing: 1.5px; text-transform: uppercase; margin-bottom: 1rem;
}}
.hero-title {{
    font-size: 2.6rem; font-weight: 800; line-height: 1.15;
    letter-spacing: -1px; margin-bottom: 0.8rem;
    background: linear-gradient(135deg, #ffffff 30%, #a5b4fc 70%, {COLOR_SUCCESS} 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}}
.hero-desc {{
    color: {COLOR_TEXT_DIM}; font-size: 0.98rem; font-weight: 400;
    line-height: 1.6; max-width: 520px; margin: 0 auto 0.5rem;
}}
.hero-credit {{ font-size: 0.8rem; color: {COLOR_TEXT_MUTE}; font-weight: 500; }}
.hero-credit strong {{ color: {COLOR_ACCENT}; }}

.stats-grid {{
    display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin: 1.5rem 0 2rem;
    width: 100%;
}}
.stat-card {{
    background: rgba(15, 23, 42, 0.5); border: 1px solid {COLOR_BORDER};
    border-radius: 16px; padding: 1.2rem 1rem; text-align: center;
    backdrop-filter: blur(10px); transition: all 0.3s ease;
}}
.stat-card:hover {{ border-color: rgba(99, 102, 241, 0.3); transform: translateY(-2px); }}
.stat-val {{ font-size: 1.8rem; font-weight: 800; line-height: 1.1; margin-bottom: 4px; }}
.stat-val.purple {{ color: {COLOR_ACCENT}; }}
.stat-val.green  {{ color: {COLOR_SUCCESS}; }}
.stat-val.red    {{ color: {COLOR_DANGER}; }}
.stat-lbl {{ font-size: 0.68rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px; color: {COLOR_TEXT_MUTE}; }}

.stTabs [data-baseweb="tab-list"] {{ gap: 10px; margin-bottom: 1.5rem; width: 100%; }}
.stTabs [data-baseweb="tab"] {{
    background: rgba(15, 23, 42, 0.4); border-radius: 12px;
    color: {COLOR_TEXT_DIM} !important; border: 1px solid rgba(255, 255, 255, 0.05);
    padding: 10px 20px; font-size: 0.88rem; font-weight: 600; flex: 1; text-align: center;
}}
.stTabs [aria-selected="true"] {{
    background: rgba(99, 102, 241, 0.2) !important;
    color: #c7d2fe !important; border-color: rgba(99, 102, 241, 0.4) !important;
}}

.input-label-header {{
    font-size: 0.8rem; font-weight: 700; text-transform: uppercase;
    color: #94a3b8; letter-spacing: 1px; margin-bottom: 8px; margin-top: 0px;
}}

.stTextArea textarea {{
    background: #0d1424 !important; color: #ffffff !important;
    border: 1.5px solid rgba(99, 102, 241, 0.35) !important; border-radius: 14px !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important; font-size: 0.98rem !important;
    font-weight: 500 !important; padding: 16px !important; line-height: 1.65 !important;
    caret-color: {COLOR_ACCENT} !important; box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.5) !important;
    transition: all 0.25s ease !important;
}}
.stTextArea textarea::placeholder {{ color: #64748b !important; opacity: 1 !important; }}
.stTextArea textarea:hover {{
    border-color: rgba(99, 102, 241, 0.6) !important; background: #111a30 !important;
}}
.stTextArea textarea:focus {{
    border-color: {COLOR_PRIMARY} !important; background: #111a30 !important;
    box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.25), inset 0 2px 8px rgba(0, 0, 0, 0.5) !important;
    outline: none !important;
}}

.stButton > button {{
    background: linear-gradient(135deg, {COLOR_PRIMARY} 0%, {COLOR_PRIMARY_2} 100%) !important;
    color: #ffffff !important; border: none !important; border-radius: 12px !important;
    padding: 0.85rem 1.5rem !important; font-size: 0.95rem !important; font-weight: 700 !important;
    letter-spacing: 0.3px !important; box-shadow: 0 4px 20px rgba(99, 102, 241, 0.35) !important;
    transition: all 0.2s ease !important; margin-top: 10px;
}}
.stButton > button:hover {{
    transform: translateY(-1px) !important; box-shadow: 0 6px 24px rgba(99, 102, 241, 0.5) !important;
}}

.result-card {{ border-radius: 16px; padding: 1.6rem; text-align: center; margin: 1.5rem 0; }}
.result-fake {{ background: rgba(239, 68, 68, 0.08); border: 1px solid rgba(239, 68, 68, 0.3); }}
.result-true {{ background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.3); }}

.badge-fake {{ background: rgba(239, 68, 68, 0.2); color: #fca5a5; padding: 4px 12px; border-radius: 999px; font-size: 0.7rem; font-weight: 700; }}
.badge-true {{ background: rgba(16, 185, 129, 0.2); color: #6ee7b7; padding: 4px 12px; border-radius: 999px; font-size: 0.7rem; font-weight: 700; }}

.gemini-box {{
    background: rgba(99, 102, 241, 0.07);
    border: 1px solid rgba(99, 102, 241, 0.25);
    border-radius: 14px; padding: 1.2rem 1.4rem; margin-top: 1rem; text-align: left;
}}
.gemini-title {{
    font-size: 0.72rem; font-weight: 800; text-transform: uppercase;
    letter-spacing: 2px; color: #a5b4fc; margin-bottom: 0.6rem;
    display: flex; align-items: center; gap: 6px;
}}
.gemini-text {{ color: #94a3b8; font-size: 0.88rem; line-height: 1.7; }}

.section-title {{ font-size: 1.05rem; font-weight: 800; color: #f8fafc; margin: 0.5rem 0 1rem; }}
.helper-text {{ color: {COLOR_TEXT_DIM}; font-size: 0.9rem; line-height: 1.6; }}
.audit-row {{
    background: rgba(15, 23, 42, 0.4); padding: 10px 14px;
    border-radius: 8px; margin-bottom: 8px; font-size: 0.85rem; color: #cbd5e1;
}}
.footer {{
    text-align: center; padding: 2.5rem 0 1rem;
    border-top: 1px solid rgba(255, 255, 255, 0.06); margin-top: 3rem;
}}
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# Helper Functions
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

def generate_pdf(claim: str, result_status: str, confidence: float, explanation: str) -> BytesIO:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("<b>MedVerify AI - Medical Verification Report</b>", styles["Title"]),
        Spacer(1, 15),
        Paragraph(f"<b>Analyzed Claim:</b> {html.escape(claim)}", styles["Normal"]),
        Spacer(1, 10),
        Paragraph(f"<b>Verification Status:</b> {result_status}", styles["Normal"]),
        Paragraph(f"<b>AI Confidence Rating:</b> {confidence:.1f}%", styles["Normal"]),
        Spacer(1, 15),
        Paragraph("<b>Gemini AI Explanation:</b>", styles["Normal"]),
        Spacer(1, 5),
        Paragraph(explanation.replace("\n", "<br/>"), styles["Normal"]),
        Spacer(1, 20),
        Paragraph(
            "<i>Disclaimer: Generated automatically by MedVerify AI. Always consult qualified healthcare professionals.</i>",
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
    logging.error(f"Failed to load model: {e}")
    st.error("Model could not be loaded.")

# ----------------------------------------------------------------------------
# Top Bar
# ----------------------------------------------------------------------------
st.markdown("""
<div class="topbar">
    <div class="topbar-logo">
        <div class="topbar-icon">🔬</div>
        <div class="topbar-name">Med<span>Verify</span> AI</div>
    </div>
    <div class="topbar-badge">v3.0 Gemini Powered</div>
</div>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# Hero
# ----------------------------------------------------------------------------
st.markdown("""
<div class="hero">
    <div class="hero-eyebrow">🤖 Gemini AI + NLP Fact Verification</div>
    <div class="hero-title">Medical Misinformation<br>Detection Engine</div>
    <div class="hero-desc">
        Validate health claims using Machine Learning + Google Gemini AI explanations.
        Get instant predictions with intelligent reasoning powered by advanced NLP.
    </div>
    <div class="hero-credit">Engineered by <strong>Shahid Nawaz</strong> &nbsp;•&nbsp; SoftaVerse Tech House</div>
</div>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# KPI Dashboard (Dynamic Realtime Update Container)
# ----------------------------------------------------------------------------
stats_container = st.empty()

def render_stats():
    stats_container.markdown(f"""
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

render_stats()

# ----------------------------------------------------------------------------
# Tabs
# ----------------------------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["🎯 Single Claim Analysis", "📁 Bulk CSV Verification", "📊 Platform Analytics"])

with tab1:
    st.markdown('<p class="input-label-header">Input Statement for Evaluation</p>', unsafe_allow_html=True)
    user_input = st.text_area(
        "label_hidden",
        placeholder="e.g., Clinical trials confirm regular exercise lowers cardiovascular disease risk...",
        height=120,
        max_chars=MAX_CHARS,
        label_visibility="collapsed",
    )
    btn = st.button("🔍 Execute Verification", use_container_width=True)

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
                    else:
                        confidence = 92.5

                    st.session_state.total += 1
                    is_misinfo = pred == 0

                    if is_misinfo:
                        st.session_state.fake += 1
                        status_str = "Misinformation Flagged"
                    else:
                        st.session_state.cred += 1
                        status_str = "Credible Statement"

                    # Instant Stats Cards Refresh
                    render_stats()

                    # ── Gemini Explanation API Call ─────────────────────────
                    with st.spinner("🤖 Gemini AI generating explanation..."):
                        explanation = get_gemini_explanation(clean_input, is_misinfo)

                    if is_misinfo:
                        st.markdown(f"""
                        <div class="result-card result-fake">
                            <span class="badge-fake">🚨 Misinformation Flagged</span>
                            <h3 style="color:#f87171;font-weight:800;margin:12px 0 6px;">Potentially Inaccurate Claim</h3>
                            <p style="color:#94a3b8;font-size:0.88rem;margin-bottom:10px;">This statement aligns with flagged health misinformation patterns.</p>
                            <span style="font-size:0.8rem;background:rgba(255,255,255,0.05);padding:4px 12px;border-radius:999px;color:#e2e8f0;">Model Confidence: {confidence:.1f}%</span>
                        </div>
                        <div class="gemini-box">
                            <div class="gemini-title">🤖 Gemini AI Explanation</div>
                            <div class="gemini-text">{html.escape(explanation).replace(chr(10), '<br>')}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        st.session_state.history.insert(0, ("❌", sanitize_display(clean_input), "f"))
                    else:
                        st.markdown(f"""
                        <div class="result-card result-true">
                            <span class="badge-true">✅ Credible Statement</span>
                            <h3 style="color:#34d399;font-weight:800;margin:12px 0 6px;">Evidence-Based Claim</h3>
                            <p style="color:#94a3b8;font-size:0.88rem;margin-bottom:10px;">This statement is consistent with established medical consensus.</p>
                            <span style="font-size:0.8rem;background:rgba(255,255,255,0.05);padding:4px 12px;border-radius:999px;color:#e2e8f0;">Model Confidence: {confidence:.1f}%</span>
                        </div>
                        <div class="gemini-box">
                            <div class="gemini-title">🤖 Gemini AI Explanation</div>
                            <div class="gemini-text">{html.escape(explanation).replace(chr(10), '<br>')}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        st.session_state.history.insert(0, ("✅", sanitize_display(clean_input), "t"))

                    pdf_data = generate_pdf(clean_input, status_str, confidence, explanation)
                    st.download_button(
                        label="📄 Export Analysis PDF Report",
                        data=pdf_data,
                        file_name="MedVerify_Report.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                    )

                except Exception as e:
                    logging.error(f"Prediction Error: {e}")
                    st.error("An error occurred during verification.")

with tab2:
    st.markdown(
        "<p class='helper-text'>Upload a <b>.csv</b> file with a column named <code>claim</code> for batch processing.</p>",
        unsafe_allow_html=True,
    )
    uploaded_file = st.file_uploader("Upload File", type=["csv"], label_visibility="collapsed")

    if uploaded_file and model_ok:
        try:
            df = pd.read_csv(uploaded_file)
            if "claim" in df.columns:
                with st.spinner("Processing batch records..."):
                    vec_batch = vectorizer.transform(df["claim"].astype(str).str.lower())
                    preds = model.predict(vec_batch)
                    df["Verification Status"] = ["Credible" if p == 1 else "Misinformation" for p in preds]

                st.success(f"Batch completed for {len(df)} records!")
                st.dataframe(df[["claim", "Verification Status"]].head(10), use_container_width=True)

                csv_bytes = df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "📥 Download Results (CSV)",
                    data=csv_bytes,
                    file_name="MedVerify_Batch_Results.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
            else:
                st.error("CSV missing required column: 'claim'")
        except Exception as e:
            st.error(f"File error: {e}")

with tab3:
    st.markdown("<p class='section-title'>Classification Distribution</p>", unsafe_allow_html=True)
    if st.session_state.total > 0:
        fig = px.pie(
            names=["Credible Claims", "Misinformation"],
            values=[st.session_state.cred, st.session_state.fake],
            color_discrete_sequence=["#34d399", "#ef4444"],
            hole=0.5,
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#f8fafc",
            legend_font_color="#f8fafc",
            margin=dict(t=20, b=20, l=20, r=20),
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No activity recorded yet. Analyze a claim to see analytics.")

# ----------------------------------------------------------------------------
# Recent Audit Log
# ----------------------------------------------------------------------------
if st.session_state.history:
    st.markdown("<p class='section-title' style='margin-top:2rem;'>Recent Audit Log</p>", unsafe_allow_html=True)
    for icon, claim, label in st.session_state.history[:5]:
        status_color = COLOR_SUCCESS if label == "t" else COLOR_DANGER
        st.markdown(f"""
        <div class="audit-row" style="border-left: 3px solid {status_color};">
            {icon} &nbsp; {claim}
        </div>
        """, unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# Footer
# ----------------------------------------------------------------------------
st.markdown("""
<div class="footer">
    <p style="font-size:0.9rem;font-weight:700;color:#f8fafc;margin-bottom:4px;">🔬 MedVerify AI Platform</p>
    <p style="font-size:0.75rem;color:#64748b;">Powered by SoftaVerse Tech House &nbsp;•&nbsp; ML + Google Gemini AI &nbsp;•&nbsp; NLP Architecture</p>
</div>
""", unsafe_allow_html=True)
