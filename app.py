import streamlit as st
import pandas as pd
from google import genai

# --- 1. SESSION STATE PERSISTENCE ---
# These must be initialized first for mobile stability
if 'user_idea' not in st.session_state:
    st.session_state.user_idea = ""
if "step" not in st.session_state:
    st.session_state.step = "START"
if "answers" not in st.session_state:
    st.session_state.answers = []
if "questions" not in st.session_state:
    st.session_state.questions = []

# --- 2. THE AI CLIENT SINGLETON (The Fix for Connection Hiccups) ---
# This ensures we don't keep re-opening connections to Google on every click
if "genai_client" not in st.session_state:
    try:
        API_KEY = st.secrets["GEMINI_API_KEY"]
        st.session_state.genai_client = genai.Client(api_key=API_KEY)
    except Exception:
        st.error("Authentication Error. Check your Streamlit Secrets.")
        st.stop()

client = st.session_state.genai_client
MODEL_ID = "gemini-2.5-flash"

# --- 3. THE ZHUZH: STYLING & SIDEBAR ---
st.set_page_config(page_title="Venture Architect", page_icon="🚀", layout="wide")

st.markdown("""
    <style>
    .stApp { background: linear-gradient(180deg, #f0f2f6 0%, #ffffff 100%); }
    .stButton>button {
        width: 100%; border-radius: 20px; border: none;
        background-color: #007bff; color: white; font-weight: bold;
        transition: 0.3s; height: 3em;
    }
    .stButton>button:hover { background-color: #0056b3; transform: scale(1.02); }
    .question-card {
        background-color: white; padding: 25px; border-radius: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08); border-left: 5px solid #007bff;
    }
    .fast-track-box {
        background-color: #e3f2fd; padding: 15px; border-radius: 10px;
        border: 1px dashed #007bff; margin-top: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

with st.sidebar:
    st.title("👨‍💻 Architect Profile")
    st.markdown(f"**Lead Consultant:** {st.secrets.get('USER_NAME', 'Adi')}")
    st.markdown("---")
    st.write("Stress-test your business model through 20 strategic, gamified questions.")
    if st.button("Reset Session"):
        st.session_state.clear()
        st.rerun()

# --- 4. MAIN INTERFACE ---
st.title("🧠 Venture Architect AI")
st.caption("Strategic Planning Agent v1.2 | High-Level Indicative Modeling")

# STEP: START
if st.session_state.step == "START":
    st.subheader("The Genesis")
    idea = st.text_area("Describe your business idea...", height=150, placeholder="e.g., Solar-powered heaters for Ottawa transit...")
    if st.button("Begin Architectural Scan"):
        if idea:
            st.session_state.user_idea = idea
            st.session_state.step = "ASKING"
            st.rerun()

# STEP: ASKING
elif st.session_state.step == "ASKING":
    current_q_idx = len(st.session_state.answers)
    st.progress((current_q_idx) / 20, text=f"Context Maturity: {current_q_idx}/20")
    
    # Generate Question if needed
    if len(st.session_state.questions) <= current_q_idx:
        with st.spinner("Analyzing context..."):
            try:
                recent_history = "\n".join([f"Q: {q}\nA: {a}" for q, a in zip(st.session_state.questions[-5:], st.session_state.answers[-5:])])
                
                gamified_prompt = f"""
                You are a 'Venture Architect' host. Help a user build a plan for: {st.session_state.user_idea}
                Context: {recent_history}
                RULES: Ask Question {current_q_idx + 1} of 20. ONE simple sentence. NO jargon.
                Focus on branding or customers. DO NOT explain why you are asking.
                """
                
                response = client.models.generate_content(model=MODEL_ID, contents=gamified_prompt)
                st.session_state.questions.append(response.text if response.text else "Who is your ideal first customer?")
            except Exception:
                st.error("Connection hiccup. Please try clicking Retry.")
                if st.button("Retry"): st.rerun()
                st.stop()

    # Display Question UI
    st.markdown(f"<div class='question-card'><small style='color:#007bff;font-weight:bold;'>STRATEGIC INQUIRY {current_q_idx + 1}</small><p style='font-size:1.2em;margin-top:10px;'>{st.session_state.questions[current_q_idx]}</p></div>", unsafe_allow_html=True)
    st.write("") 
    user_ans = st.text_input("Your Response:", key=f"input_{current_q_idx}")

    col1, col2 = st.columns([1, 1])
    with col1:
        btn_container = st.empty()
        if btn_container.button("Submit Response →", key=f"btn_{current_q_idx}"):
            if user_ans:
                btn_container.empty()
                st.session_state.answers.append(user_ans)
                if len(st.session_state.answers) >= 20:
                    st.session_state.step = "REPORT"
                st.rerun()

    # FAST-TRACK (After 7 Questions)
    if current_q_idx >= 7:
        st.markdown("<div class='fast-track-box'>💡 <b>Architect's Insight:</b> Data baseline reached. Ready for synthesis?</div>", unsafe_allow_html=True)
        if st.button("🚀 Fast-Track: Generate Strategic Synthesis"):
            st.session_state.step = "REPORT"
            st.rerun()

# STEP: REPORT
elif st.session_state.step == "REPORT":
    st.header("📋 Venture Architecture Report")
    
    q_count = len(st.session_state.answers)
    m1, m2, m3 = st.columns(3)
    m1.metric("Data Maturity", f"{int((q_count/20)*100)}%")
    m2.metric("Market Viability", "Indicative High")
    m3.metric("Complexity", "Medium")
    
    chart_data = pd.DataFrame({"Year": ["Y1", "Y2", "Y3", "Y4", "Y5"], "Projection": [10, 35, 85, 170, 300]})
    st.line_chart(chart_data, x="Year")

    with st.spinner("Synthesizing Report..."):
        full_context = "\n".join([f"Q: {q}\nA: {a}" for q, a in zip(st.session_state.questions, st.session_state.answers)])
        report_prompt = f"VC Report for: {st.session_state.user_idea}. Data: {full_context}. Include Summary, Cost Table, Accuracy Score, and Verdict."
        response = client.models.generate_content(model=MODEL_ID, contents=report_prompt)
        st.markdown(response.text)
        st.download_button("📩 Download Report", response.text, file_name="Venture_Report.txt")

    if st.button("New Scan"):
        st.session_state.clear()
        st.rerun()