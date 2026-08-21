import streamlit as st
import joblib
import time
import re
import html
import logging
import os

# ── Logging Setup ───────────────────────────────────────────────────────────────
logging.basicConfig(
    filename="app_logs.txt",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

# ── Constants ───────────────────────────────────────────────────────────────────
MIN_CHARS = 10
MAX_CHARS = 500
MODEL_PATH = "svm_model.pkl"
VEC_PATH   = "tfidf_vectorizer.pkl"
ALLOWED_PATTERN = re.compile(r"^[a-zA-Z0-9\s\.\,\!\?\-\'\"\(\)]+$")

st.set_page_config(page_title="Health Claim Checker", page_icon="🏥", layout="centered")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html, body, [class*="css"], .stApp {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    background: #060818 !important;
}
.stApp {
    background:
        radial-gradient(ellipse 80% 60% at 20% -10%, rgba(99,57,242,0.35) 0%, transparent 60%),
        radial-gradient(ellipse 60% 50% at 80% 110%, rgba(16,185,129,0.2) 0%, transparent 55%),
        #060818 !important;
    min-height: 100vh;
}
.block-container { padding: 2rem 1.5rem 3rem !important; max-width: 720px !important; }
#MainMenu, footer, header { visibility: hidden; }
.hero { text-align: center; padding: 1.5rem 0 1rem; }
.hero-badge {
    display: inline-flex; align-items: center; gap: 6px;
    background: rgba(99,57,242,0.18); border: 1px solid rgba(139,92,246,0.35);
    border-radius: 999px; padding: 6px 18px; font-size: 0.7rem; font-weight: 700;
    color: #c4b5fd; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 1.2rem;
}
.hero-title {
    font-size: 2.8rem; font-weight: 800; line-height: 1.1; letter-spacing: -1.5px; margin-bottom: 0.7rem;
    background: linear-gradient(135deg, #ffffff 30%, #a78bfa 70%, #34d399 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}
.hero-sub { color: #64748b; font-size: 0.95rem; font-weight: 500; line-height: 1.6; max-width: 440px; margin: 0 auto 1.8rem; }
.stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.9rem; margin-bottom: 1.8rem; }
.stat { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.07); border-radius: 18px; padding: 1.1rem 0.8rem; text-align: center; position: relative; overflow: hidden; }
.stat::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px; border-radius: 2px 2px 0 0; }
.stat.purple::before { background: linear-gradient(90deg, #7c3aed, #a78bfa); }
.stat.green::before  { background: linear-gradient(90deg, #059669, #34d399); }
.stat.red::before    { background: linear-gradient(90deg, #dc2626, #f87171); }
.stat-n { font-size: 2rem; font-weight: 800; letter-spacing: -1px; }
.stat-n.purple { color: #a78bfa; } .stat-n.green { color: #34d399; } .stat-n.red { color: #f87171; }
.stat-l { font-size: 0.62rem; font-weight: 700; text-transform: uppercase; letter-spacing: 2px; color: #334155; margin-top: 3px; }
.input-card { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 24px; padding: 1.8rem; backdrop-filter: blur(20px); }
.input-card-label { font-size: 0.68rem; font-weight: 700; text-transform: uppercase; letter-spacing: 2px; color: #475569; margin-bottom: 10px; display: flex; align-items: center; gap: 8px; }
.input-card-label::before { content: ''; display: inline-block; width: 6px; height: 6px; border-radius: 50%; background: #7c3aed; }
.char-count { font-size: 0.68rem; color: #334155; text-align: right; margin-top: 4px; }
.char-warn  { color: #f87171 !important; }
.stTextArea > div > div > textarea {
    background: rgba(7,5,30,0.7) !important; color: #e2e8f0 !important;
    border: 1.5px solid rgba(255,255,255,0.08) !important; border-radius: 16px !important;
    font-size: 0.97rem !important; font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 500 !important; padding: 16px 18px !important; line-height: 1.7 !important;
    caret-color: #a78bfa !important; resize: none !important;
}
.stTextArea > div > div > textarea::placeholder { color: #1e293b !important; }
.stTextArea > div > div > textarea:hover {
    border-color: rgba(139,92,246,0.45) !important; background: rgba(99,57,242,0.07) !important;
    box-shadow: 0 0 0 4px rgba(99,57,242,0.08) !important;
}
.stTextArea > div > div > textarea:focus {
    border-color: rgba(139,92,246,0.8) !important; background: rgba(99,57,242,0.09) !important;
    box-shadow: 0 0 0 5px rgba(99,57,242,0.15) !important; outline: none !important;
}
.stButton > button {
    width: 100% !important; background: linear-gradient(135deg, #6d28d9 0%, #4f46e5 100%) !important;
    color: #ffffff !important; border: none !important; border-radius: 14px !important;
    padding: 0.9rem 1.5rem !important; font-size: 0.97rem !important; font-weight: 700 !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important; margin-top: 1rem !important;
    box-shadow: 0 4px 24px rgba(99,57,242,0.35) !important; transition: all 0.25s !important;
}
.stButton > button:hover { transform: translateY(-2px) !important; box-shadow: 0 8px 32px rgba(99,57,242,0.55) !important; }
.result { border-radius: 20px; padding: 2rem 1.5rem; text-align: center; margin: 1.4rem 0; animation: popIn 0.5s cubic-bezier(0.175,0.885,0.32,1.275) both; }
.result-fake { background: linear-gradient(135deg, rgba(220,38,38,0.1), rgba(239,68,68,0.05)); border: 1.5px solid rgba(239,68,68,0.4); box-shadow: 0 0 40px rgba(239,68,68,0.1); }
.result-true { background: linear-gradient(135deg, rgba(16,185,129,0.1), rgba(52,211,153,0.05)); border: 1.5px solid rgba(52,211,153,0.4); box-shadow: 0 0 40px rgba(52,211,153,0.1); }
.result-icon { font-size: 3rem; margin-bottom: 0.6rem; display: block; }
.result-tag { display: inline-block; border-radius: 999px; padding: 4px 14px; font-size: 0.65rem; font-weight: 800; letter-spacing: 2.5px; text-transform: uppercase; margin-bottom: 0.8rem; }
.result-tag-fake { background: rgba(239,68,68,0.15); color: #fca5a5; border: 1px solid rgba(239,68,68,0.3); }
.result-tag-true { background: rgba(52,211,153,0.15); color: #6ee7b7; border: 1px solid rgba(52,211,153,0.3); }
.result-label-fake { font-size: 1.55rem; font-weight: 800; color: #f87171; letter-spacing: -0.5px; margin-bottom: 0.5rem; }
.result-label-true { font-size: 1.55rem; font-weight: 800; color: #34d399; letter-spacing: -0.5px; margin-bottom: 0.5rem; }
.result-desc { color: #475569; font-size: 0.85rem; line-height: 1.6; font-weight: 500; }
.divider { height: 1px; background: linear-gradient(90deg, transparent, rgba(255,255,255,0.06), transparent); margin: 1.5rem 0; }
.ex-section-title { font-size: 0.62rem; font-weight: 800; text-transform: uppercase; letter-spacing: 2.5px; color: #334155; margin-bottom: 0.9rem; }
.ex-group-label { font-size: 0.75rem; font-weight: 700; margin-bottom: 8px; }
.ex-group-label.fake { color: #f87171; } .ex-group-label.cred { color: #34d399; }
.chip { display: inline-block; border-radius: 10px; padding: 6px 13px; font-size: 0.76rem; font-weight: 600; margin: 3px 3px 3px 0; }
.chip-f { background: rgba(239,68,68,0.08); border: 1px solid rgba(239,68,68,0.2); color: #fca5a5; }
.chip-t { background: rgba(52,211,153,0.08); border: 1px solid rgba(52,211,153,0.2); color: #6ee7b7; }
.h-section-title { font-size: 0.62rem; font-weight: 800; text-transform: uppercase; letter-spacing: 2.5px; color: #334155; margin-bottom: 0.8rem; }
.h-item { display: flex; align-items: center; gap: 10px; border-radius: 12px; padding: 11px 15px; margin-bottom: 7px; font-size: 0.85rem; font-weight: 500; color: #94a3b8; }
.h-fake { background: rgba(239,68,68,0.06); border-left: 2.5px solid #ef4444; }
.h-true { background: rgba(52,211,153,0.06); border-left: 2.5px solid #34d399; }
.footer { text-align: center; padding: 2.5rem 0 1rem; border-top: 1px solid rgba(255,255,255,0.05); margin-top: 2rem; }
.footer-logo { font-size: 1rem; font-weight: 800; color: #e2e8f0; margin-bottom: 4px; }
.footer-sub { font-size: 0.75rem; color: #1e293b; font-weight: 500; line-height: 1.8; }
.security-badge { display: inline-flex; align-items: center; gap: 5px; background: rgba(52,211,153,0.08); border: 1px solid rgba(52,211,153,0.2); border-radius: 999px; padding: 3px 12px; font-size: 0.62rem; font-weight: 700; color: #34d399; letter-spacing: 1.5px; text-transform: uppercase; margin-left: 8px; }
@keyframes popIn { 0% { opacity:0; transform: scale(0.88) translateY(14px); } 100% { opacity:1; transform: scale(1) translateY(0); } }
</style>
""", unsafe_allow_html=True)

# ── SECURITY: Input Validation ──────────────────────────────────────────────────
def validate_input(text: str) -> tuple[bool, str]:
    """Validate and sanitize user input."""
    text = text.strip()
    if len(text) < MIN_CHARS:
        return False, f"Claim too short. Minimum {MIN_CHARS} characters required."
    if len(text) > MAX_CHARS:
        return False, f"Claim too long. Maximum {MAX_CHARS} characters allowed."
    if not ALLOWED_PATTERN.match(text):
        return False, "Invalid characters detected. Only letters, numbers, and basic punctuation allowed."
    return True, text

def sanitize_display(text: str) -> str:
    """Escape HTML to prevent XSS."""
    return html.escape(text)

# ── Load Model ──────────────────────────────────────────────────────────────────
@st.cache_resource
def load_model():
    try:
        import os
        m = joblib.load("svm_model.pkl")
        v = joblib.load("tfidf_vectorizer.pkl")
        logging.info("Model loaded successfully.")
        return m, v
    except FileNotFoundError as e:
        logging.error(f"Model file not found: {e}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error loading model: {e}")
        raise

try:
    model, vectorizer = load_model()
    model_ok = True
except Exception as e:
    model_ok = False
    st.error("Model load nahi hua. Please check model files.")

# ── Session State ───────────────────────────────────────────────────────────────
for key, val in [("history",[]),("total",0),("fake",0),("cred",0)]:
    if key not in st.session_state:
        st.session_state[key] = val

# ── HERO ────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <div>
        <span class="hero-badge">🔬 AI Powered Detection</span>
        <span class="security-badge">🔒 Secured</span>
    </div>
    <div class="hero-title">Health Claim<br>Checker</div>
    <div class="hero-sub">Instantly detect if any health claim is medically credible or dangerous misinformation — powered by Machine Learning.</div>
</div>
""", unsafe_allow_html=True)

# ── STATS ───────────────────────────────────────────────────────────────────────
st.markdown(
    '<div class="stats">'
    '<div class="stat purple"><div class="stat-n purple">' + str(st.session_state.total) + '</div><div class="stat-l">Checked</div></div>'
    '<div class="stat green"><div class="stat-n green">'  + str(st.session_state.cred)  + '</div><div class="stat-l">Credible</div></div>'
    '<div class="stat red"><div class="stat-n red">'      + str(st.session_state.fake)  + '</div><div class="stat-l">Misinformation</div></div>'
    '</div>', unsafe_allow_html=True)

# ── INPUT ───────────────────────────────────────────────────────────────────────
st.markdown('<div class="input-card"><div class="input-card-label">Enter Health Claim</div>', unsafe_allow_html=True)
user_input = st.text_area("x", placeholder="Type or paste a health claim here...", height=130, max_chars=MAX_CHARS, label_visibility="collapsed")

char_count = len(user_input)
char_class = "char-warn" if char_count > MAX_CHARS * 0.9 else ""
st.markdown(f'<div class="char-count {char_class}">{char_count} / {MAX_CHARS}</div>', unsafe_allow_html=True)

btn = st.button("🔍   Analyze Claim", use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# ── PREDICTION ──────────────────────────────────────────────────────────────────
if btn:
    if not model_ok:
        st.error("Model not available. Please contact administrator.")
        logging.warning("Prediction attempted without loaded model.")
    else:
        is_valid, result_or_error = validate_input(user_input)
        if not is_valid:
            st.warning(f"⚠️ {result_or_error}")
        else:
            clean_input = result_or_error
            try:
                with st.spinner("Analyzing..."):
                    time.sleep(0.5)
                vec_input = vectorizer.transform([clean_input.lower()])
                pred = model.predict(vec_input)[0]
                st.session_state.total += 1
                logging.info(f"Prediction made | Input length: {len(clean_input)} | Result: {'Misinformation' if pred==0 else 'Credible'}")

                if pred == 0:
                    st.session_state.fake += 1
                    st.markdown("""
                    <div class="result result-fake">
                        <span class="result-icon">🚨</span>
                        <div><span class="result-tag result-tag-fake">Warning</span></div>
                        <div class="result-label-fake">Misinformation Detected</div>
                        <div class="result-desc">This claim appears to be medically false or misleading.<br>Always verify with certified medical professionals or trusted health organizations.</div>
                    </div>""", unsafe_allow_html=True)
                    st.session_state.history.insert(0, ("❌", sanitize_display(clean_input), "f"))
                else:
                    st.session_state.cred += 1
                    st.markdown("""
                    <div class="result result-true">
                        <span class="result-icon">✅</span>
                        <div><span class="result-tag result-tag-true">Verified</span></div>
                        <div class="result-label-true">Credible Claim</div>
                        <div class="result-desc">This claim appears to be medically accurate and evidence-based.<br>It aligns with established scientific and medical knowledge.</div>
                    </div>""", unsafe_allow_html=True)
                    st.session_state.history.insert(0, ("✅", sanitize_display(clean_input), "t"))

            except Exception as e:
                logging.error(f"Prediction error: {e}")
                st.error("An error occurred during analysis. Please try again.")

# ── DIVIDER & EXAMPLES ──────────────────────────────────────────────────────────
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
st.markdown('<div class="ex-section-title">Try These Examples</div>', unsafe_allow_html=True)
c1, c2 = st.columns(2)
with c1:
    st.markdown("""<div class="ex-group-label fake">❌ Misinformation</div>
    <span class="chip chip-f">5G spreads coronavirus</span>
    <span class="chip chip-f">Bleach cures COVID-19</span>
    <span class="chip chip-f">Vaccines cause autism</span>
    <span class="chip chip-f">Magnets cure arthritis</span>""", unsafe_allow_html=True)
with c2:
    st.markdown("""<div class="ex-group-label cred">✅ Credible</div>
    <span class="chip chip-t">Exercise reduces heart disease</span>
    <span class="chip chip-t">Smoking causes lung cancer</span>
    <span class="chip chip-t">Handwashing prevents infections</span>
    <span class="chip chip-t">Vaccines are safe and effective</span>""", unsafe_allow_html=True)

# ── HISTORY ─────────────────────────────────────────────────────────────────────
if st.session_state.history:
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="h-section-title">Recent Checks</div>', unsafe_allow_html=True)
    for icon, claim, label in st.session_state.history[:5]:
        css = "h-true" if label == "t" else "h-fake"
        short = claim[:68] + "..." if len(claim) > 68 else claim
        st.markdown(f'<div class="h-item {css}"><span>{icon}</span><span>{short}</span></div>', unsafe_allow_html=True)
    if st.button("🗑  Clear History"):
        for k, v in [("history",[]),("total",0),("fake",0),("cred",0)]:
            st.session_state[k] = v
        st.rerun()

# ── FOOTER ───────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="footer">
    <div class="footer-logo">🏥 Health Claim Checker</div>
    <div class="footer-sub">SoftaVerse Tech House &nbsp;·&nbsp; AI Health Misinformation Detection<br>
    Python &nbsp;·&nbsp; Scikit-learn &nbsp;·&nbsp; Streamlit &nbsp;·&nbsp; NLP &nbsp;·&nbsp; 🔒 Security Hardened v2.0</div>
</div>""", unsafe_allow_html=True)
