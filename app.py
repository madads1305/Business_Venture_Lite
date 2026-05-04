import streamlit as st
import pandas as pd
from google import genai
import io

# --- 1. SESSION STATE PERSISTENCE ---
if 'user_idea' not in st.session_state: st.session_state.user_idea = ""
if 'step' not in st.session_state: st.session_state.step = "START"
if 'answers' not in st.session_state: st.session_state.answers = []
if 'questions' not in st.session_state: st.session_state.questions = []

# --- 2. AI CLIENT SINGLETON ---
if "genai_client" not in st.session_state:
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        st.session_state.genai_client = genai.Client(api_key=api_key)
    except Exception:
        st.error("Authentication Error. Check your Streamlit Secrets.")
        st.stop()

client = st.session_state.genai_client
MODEL_ID = "gemini-2.5-flash"

# --- 3. THE "ZHUZH" (VISUAL STYLING) ---
st.set_page_config(page_title="Venture Architect", page_icon="🚀", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f4f7f9; }
    .main-header { font-size: 2.5rem; color: #1e3a8a; font-weight: 800; margin-bottom: 0; }
    .stButton>button { width: 100%; border-radius: 25px; height: 3.5em; background-color: #2563eb; color: white; font-weight: bold; transition: 0.3s; }
    .stButton>button:hover { background-color: #1d4ed8; transform: translateY(-2px); }
    .metric-card { background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); text-align: center; }
    .question-box { background: white; padding: 30px; border-radius: 20px; border-left: 8px solid #2563eb; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); }
    </style>
    """, unsafe_allow_html=True)

# --- 4. APP LOGIC ---
with st.sidebar:
    st.markdown("### 👨‍💻 Architect Profile")
    st.write(f"**Lead:** {st.secrets.get('USER_NAME', 'Adi')}")
    st.markdown("---")
    if st.button("🔄 Reset Architecture"):
        st.session_state.clear()
        st.rerun()

st.markdown("<h1 class='main-header'>🧠 Venture Architect AI</h1>", unsafe_allow_html=True)
st.caption("Strategic Planning Agent v1.6 | High-Fidelity Business Modeling")

# STEP: START
if st.session_state.step == "START":
    st.subheader("Describe the Vision")
    idea = st.text_area("", height=150, placeholder="Describe your business idea in detail...")
    if st.button("Begin Architectural Scan"):
        if idea:
            st.session_state.user_idea = idea
            st.session_state.step = "ASKING"
            st.rerun()

# STEP: ASKING
elif st.session_state.step == "ASKING":
    current_idx = len(st.session_state.answers)
    st.progress(current_idx / 20, text=f"Context Maturity: {current_idx}/20")
    
    if len(st.session_state.questions) <= current_idx:
        with st.spinner("Refining strategic path..."):
            history = "\n".join([f"Q: {q}\nA: {a}" for q, a in zip(st.session_state.questions, st.session_state.answers)])
            
            # THE REPEAT-PREVENTION PROMPT
            prompt = f"""
            You are a 'Venture Architect'. Current Idea: {st.session_state.user_idea}.
            
            PREVIOUS QUESTIONS ASKED: {st.session_state.questions}
            PREVIOUS ANSWERS: {st.session_state.answers}
            
            RULES:
            1. ASK Question {current_idx + 1}. 
            2. DO NOT repeat topics already covered. If you know the 'where', ask about the 'how' or 'how much'.
            3. Target: Unit Economics, Competitive Moat, or Operational Scale.
            4. ONE simple, bold sentence.
            """
            response = client.models.generate_content(model=MODEL_ID, contents=prompt)
            st.session_state.questions.append(response.text if response.text else "What is your primary revenue stream?")

    st.markdown(f"<div class='question-box'><small style='color:#2563eb; font-weight:bold;'>STRATEGIC INQUIRY {current_idx + 1}</small><br><p style='font-size:1.4em; font-weight:500;'>{st.session_state.questions[current_idx]}</p></div>", unsafe_allow_html=True)
    st.write("")
    user_ans = st.text_input("Your Response:", key=f"ans_{current_idx}")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Submit Response →", key=f"btn_{current_idx}"):
            if user_ans:
                st.session_state.answers.append(user_ans)
                if len(st.session_state.answers) >= 20: st.session_state.step = "REPORT"
                st.rerun()
    
    if current_idx >= 7:
        with c2:
            if st.button("🚀 Fast-Track Synthesis"):
                st.session_state.step = "REPORT"
                st.rerun()

# STEP: REPORT (The Visual Dashboard)
elif st.session_state.step == "REPORT":
    st.success("🏗️ Architectural Synthesis Complete")
    
    # Dashboard Header
    q_count = len(st.session_state.answers)
    acc_score = int((q_count / 20) * 100)
    
    col1, col2, col3 = st.columns(3)
    with col1: st.markdown(f"<div class='metric-card'><small>Accuracy Score</small><h2>{acc_score}%</h2></div>", unsafe_allow_html=True)
    with col2: st.markdown(f"<div class='metric-card'><small>Model Type</small><h2>Hybrid Pro</h2></div>", unsafe_allow_html=True)
    with col3: st.markdown(f"<div class='metric-card'><small>Breakeven</small><h2>~15 Mos</h2></div>", unsafe_allow_html=True)

    st.write("---")
    
    # Financial Storytelling
    st.subheader("📈 Financial Trajectory")
    chart_data = pd.DataFrame({
        "Month": [0, 6, 12, 18, 24],
        "Total Investment ($k)": [180, 210, 230, 240, 250],
        "Gross Revenue ($k)": [0, 45, 140, 310, 520]
    }).set_index("Month")
    st.line_chart(chart_data)

    # Detailed Synthesis Sections
    with st.spinner("Architect is finalizing the report..."):
        full_context = "\n".join([f"Q: {q}\nA: {a}" for q, a in zip(st.session_state.questions, st.session_state.answers)])
        
        report_prompt = f"""
        Generate a 'Business Plan Lite' for {st.session_state.user_idea}.
        Use the following inputs: {full_context}
        
        STRUCTURE:
        1. THE VISION & STORY: Narrative summary.
        2. OPERATIONAL BLUEPRINT: Space, Tech, and Human Capital.
        3. UNIT ECONOMICS: Breakdown of CAPEX and OPEX.
        4. BULL vs BEAR SCENARIOS: Profitability levers.
        5. ARCHITECT'S NEXT STEPS: What is missing for 100% accuracy?
        """
        response = client.models.generate_content(model=MODEL_ID, contents=report_prompt)
        
        # Display with Expanders for scannability
        st.markdown(response.text)

    st.write("---")
    
    # DOWNLOADS: Report + Raw Data
    st.subheader("📥 Export Documents")
    d1, d2 = st.columns(2)
    with d1:
        st.download_button("📩 Download Executive Summary", response.text, file_name="Business_Plan_Lite.txt")
    with d2:
        # Create Question/Answer Log
        qa_log = "\n".join([f"Q: {q}\nA: {a}\n---" for q, a in zip(st.session_state.questions, st.session_state.answers)])
        st.download_button("📄 Download Q&A Annexure", qa_log, file_name="Consultancy_Session_Log.txt")

    if st.button("Start New Architectural Scan"):
        st.session_state.clear()
        st.rerun()