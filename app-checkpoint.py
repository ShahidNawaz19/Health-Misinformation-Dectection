
import streamlit as st
import joblib
import time
from scipy.sparse import hstack, csr_matrix
 
st.set_page_config(
    page_title="Health Claim Checker",
    page_icon="🏥",
    layout="centered"
)
 
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;900&display=swap');
 
* { box-sizing: border-box; }
 
html, body, [class*="css"], .stApp {
    font-family: 'Inter', sans-serif !important;
    background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%) !important;
}
 
.block-container {
    padding: 1.5rem 1.5rem 2rem 1.5rem !important;
    max-width: 780px !important;
}
 
#MainMenu, footer, header { visibility: hidden; }
 
.hero-title {
    text-align: center;
    font-size: 2.6rem;
    font-weight: 900;
    background: linear-gradient(90deg, #a78bfa, #60a5fa, #34d399);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -1px;
    margin-bottom: 0.4rem;
}
 
.hero-sub {
    text-align: center;
    color: #94a3b8;
    font-size: 0.95rem;
    margin-bottom: 1.5rem;
}
 
.badge-wrap { text-align: center; margin-bottom: 0.8rem; }
 
.badge {
    display: inline-block;
    background: rgba(167,139,250,0.15);
    border: 1px solid rgba(167,139,250,0.4);
    color: #a78bfa;
    border-radius: 999px;
    padding: 4px 16px;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
}
 
.stats-row {
    display: flex;
    gap: 0.8rem;
    margin-bottom: 1.2rem;
}
 
.stat-box {
    flex: 1;
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 14px;
    padding: 1rem;
    text-align: center;
}
 
.stat-num { font-size: 1.8rem; font-weight: 900; }
.stat-num.purple { color: #a78bfa; }
.stat-num.green  { color: #34d399; }
.stat-num.red    { color: #f87171; }
.stat-lbl {
    color: #475569;
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    margin-top: 2px;
}
 
.input-lbl {
    color: #64748b;
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-bottom: 6px;
}
 
.stTextArea > div > div > textarea {
    background-color: #1e1b4b !important;
    color: #e2e8f0 !important;
    border: 1.5px solid rgba(255,255,255,0.12) !important;
    border-radius: 14px !important;
    font-size: 0.97rem !important;
    font-family: 'Inter', sans-serif !important;
    padding: 14px 16px !important;
    caret-color: #a78bfa !important;
}
 
.stTextArea > div > div > textarea:focus {
    border-color: #a78bfa !important;
    background-color: #1a1740 !important;
    box-shadow: 0 0 0 4px rgba(167,139,250,0.18) !important;
}
 
.stTextArea > div > div > textarea::placeholder {
    color: #475569 !important;
}
 
.stButton > button {
    width: 100% !important;
    background: linear-gradient(135deg, #7c3aed, #4f46e5) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 0.8rem !important;
    font-size: 1rem !important;
    font-weight: 700 !important;
    margin-top: 0.6rem !important;
    transition: all 0.2s ease !important;
}
 
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 25px rgba(124,58,237,0.45) !important;
}
 
.result-box {
    border-radius: 16px;
    padding: 1.5rem;
    text-align: center;
    margin: 1rem 0;
    animation: popIn 0.4s cubic-bezier(0.175,0.885,0.32,1.275);
}
 
.result-fake {
    background: rgba(239,68,68,0.1);
    border: 2px solid rgba(239,68,68,0.5);
}
 
.result-true {
    background: rgba(52,211,153,0.1);
    border: 2px solid rgba(52,211,153,0.5);
}
 
.result-icon { font-size: 2.8rem; }
 
.result-lbl-fake {
    font-size: 1.4rem;
    font-weight: 900;
    color: #f87171;
    margin: 0.3rem 0;
}
 
.result-lbl-true {
    font-size: 1.4rem;
    font-weight: 900;
    color: #34d399;
    margin: 0.3rem 0;
}
 
.result-desc {
    color: #64748b;
    font-size: 0.85rem;
    line-height: 1.5;
}
 
.ex-title {
    color: #475569;
    font-size: 0.68rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin: 1rem 0 0.5rem;
}
 
.ex-sub {
    font-size: 0.75rem;
    font-weight: 700;
    margin-bottom: 5px;
}
 
.ex-sub.red   { color: #f87171; }
.ex-sub.green { color: #34d399; }
 
.chip {
    display: inline-block;
    border-radius: 999px;
    padding: 4px 12px;
    font-size: 0.75rem;
    margin: 3px 2px;
}
 
.chip-f {
    background: rgba(239,68,68,0.1);
    border: 1px solid rgba(239,68,68,0.3);
    color: #fca5a5;
}
 
.chip-t {
    background: rgba(52,211,153,0.1);
    border: 1px solid rgba(52,211,153,0.3);
    color: #6ee7b7;
}
 
.h-title {
    color: #475569;
    font-size: 0.68rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin: 1rem 0 0.5rem;
}
 
.h-item {
    border-radius: 10px;
    padding: 9px 13px;
    margin-bottom: 6px;
    font-size: 0.84rem;
    color: #cbd5e1;
}
 
.h-f { background: rgba(239,68,68,0.08); border-left: 3px solid #ef4444; }
.h-t { background: rgba(52,211,153,0.08); border-left: 3px solid #34d399; }
 
.footer {
    text-align: center;
    color: #1e293b;
    font-size: 0.72rem;
    margin-top: 1.5rem;
}
 
@keyframes popIn {
    from { opacity:0; transform: scale(0.9) translateY(10px); }
    to   { opacity:1; transform: scale(1) translateY(0); }
}
</style>
""", unsafe_allow_html=True)
 
 
@st.cache_resource
def load_model():
    base = r"C:\Users\LENOVO\Desktop\datascience project"
    m = joblib.load(f"{base}\\svm_model.pkl")
    v = joblib.load(f"{base}\\tfidf_vectorizer.pkl")
    return m, v
 
try:
    model, vectorizer = load_model()
    model_ok = True
except Exception as e:
    model_ok = False
    st.error(f"Model load nahi hua: {e}")
 
for key, val in [("history",[]),("total",0),("fake",0),("cred",0)]:
    if key not in st.session_state:
        st.session_state[key] = val
 
st.markdown("""
<div class="badge-wrap"><span class="badge">🔬 AI Powered</span></div>
<div class="hero-title">Health Claim Checker</div>
<div class="hero-sub">Paste any health claim — AI will detect if it's misinformation or credible</div>
""", unsafe_allow_html=True)
 
st.markdown(f"""
<div class="stats-row">
    <div class="stat-box">
        <div class="stat-num purple">{st.session_state.total}</div>
        <div class="stat-lbl">Checked</div>
    </div>
    <div class="stat-box">
        <div class="stat-num green">{st.session_state.cred}</div>
        <div class="stat-lbl">Credible</div>
    </div>
    <div class="stat-box">
        <div class="stat-num red">{st.session_state.fake}</div>
        <div class="stat-lbl">Misinformation</div>
    </div>
</div>
""", unsafe_allow_html=True)
 
st.markdown('<div class="input-lbl">Enter Health Claim</div>', unsafe_allow_html=True)
user_input = st.text_area(
    label="claim",
    placeholder="e.g. Drinking bleach cures COVID-19...",
    height=120,
    label_visibility="collapsed"
)
btn = st.button("🔍  Analyze Claim", use_container_width=True)
 
if btn:
    if not user_input.strip():
        st.warning("Pehle koi health claim likho!")
    elif not model_ok:
        st.error("Model load nahi hua.")
    else:
        with st.spinner("Analyzing..."):
            time.sleep(0.4)
 
        claim_text = user_input.lower().strip()
 
        extra = {
            "word_count": len(claim_text.split()),
            "has_numbers": int(any(c.isdigit() for c in claim_text)),
            "has_exclamation": int("!" in claim_text),
            "has_question": int("?" in claim_text),
            "credibility_keyword_count": sum(1 for w in ["research","study","evidence","clinical","trial","proven","expert","doctor","hospital"] if w in claim_text),
            "misinfo_keyword_count": sum(1 for w in ["secret","shocking","cure","detox","miracle","suppressed","hidden","poison","scam","truth"] if w in claim_text),
        }
 
        X_text = vectorizer.transform([claim_text])
        X_extra = csr_matrix([[extra["word_count"], extra["has_numbers"],
                               extra["has_exclamation"], extra["has_question"],
                               extra["credibility_keyword_count"], extra["misinfo_keyword_count"]]])
        X_input = hstack([X_text, X_extra])
 
        pred = model.predict(X_input)[0]
        st.session_state.total += 1
 
        if pred == 1:
            st.session_state.fake += 1
            st.markdown("""
            <div class="result-box result-fake">
                <div class="result-icon">🚨</div>
                <div class="result-lbl-fake">MISINFORMATION DETECTED</div>
                <div class="result-desc">This claim appears to be false or misleading.<br>Always verify with trusted medical sources.</div>
            </div>""", unsafe_allow_html=True)
            st.session_state.history.insert(0, ("❌", user_input.strip(), "f"))
        else:
            st.session_state.cred += 1
            st.markdown("""
            <div class="result-box result-true">
                <div class="result-icon">✅</div>
                <div class="result-lbl-true">CREDIBLE CLAIM</div>
                <div class="result-desc">This claim appears to be medically accurate<br>and evidence-based.</div>
            </div>""", unsafe_allow_html=True)
            st.session_state.history.insert(0, ("✅", user_input.strip(), "t"))
 
        st.rerun()
 
st.markdown('<div class="ex-title">Try These Examples</div>', unsafe_allow_html=True)
c1, c2 = st.columns(2)
with c1:
    st.markdown("""
    <div class="ex-sub red">❌ Misinformation</div>
    <span class="chip chip-f">5G spreads coronavirus</span>
    <span class="chip chip-f">Bleach cures COVID</span>
    <span class="chip chip-f">Vaccines cause autism</span>
    <span class="chip chip-f">Magnets cure arthritis</span>
    """, unsafe_allow_html=True)
with c2:
    st.markdown("""
    <div class="ex-sub green">✅ Credible</div>
    <span class="chip chip-t">Exercise reduces heart disease</span>
    <span class="chip chip-t">Smoking causes lung cancer</span>
    <span class="chip chip-t">Handwashing prevents infections</span>
    <span class="chip chip-t">Vaccines are safe and effective</span>
    """, unsafe_allow_html=True)
 
if st.session_state.history:
    st.markdown('<div class="h-title">Recent Checks</div>', unsafe_allow_html=True)
    for icon, claim, label in st.session_state.history[:5]:
        css = "h-t" if label == "t" else "h-f"
        short = claim[:72] + "..." if len(claim) > 72 else claim
        st.markdown(f'<div class="h-item {css}">{icon} {short}</div>', unsafe_allow_html=True)
 
    if st.button("🗑️ Clear History"):
        for k, v in [("history",[]),("total",0),("fake",0),("cred",0)]:
            st.session_state[k] = v
        st.rerun()
 
st.markdown("""
<div class="footer">
    🏥 <strong>Health Claim Checker</strong><br>
    SoftaVerse Tech House · AI Health Misinformation Detection<br>
    Built with Python, Scikit-learn & Streamlit
</div>
""", unsafe_allow_html=True)