import streamlit as st
import pandas as pd
from google import genai

# --- 1. SESSION STATE PERSISTENCE (Mobile & Logic Stability) ---
if 'user_idea' not in st.session_state:
    st.session_state.user_idea = ""
if "step" not in st.session_state:
    st.session_state.step = "START"
if "answers" not in st.session_state:
    st.session_state.answers = []
if "questions" not in st.session_state:
    st.session_state.questions = []

# --- 2. THE AI CLIENT SINGLETON ---
if "genai_client" not in st.session_state:
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        st.session_state.genai_client = genai.Client(api_key=api_key)
    except Exception:
        st.error("Authentication Error. Check your Streamlit Secrets.")
        st.stop()

client = st.session_state.genai_client
MODEL_ID = "gemini-2.5-flash"

# --- 3. STYLING & UI ---
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
    .report-section { background: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

with st.sidebar:
    st.title("👨‍💻 Architect Profile")
    st.markdown(f"**Lead Consultant:** {st.secrets.get('USER_NAME', 'Adi')}")
    st.write("---")
    st.info("The 'Fast-Track' option becomes available after 7 questions once a baseline model is established.")
    if st.button("Reset Session"):
        st.session_state.clear()
        st.rerun()

# --- 4. APP FLOW ---
st.title("🧠 Venture Architect AI")
st.caption("Strategic Planning Agent v1.5 | High-Level Business Modeling")

# STEP: START
if st.session_state.step == "START":
    st.subheader("The Genesis")
    idea = st.text_area("Describe your business idea...", height=150, placeholder="e.g., A high-end racing simulator arcade in downtown Ottawa...")
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
        with st.spinner("Architect is analyzing business ambition..."):
            try:
                recent_history = "\n".join([f"Q: {q}\nA: {a}" for q, a in zip(st.session_state.questions[-5:], st.session_state.answers[-5:])])
                
                # FIXED: Targeted Business Questions instead of "feelings"
                prompt = f"""
                You are a 'Venture Architect' host. Help a user build a professional plan for: {st.session_state.user_idea}
                Recent Context: {recent_history}
                
                RULES:
                1. Ask Question {current_idx + 1} of 20.
                2. FOCUS on BUSINESS REQUIREMENTS (Scale, CAPEX, revenue model, or operational footprint).
                3. NO questions about user feelings, emotions, or "what you enjoy".
                4. ONE simple sentence. DO NOT explain reasoning.
                """
                response = client.models.generate_content(model=MODEL_ID, contents=prompt)
                st.session_state.questions.append(response.text if response.text else "What is your target revenue for Year 1?")
            except Exception as e:
                st.error("Connection hiccup. Please try clicking Retry.")
                if st.button("Retry"): st.rerun()
                st.stop()

    st.markdown(f"<div class='question-card'><small style='color:#007bff;font-weight:bold;'>STRATEGIC INQUIRY {current_idx + 1}</small><p style='font-size:1.2em;margin-top:10px;'>{st.session_state.questions[current_idx]}</p></div>", unsafe_allow_html=True)
    st.write("") 
    user_ans = st.text_input("Your Response:", key=f"input_{current_idx}")

    col1, col2 = st.columns([1, 1])
    with col1:
        btn_container = st.empty()
        if btn_container.button("Submit Response →", key=f"btn_{current_idx}"):
            if user_ans:
                btn_container.empty()
                st.session_state.answers.append(user_ans)
                if len(st.session_state.answers) >= 20: st.session_state.step = "REPORT"
                st.rerun()

    if current_idx >= 7:
        st.info("💡 **Architect's Insight:** Data baseline reached. Ready for synthesis?")
        if st.button("🚀 Fast-Track: Generate Strategic Synthesis"):
            st.session_state.step = "REPORT"
            st.rerun()

# STEP: REPORT (The Dashboard)
elif st.session_state.step == "REPORT":
    st.warning("⚠️ **DISCLAIMER:** This report is based on user inputs and AI modeling. It is intended for high-level tangibility, not final financial advice.")
    
    q_count = len(st.session_state.answers)
    acc_score = int((q_count / 20) * 100)
    
    # 1. DASHBOARD METRICS
    m1, m2, m3 = st.columns(3)
    m1.metric("Accuracy Score", f"{acc_score}%")
    m2.metric("Market Fit", "Indicative High")
    m3.metric("Est. Breakeven", "12-18 Months")

    # 2. BREAKEVEN VISUAL
    st.subheader("📈 Financial Path to Breakeven (Indicative)")
    chart_data = pd.DataFrame({
        "Month": [0, 6, 12, 18, 24],
        "Accumulated Cost ($k)": [150, 180, 210, 240, 270],
        "Accumulated Revenue ($k)": [0, 40, 120, 250, 450]
    }).set_index("Month")
    st.line_chart(chart_data)

    # 3. THE STORY & DATA
    with st.spinner("Synthesizing Final Executive Summary..."):
        full_context = "\n".join([f"Q: {q}\nA: {a}" for q, a in zip(st.session_state.questions, st.session_state.answers)])
        
        report_prompt = f"""
        Act as a VC Strategist. Generate a structured report for: {st.session_state.user_idea}
        Data: {full_context}
        
        STRUCTURE:
        1. THE STORY: Summarize the business story and core assumptions.
        2. REQUIREMENTS: A list of space, hardware, and staffing needs.
        3. COST MODEL: Estimates for CAPEX and Monthly OPEX.
        4. BULL vs BEAR: A quick 'Scenarios' section for profitability.
        5. ACCURACY GAPS: What specific data is missing to reach 100% accuracy?
        """
        response = client.models.generate_content(model=MODEL_ID, contents=report_prompt)
        st.markdown(response.text)
        st.download_button("📩 Download Report", response.text, file_name="Venture_Report.txt")

    if st.button("Start New Scan"):
        st.session_state.clear()
        st.rerun()