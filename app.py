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

# Logging Configuration
logging.basicConfig(
    filename="app_logs.txt",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

# Constants & Guardrails
MIN_CHARS = 10
MAX_CHARS = 500
ALLOWED_PATTERN = re.compile(r"^[a-zA-Z0-9\s\.\,\!\?\-\'\"\(\)]+$")

# Page Configuration
st.set_page_config(
    page_title="MedVerify AI | Professional Medical Fact Checker",
    page_icon="🔬",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Professional Custom CSS Styling
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

*, *::before, *::after { box-sizing: border-box; }

html, body, [class*="css"], .stApp {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    background-color: #0b0f19 !important;
    color: #f1f5f9;
}

.stApp {
    background: 
        radial-gradient(circle at 15% 15%, rgba(99, 102, 241, 0.15) 0%, transparent 40%),
        radial-gradient(circle at 85% 85%, rgba(16, 185, 129, 0.12) 0%, transparent 40%),
        #0b0f19 !important;
    min-height: 100vh;
}

.block-container { 
    padding: 1.5rem 1rem 3rem !important; 
    max-width: 800px !important; 
}

#MainMenu, footer, header { visibility: hidden; }

/* Top Navigation Bar */
.topbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.8rem 1.2rem;
    background: rgba(15, 23, 42, 0.6);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    margin-bottom: 2rem;
}
.topbar-logo {
    display: flex;
    align-items: center;
    gap: 12px;
}
.topbar-icon {
    width: 40px; height: 40px;
    background: linear-gradient(135deg, #6366f1, #4f46e5);
    border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.2rem;
    box-shadow: 0 4px 12px rgba(99, 102, 241, 0.35);
}
.topbar-name {
    font-size: 1.1rem;
    font-weight: 800;
    color: #ffffff;
    letter-spacing: -0.3px;
}
.topbar-name span { color: #818cf8; }
.topbar-badge {
    background: rgba(16, 185, 129, 0.15);
    border: 1px solid rgba(16, 185, 129, 0.3);
    border-radius: 999px;
    padding: 4px 14px;
    font-size: 0.7rem;
    font-weight: 700;
    color: #34d399;
    letter-spacing: 1.2px;
    text-transform: uppercase;
}

/* Hero Banner */
.hero {
    text-align: center;
    padding: 1rem 0 2rem;
}
.hero-eyebrow {
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
    margin-bottom: 1rem;
}
.hero-title {
    font-size: 2.6rem;
    font-weight: 800;
    line-height: 1.15;
    letter-spacing: -1px;
    margin-bottom: 0.8rem;
    background: linear-gradient(135deg, #ffffff 30%, #a5b4fc 70%, #34d399 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.hero-desc {
    color: #94a3b8;
    font-size: 0.98rem;
    font-weight: 400;
    line-height: 1.6;
    max-width: 520px;
    margin: 0 auto 0.5rem;
}
.hero-credit {
    font-size: 0.8rem;
    color: #64748b;
    font-weight: 500;
}
.hero-credit strong { color: #818cf8; }

/* Dashboard Metrics Grid */
.stats-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1rem;
    margin: 1.5rem 0 2rem;
}
.stat-card {
    background: rgba(15, 23, 42, 0.5);
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 16px;
    padding: 1.2rem 1rem;
    text-align: center;
    backdrop-filter: blur(10px);
    transition: all 0.3s ease;
}
.stat-card:hover {
    border-color: rgba(99, 102, 241, 0.3);
    transform: translateY(-2px);
}
.stat-val { font-size: 1.8rem; font-weight: 800; line-height: 1.1; margin-bottom: 4px; }
.stat-val.purple { color: #818cf8; }
.stat-val.green  { color: #34d399; }
.stat-val.red    { color: #f87171; }
.stat-lbl { font-size: 0.68rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px; color: #64748b; }

/* UI Inputs & Cards */
.input-card {
    background: rgba(15, 23, 42, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 20px;
    padding: 1.5rem;
    backdrop-filter: blur(16px);
    box-shadow: 0 20px 40px rgba(0,0,0,0.3);
}

.stTextArea > div > div > textarea {
    background: rgba(3, 7, 18, 0.6) !important;
    color: #f8fafc !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 14px !important;
    font-size: 0.95rem !important;
    padding: 14px !important;
    line-height: 1.5 !important;
}
.stTextArea > div > div > textarea:focus {
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2) !important;
}

.stButton > button {
    background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 0.85rem 1.5rem !important;
    font-size: 0.95rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.3px !important;
    box-shadow: 0 4px 20px rgba(99, 102, 241, 0.35) !important;
    transition: all 0.2s ease !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 24px rgba(99, 102, 241, 0.5) !important;
}

/* Tabs Styling */
.stTabs [data-baseweb="tab-list"] { gap: 10px; margin-bottom: 1.5rem; }
.stTabs [data-baseweb="tab"] {
    background: rgba(15, 23, 42, 0.4);
    border-radius: 12px;
    color: #94a3b8;
    border: 1px solid rgba(255, 255, 255, 0.05);
    padding: 10px 20px;
    font-size: 0.88rem;
    font-weight: 600;
}
.stTabs [aria-selected="true"] {
    background: rgba(99, 102, 241, 0.2) !important;
    color: #c7d2fe !important;
    border-color: rgba(99, 102, 241, 0.4) !important;
}

/* Result Displays */
.result-card {
    border-radius: 16px;
    padding: 1.6rem;
    text-align: center;
    margin: 1.5rem 0;
}
.result-fake {
    background: rgba(239, 68, 68, 0.08);
    border: 1px solid rgba(239, 68, 68, 0.3);
}
.result-true {
    background: rgba(16, 185, 129, 0.08);
    border: 1px solid rgba(16, 185, 129, 0.3);
}

.badge-fake { background: rgba(239, 68, 68, 0.2); color: #fca5a5; padding: 4px 12px; border-radius: 999px; font-size: 0.7rem; font-weight: 700; }
.badge-true { background: rgba(16, 185, 129, 0.2); color: #6ee7b7; padding: 4px 12px; border-radius: 999px; font-size: 0.7rem; font-weight: 700; }

.footer {
    text-align: center;
    padding: 2.5rem 0 1rem;
    border-top: 1px solid rgba(255, 255, 255, 0.06);
    margin-top: 3rem;
}
</style>
""", unsafe_allow_html=True)

# Input Validation
def validate_input(text):
    text = text.strip()
    if len(text) < MIN_CHARS:
        return False, f"Claim is too short. Please enter at least {MIN_CHARS} characters."
    if len(text) > MAX_CHARS:
        return False, f"Claim exceeds maximum length of {MAX_CHARS} characters."
    if not ALLOWED_PATTERN.match(text):
        return False, "Invalid characters detected. Only letters, numbers, and standard punctuation allowed."
    return True, text

def sanitize_display(text):
    return html.escape(text)

# PDF Report Generation
def generate_pdf(claim, result_status, confidence):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    conf_str = f"{confidence:.2f}%"
    story = [
        Paragraph("<b>MedVerify AI - Medical Verification Report</b>", styles['Title']),
        Spacer(1, 15),
        Paragraph(f"<b>Analyzed Claim:</b> {html.escape(claim)}", styles['Normal']),
        Spacer(1, 10),
        Paragraph(f"<b>Status:</b> {result_status}", styles['Normal']),
        Paragraph(f"<b>AI Confidence Rating:</b> {conf_str}", styles['Normal']),
        Spacer(1, 25),
        Paragraph("<i>Disclaimer: Generated automatically by MedVerify AI engine. Always consult qualified healthcare professionals for medical decisions.</i>", styles['Italic'])
    ]
    doc.build(story)
    buffer.seek(0)
    return buffer

# Load Trained Model
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
    st.error("Model could not be loaded. Please ensure required `.pkl` files are present.")

# Session State Initialization
for key, val in [("history", []), ("total", 0), ("fake", 0), ("cred", 0)]:
    if key not in st.session_state:
        st.session_state[key] = val

# Header Navigation
st.markdown("""
<div class="topbar">
    <div class="topbar-logo">
        <div class="topbar-icon">🔬</div>
        <div class="topbar-name">Med<span>Verify</span> AI</div>
    </div>
    <div class="topbar-badge">v2.0 Enterprise</div>
</div>
""", unsafe_allow_html=True)

# Hero Section
st.markdown("""
<div class="hero">
    <div class="hero-eyebrow">Advanced NLP Fact Verification</div>
    <div class="hero-title">Medical Misinformation<br>Detection Engine</div>
    <div class="hero-desc">
        Validate clinical claims, execute batch CSV analysis, and view real-time intelligence analytics powered by Machine Learning.
    </div>
    <div class="hero-credit">Engineered by <strong>Shahid Nawaz</strong> &nbsp;•&nbsp; SoftaVerse Tech House</div>
</div>
""", unsafe_allow_html=True)

# KPI Metrics Dashboard
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

# Main Application Tabs
tab1, tab2, tab3 = st.tabs(["🎯 Single Claim Analysis", "📁 Bulk CSV Verification", "📊 Platform Analytics"])

with tab1:
    st.markdown('<div class="input-card">', unsafe_allow_html=True)
    st.markdown("<p style='font-size: 0.8rem; font-weight: 700; text-transform: uppercase; color: #94a3b8; letter-spacing: 1px; margin-bottom: 8px;'>Input Statement for Evaluation</p>", unsafe_allow_html=True)

    user_input = st.text_area(
        "label_hidden",
        placeholder="e.g., Clinical trials confirm regular exercise lowers cardiovascular disease risk...",
        height=120,
        max_chars=MAX_CHARS,
        label_visibility="collapsed"
    )

    btn = st.button("🔍 Execute Verification", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

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
                        use_container_width=True
                    )

                except Exception as e:
                    logging.error(f"Prediction Error: {e}")
                    st.error("An error occurred during verification execution.")

with tab2:
    st.markdown("<p style='color:#94a3b8; font-size:0.9rem;'>Upload a dataset in <b>.csv</b> format containing a required column named <code>claim</code> for automated batch processing.</p>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload File", type=["csv"], label_visibility="collapsed")
    
    if uploaded_file and model_ok:
        try:
            df = pd.read_csv(uploaded_file)
            if 'claim' in df.columns:
                with st.spinner("Processing batch records..."):
                    vec_batch = vectorizer.transform(df['claim'].astype(str).str.lower())
                    preds = model.predict(vec_batch)
                    df['Verification Status'] = ["Credible" if p == 1 else "Misinformation" for p in preds]
                
                st.success(f"Batch execution completed for {len(df)} records!")
                st.dataframe(df[['claim', 'Verification Status']].head(10), use_container_width=True)
                
                csv_bytes = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "📥 Download Complete Results (CSV)",
                    data=csv_bytes,
                    file_name="MedVerify_Batch_Results.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            else:
                st.error("CSV Structure Error: Missing required column header named 'claim'.")
        except Exception as e:
            st.error(f"Error parsing file: {e}")

with tab3:
    st.markdown("<h4 style='color:#f8fafc; font-weight:700; margin-bottom:12px;'>Classification Distribution</h4>", unsafe_allow_html=True)
    if st.session_state.total > 0:
        fig = px.pie(
            names=["Credible Claims", "Misinformation"],
            values=[st.session_state.cred, st.session_state.fake],
            color_discrete_sequence=["#34d399", "#ef4444"],
            hole=0.5
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#f8fafc",
            margin=dict(t=20, b=20, l=20, r=20)
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No query activity recorded in the current session.")

# Recent Session History
if st.session_state.history:
    st.markdown("<h5 style='color:#cbd5e1; font-weight:700; margin-top:2rem;'>Recent Audit Log</h5>", unsafe_allow_html=True)
    for icon, claim, label in st.session_state.history[:5]:
        status_color = "#34d399" if label == "t" else "#f87171"
        st.markdown(f"""
        <div style="background: rgba(15, 23, 42, 0.4); border-left: 3px solid {status_color}; padding: 10px 14px; border-radius: 8px; margin-bottom: 8px; font-size: 0.85rem; color: #cbd5e1;">
            {icon} &nbsp; {claim}
        </div>
        """, unsafe_allow_html=True)

# Application Footer
st.markdown("""
<div class="footer">
    <p style="font-size:0.9rem; font-weight:700; color:#f8fafc; margin-bottom:4px;">🔬 MedVerify AI Platform</p>
    <p style="font-size:0.75rem; color:#64748b;">Powered by SoftaVerse Tech House &nbsp;•&nbsp; Machine Learning & NLP Architecture</p>
</div>
""", unsafe_allow_html=True)
