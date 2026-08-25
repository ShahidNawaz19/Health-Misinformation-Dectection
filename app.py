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

logging.basicConfig(
    filename="app_logs.txt",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

MIN_CHARS = 10
MAX_CHARS = 500
ALLOWED_PATTERN = re.compile(r"^[a-zA-Z0-9\s\.\,\!\?\-\'\"\(\)]+$")

st.set_page_config(page_title="MedVerify AI - Pro", page_icon="🔬", layout="centered")

# ── CUSTOM CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800;900&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, [class*="css"], .stApp {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    background: #03040f !important;
}

.stApp {
    background:
        radial-gradient(ellipse 90% 70% at 15% -5%, rgba(109,40,217,0.45) 0%, transparent 55%),
        radial-gradient(ellipse 70% 60% at 85% 105%, rgba(16,185,129,0.25) 0%, transparent 50%),
        radial-gradient(ellipse 50% 40% at 50% 50%, rgba(79,70,229,0.08) 0%, transparent 70%),
        #03040f !important;
    min-height: 100vh;
}

.block-container { padding: 0 1.5rem 3rem !important; max-width: 720px !important; }
#MainMenu, footer, header { visibility: hidden; }

/* ── TOP BAR ── */
.topbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1.2rem 0 0.5rem;
    margin-bottom: 0.5rem;
    border-bottom: 1px solid rgba(255,255,255,0.05);
}
.topbar-logo {
    display: flex;
    align-items: center;
    gap: 10px;
}
.topbar-icon {
    width: 36px; height: 36px;
    background: linear-gradient(135deg, #6d28d9, #4f46e5);
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.1rem;
    box-shadow: 0 4px 15px rgba(109,40,217,0.5);
}
.topbar-name {
    font-size: 1rem;
    font-weight: 800;
    color: #f8fafc;
    letter-spacing: -0.3px;
}
.topbar-name span { color: #a78bfa; }
.topbar-badge {
    background: rgba(52,211,153,0.1);
    border: 1px solid rgba(52,211,153,0.25);
    border-radius: 999px;
    padding: 4px 12px;
    font-size: 0.62rem;
    font-weight: 700;
    color: #34d399;
    letter-spacing: 1.5px;
    text-transform: uppercase;
}

/* ── HERO ── */
.hero {
    text-align: center;
    padding: 2rem 1rem 1rem;
}
.hero-eyebrow {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: rgba(109,40,217,0.15);
    border: 1px solid rgba(139,92,246,0.3);
    border-radius: 999px;
    padding: 6px 20px;
    font-size: 0.68rem;
    font-weight: 700;
    color: #c4b5fd;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 1.2rem;
}
.hero-eyebrow-dot {
    width: 6px; height: 6px;
    background: #a78bfa;
    border-radius: 50%;
    animation: pulse 2s infinite;
}
.hero-title {
    font-size: 2.8rem;
    font-weight: 900;
    line-height: 1.05;
    letter-spacing: -1.8px;
    margin-bottom: 0.8rem;
    background: linear-gradient(135deg, #ffffff 0%, #e2d9f3 40%, #a78bfa 70%, #34d399 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.hero-desc {
    color: #94a3b8;
    font-size: 0.92rem;
    font-weight: 500;
    line-height: 1.6;
    max-width: 440px;
    margin: 0 auto 0.6rem;
}
.hero-credit {
    font-size: 0.75rem;
    color: #64748b;
    font-weight: 500;
    margin-bottom: 1.5rem;
}
.hero-credit strong { color: #a78bfa; }

/* ── STATS ── */
.stats {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 0.8rem;
    margin: 1rem 0 1.5rem;
}
.stat {
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 20px;
    padding: 1.1rem 0.8rem 0.9rem;
    text-align: center;
    position: relative;
    overflow: hidden;
    transition: border-color 0.3s, transform 0.3s;
}
.stat:hover { border-color: rgba(255,255,255,0.12); transform: translateY(-2px); }
.stat::after {
    content: '';
    position: absolute;
    bottom: 0; left: 0; right: 0;
    height: 2px;
    border-radius: 0 0 20px 20px;
}
.stat.purple::after { background: linear-gradient(90deg, transparent, #7c3aed, transparent); }
.stat.green::after  { background: linear-gradient(90deg, transparent, #10b981, transparent); }
.stat.red::after    { background: linear-gradient(90deg, transparent, #ef4444, transparent); }
.stat-icon { font-size: 1.1rem; margin-bottom: 3px; }
.stat-n { font-size: 2rem; font-weight: 900; letter-spacing: -1.5px; line-height: 1; }
.stat-n.purple { color: #a78bfa; }
.stat-n.green  { color: #34d399; }
.stat-n.red    { color: #f87171; }
.stat-l { font-size: 0.6rem; font-weight: 700; text-transform: uppercase; letter-spacing: 2px; color: #64748b; margin-top: 4px; }

/* ── INPUT CARD ── */
.input-card {
    background: rgba(255,255,255,0.025);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 24px;
    padding: 1.5rem;
    backdrop-filter: blur(30px);
    box-shadow: 0 25px 60px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.05);
    margin-bottom: 0.5rem;
}
.input-label {
    font-size: 0.65rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 2.5px;
    color: #64748b;
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    gap: 8px;
}
.input-label::before {
    content: '';
    display: block;
    width: 3px; height: 14px;
    background: linear-gradient(180deg, #7c3aed, #4f46e5);
    border-radius: 2px;
}
.char-bar-wrap { margin-top: 8px; }
.char-bar-bg { background: rgba(255,255,255,0.05); border-radius: 999px; height: 3px; overflow: hidden; }
.char-bar-fill { height: 100%; border-radius: 999px; background: linear-gradient(90deg, #7c3aed, #4f46e5); transition: width 0.3s; }
.char-text { font-size: 0.65rem; color: #64748b; text-align: right; margin-top: 4px; font-weight: 600; }
.char-warn { color: #f87171 !important; }

.stTextArea > div > div > textarea {
    background: rgba(3,4,15,0.8) !important;
    color: #e2e8f0 !important;
    border: 1.5px solid rgba(255,255,255,0.07) !important;
    border-radius: 16px !important;
    font-size: 0.95rem !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 500 !important;
    padding: 16px !important;
    line-height: 1.6 !important;
    caret-color: #a78bfa !important;
    resize: none !important;
    transition: all 0.25s !important;
}
.stTextArea > div > div > textarea::placeholder { color: #475569 !important; }
.stTextArea > div > div > textarea:hover {
    border-color: rgba(139,92,246,0.4) !important;
    box-shadow: 0 0 0 4px rgba(109,40,217,0.08) !important;
}
.stTextArea > div > div > textarea:focus {
    border-color: rgba(139,92,246,0.75) !important;
    box-shadow: 0 0 0 5px rgba(109,40,217,0.15) !important;
    background: rgba(109,40,217,0.05) !important;
    outline: none !important;
}

/* ── BUTTON ── */
.stButton > button {
    width: 100% !important;
    background: linear-gradient(135deg, #6d28d9 0%, #4f46e5 100%) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 16px !important;
    padding: 0.9rem 1.5rem !important;
    font-size: 0.98rem !important;
    font-weight: 700 !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    margin-top: 1rem !important;
    box-shadow: 0 8px 30px rgba(109,40,217,0.45), inset 0 1px 0 rgba(255,255,255,0.15) !important;
    transition: all 0.25s !important;
    letter-spacing: 0.3px !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 15px 40px rgba(109,40,217,0.6), inset 0 1px 0 rgba(255,255,255,0.2) !important;
}

/* ── RESULT ── */
.result {
    border-radius: 20px;
    padding: 1.8rem 1.5rem;
    text-align: center;
    margin: 1.2rem 0;
    position: relative;
    overflow: hidden;
}
.result::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
}
.result-fake {
    background: linear-gradient(135deg, rgba(220,38,38,0.12), rgba(239,68,68,0.04));
    border: 1.5px solid rgba(239,68,68,0.35);
    box-shadow: 0 0 50px rgba(239,68,68,0.12);
}
.result-fake::before { background: linear-gradient(90deg, transparent, #ef4444, transparent); }
.result-true {
    background: linear-gradient(135deg, rgba(16,185,129,0.12), rgba(52,211,153,0.04));
    border: 1.5px solid rgba(52,211,153,0.35);
    box-shadow: 0 0 50px rgba(52,211,153,0.12);
}
.result-true::before { background: linear-gradient(90deg, transparent, #34d399, transparent); }

.result-emoji { font-size: 3rem; display: block; margin-bottom: 0.6rem; }
.result-tag {
    display: inline-block;
    border-radius: 999px;
    padding: 4px 14px;
    font-size: 0.6rem;
    font-weight: 800;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    margin-bottom: 0.8rem;
}
.result-tag-fake { background: rgba(239,68,68,0.12); color: #fca5a5; border: 1px solid rgba(239,68,68,0.25); }
.result-tag-true { background: rgba(52,211,153,0.12); color: #6ee7b7; border: 1px solid rgba(52,211,153,0.25); }
.result-title-fake { font-size: 1.5rem; font-weight: 900; color: #f87171; letter-spacing: -0.5px; margin-bottom: 0.4rem; }
.result-title-true { font-size: 1.5rem; font-weight: 900; color: #34d399; letter-spacing: -0.5px; margin-bottom: 0.4rem; }
.result-desc { color: #94a3b8; font-size: 0.84rem; line-height: 1.6; font-weight: 500; }
.confidence-pill {
    display: inline-block;
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 999px;
    padding: 3px 12px;
    font-size: 0.72rem;
    color: #e2e8f0;
    margin-top: 8px;
    font-weight: 600;
}

/* ── DIVIDER & LABELS ── */
.divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.06), transparent);
    margin: 1.8rem 0;
}
.section-label {
    font-size: 0.6rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 3px;
    color: #64748b;
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    gap: 10px;
}
.section-label::after {
    content: ''; flex: 1; height: 1px; background: rgba(255,255,255,0.05);
}
.ex-group-label { font-size: 0.75rem; font-weight: 700; margin-bottom: 8px; }
.ex-group-label.fake { color: #f87171; }
.ex-group-label.cred { color: #34d399; }
.chip {
    display: inline-block; border-radius: 12px; padding: 6px 14px;
    font-size: 0.75rem; font-weight: 600; margin: 3px 3px 3px 0;
}
.chip-f { background: rgba(239,68,68,0.07); border: 1px solid rgba(239,68,68,0.18); color: #fca5a5; }
.chip-t { background: rgba(52,211,153,0.07); border: 1px solid rgba(52,211,153,0.18); color: #6ee7b7; }

/* ── HISTORY ── */
.h-item {
    display: flex; align-items: center; gap: 12px; border-radius: 14px;
    padding: 10px 14px; margin-bottom: 8px; font-size: 0.82rem; font-weight: 500;
    color: #94a3b8;
}
.h-fake { background: rgba(239,68,68,0.05); border-left: 2px solid rgba(239,68,68,0.5); }
.h-true { background: rgba(52,211,153,0.05); border-left: 2px solid rgba(52,211,153,0.5); }

/* ── TABS ── */
.stTabs [data-baseweb="tab-list"] { gap: 8px; margin-bottom: 1rem; }
.stTabs [data-baseweb="tab"] {
    background: rgba(255,255,255,0.02);
    border-radius: 14px;
    color: #94a3b8;
    border: 1px solid rgba(255,255,255,0.05);
    padding: 8px 18px;
    font-size: 0.85rem;
    font-weight: 600;
}
.stTabs [aria-selected="true"] {
    background: rgba(109,40,217,0.25) !important;
    color: #c4b5fd !important;
    border-color: rgba(139,92,246,0.4) !important;
}

/* ── FOOTER ── */
.footer {
    text-align: center;
    padding: 2rem 0 1rem;
    border-top: 1px solid rgba(255,255,255,0.04);
    margin-top: 2rem;
}
.footer-logo {
    font-size: 1.1rem;
    font-weight: 800;
    color: #e2e8f0;
    margin-bottom: 6px;
    letter-spacing: -0.3px;
}
.footer-logo span { color: #a78bfa; }
.footer-sub {
    font-size: 0.72rem;
    color: #64748b;
    font-weight: 500;
    line-height: 1.8;
}
</style>
""", unsafe_allow_html=True)

def validate_input(text):
    text = text.strip()
    if len(text) < MIN_CHARS:
        return False, "Claim too short. Minimum " + str(MIN_CHARS) + " characters required."
    if len(text) > MAX_CHARS:
        return False, "Claim too long. Maximum " + str(MAX_CHARS) + " characters allowed."
    if not ALLOWED_PATTERN.match(text):
        return False, "Invalid characters detected. Only letters, numbers, and basic punctuation allowed."
    return True, text

def sanitize_display(text):
    return html.escape(text)

def generate_pdf(claim, result_status, confidence):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    conf_str = "{:.2f}%".format(confidence)
    story = [
        Paragraph("<b>MedVerify AI - Medical Fact Check Report</b>", styles['Title']),
        Spacer(1, 15),
        Paragraph("<b>Analyzed Health Claim:</b> " + html.escape(claim), styles['Normal']),
        Spacer(1, 10),
        Paragraph("<b>Verification Status:</b> " + result_status, styles['Normal']),
        Paragraph("<b>AI Confidence Score:</b> " + conf_str, styles['Normal']),
        Spacer(1, 25),
        Paragraph("<i>Disclaimer: Generated automatically by MedVerify AI System. Always consult certified healthcare professionals.</i>", styles['Italic'])
    ]
    doc.build(story)
    buffer.seek(0)
    return buffer

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
    st.error("Model load nahi hua. Please check model files.")

for key, val in [("history",[]),("total",0),("fake",0),("cred",0)]:
    if key not in st.session_state:
        st.session_state[key] = val

# ── TOP BAR ──────────────────────────────────────────────────────────────────
st.markdown("""
<div class="topbar">
    <div class="topbar-logo">
        <div class="topbar-icon">🔬</div>
        <div class="topbar-name">Med<span>Verify</span> AI <small style='font-size:0.65rem; color:#a78bfa;'>v2.0 Pro</small></div>
    </div>
    <div class="topbar-badge">🟢 Live</div>
</div>
""", unsafe_allow_html=True)

# ── HERO ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <div class="hero-eyebrow">
        <span class="hero-eyebrow-dot"></span>
        AI-Powered Health Fact Checker
    </div>
    <div class="hero-title">Detect Health<br>Misinformation</div>
    <div class="hero-desc">
        Instantly verify claims, analyze bulk datasets, and view platform metrics using advanced Machine Learning.
    </div>
    <div class="hero-credit">Built by <strong>Shahid Nawaz</strong> &nbsp;·&nbsp; SoftaVerse Tech House</div>
</div>
""", unsafe_allow_html=True)

# ── STATS COUNTER ─────────────────────────────────────────────────────────────
tot = st.session_state.total
c_val = st.session_state.cred
f_val = st.session_state.fake

st.markdown(
    '<div class="stats">'
    '<div class="stat purple">'
    '<div class="stat-icon">📊</div>'
    '<div class="stat-n purple">' + str(tot) + '</div>'
    '<div class="stat-l">Analyzed</div></div>'
    '<div class="stat green">'
    '<div class="stat-icon">✅</div>'
    '<div class="stat-n green">' + str(c_val) + '</div>'
    '<div class="stat-l">Credible</div></div>'
    '<div class="stat red">'
    '<div class="stat-icon">🚨</div>'
    '<div class="stat-n red">' + str(f_val) + '</div>'
    '<div class="stat-l">Misinformation</div></div>'
    '</div>',
    unsafe_allow_html=True
)

# ── NAVIGATION TABS ──────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["🎯 Single Claim Check", "📁 Bulk CSV Analysis", "📊 Analytics Dashboard"])

# ── TAB 1: SINGLE CLAIM CHECK ────────────────────────────────────────────────
with tab1:
    st.markdown('<div class="input-card"><div class="input-label">Enter Health Claim</div>', unsafe_allow_html=True)

    user_input = st.text_area(
        "x",
        placeholder="e.g. Vaccines cause autism in children...",
        height=120,
        max_chars=MAX_CHARS,
        label_visibility="collapsed"
    )

    char_count = len(user_input)
    fill_pct   = int((char_count / MAX_CHARS) * 100)
    char_class = "char-warn" if char_count > MAX_CHARS * 0.85 else ""

    st.markdown(
        '<div class="char-bar-wrap">'
        '<div class="char-bar-bg"><div class="char-bar-fill" style="width:' + str(fill_pct) + '%"></div></div>'
        '<div class="char-text ' + char_class + '">' + str(char_count) + ' / ' + str(MAX_CHARS) + '</div>'
        '</div>',
        unsafe_allow_html=True
    )

    btn = st.button("🔍   Analyze Claim", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if btn:
        if not model_ok:
            st.error("Model not available.")
        else:
            is_valid, result_or_error = validate_input(user_input)
            if not is_valid:
                st.warning("⚠️ " + result_or_error)
            else:
                clean_input = result_or_error
                try:
                    with st.spinner("Analyzing claim..."):
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
                        confidence = 90.0

                    st.session_state.total += 1
                    conf_formatted = "{:.1f}".format(confidence)

                    if pred == 0:
                        st.session_state.fake += 1
                        status_str = "Misinformation Detected"
                        st.markdown(
                            '<div class="result result-fake">'
                            '<span class="result-emoji">🚨</span>'
                            '<div><span class="result-tag result-tag-fake">⚠ Warning</span></div>'
                            '<div class="result-title-fake">Misinformation Detected</div>'
                            '<div class="result-desc">This claim appears to be medically false or misleading.<br>Always verify with trusted health organizations like WHO or CDC.</div>'
                            '<div class="confidence-pill">AI Confidence: ' + conf_formatted + '%</div>'
                            '</div>',
                            unsafe_allow_html=True
                        )
                        st.session_state.history.insert(0, ("❌", sanitize_display(clean_input), "f"))
                    else:
                        st.session_state.cred += 1
                        status_str = "Credible Claim"
                        st.markdown(
                            '<div class="result result-true">'
                            '<span class="result-emoji">✅</span>'
                            '<div><span class="result-tag result-tag-true">✓ Verified</span></div>'
                            '<div class="result-title-true">Credible Claim</div>'
                            '<div class="result-desc">This claim appears to be medically accurate and evidence-based.<br>It aligns with established scientific and medical knowledge.</div>'
