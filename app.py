import streamlit as st
import pandas as pd
from google import genai
import json

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

# --- 3. UI STYLING ---
st.set_page_config(page_title="Venture Architect", page_icon="🚀", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f4f7f9; }
    .main-header { font-size: 2.5rem; color: #1e3a8a; font-weight: 800; margin-bottom: 5px; }
    .stButton>button { width: 100%; border-radius: 25px; height: 3.5em; background-color: #2563eb; color: white; font-weight: bold; }
    .metric-card { 
        background: white; padding: 15px; border-radius: 12px; 
        box-shadow: 0 2px 4px rgba(0,0,0,0.05); text-align: center; border-top: 4px solid #2563eb;
    }
    .metric-value { font-size: 1.5rem; font-weight: bold; color: #1e3a8a; }
    .metric-label { font-size: 0.8rem; color: #64748b; text-transform: uppercase; }
    .question-box { background: white; padding: 30px; border-radius: 20px; border-left: 8px solid #2563eb; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); }
    </style>
    """, unsafe_allow_html=True)

# --- 4. APP FLOW ---
with st.sidebar:
    st.markdown("### 👨‍💻 Architect Profile")
    st.write(f"**Lead:** {st.secrets.get('USER_NAME', 'Adi')}")
    st.write("---")
    if st.button("🔄 Reset Architecture"):
        st.session_state.clear()
        st.rerun()

st.markdown("<h1 class='main-header'>🧠 Venture Architect AI</h1>", unsafe_allow_html=True)
st.caption("Strategic Planning Agent v1.7 | High-Fidelity Business Modeling")

# STEP: START
if st.session_state.step == "START":
    st.subheader("Describe the Vision")
    idea = st.text_area("", height=150, placeholder="Describe your business idea (e.g., Arcade & Speakeasy in Ottawa)...")
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
        with st.spinner("Architect is refining strategic path..."):
            history = "\n".join([f"Q: {q}\nA: {a}" for q, a in zip(st.session_state.questions, st.session_state.answers)])
            prompt = f"Idea: {st.session_state.user_idea}. History: {history}. Ask Question {current_idx+1}. FOCUS on Business Requirements/Ambition only. No feelings. ONE sentence. DO NOT repeat topics."
            response = client.models.generate_content(model=MODEL_ID, contents=prompt)
            st.session_state.questions.append(response.text if response.text else "What is your Year 1 revenue goal?")

    st.markdown(f"<div class='question-box'><small style='color:#2563eb; font-weight:bold;'>STRATEGIC INQUIRY {current_idx + 1}</small><br><p style='font-size:1.4em;'>{st.session_state.questions[current_idx]}</p></div>", unsafe_allow_html=True)
    st.write("")
    user_ans = st.text_input("Your Response:", key=f"ans_{current_idx}")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Submit Response →", key=f"btn_{current_idx}"):
            if user_ans:
                st.session_state.answers.append(user_ans)
                if len(st.session_state.answers) >= 20: st.session_state.step = "REPORT"
                st.rerun()
    with c2:
        if current_idx >= 7:
            if st.button("🚀 Fast-Track Synthesis"):
                st.session_state.step = "REPORT"
                st.rerun()

# STEP: REPORT
elif st.session_state.step == "REPORT":
    st.warning("⚠️ **DISCLAIMER:** This report is an indicative model based on user inputs. Not a final financial audit.")
    
    with st.spinner("Synthesizing Executive Dashboard..."):
        full_context = "\n".join([f"Q: {q}\nA: {a}" for q, a in zip(st.session_state.questions, st.session_state.answers)])
        
        # We ask the AI to provide a JSON summary first for the tiles, then the full report
        summary_prompt = f"""
        Analyze this business idea: {st.session_state.user_idea}
        Data: {full_context}
        
        Provide a JSON object with these exact keys: 
        "capex" (string, e.g. '$200k'), 
        "opex" (string, e.g. '$15k/mo'), 
        "breakeven" (string, e.g. '18 Mos'), 
        "viability" (string 0-100, e.g. '85%'), 
        "risk" (string, e.g. 'Medium')
        """
        summary_res = client.models.generate_content(model=MODEL_ID, contents=summary_prompt)
        
        # Clean the JSON string from AI response
        json_str = summary_res.text.replace('```json', '').replace('```', '').strip()
        try:
            metrics = json.loads(json_str)
        except:
            metrics = {"capex": "N/A", "opex": "N/A", "breakeven": "N/A", "viability": "N/A", "risk": "N/A"}

    # 1. EXECUTIVE TILES (The Dashboard)
    q_count = len(st.session_state.answers)
    acc_score = int((q_count / 20) * 100)

    t1, t2, t3, t4, t5, t6 = st.columns(6)
    with t1: st.markdown(f"<div class='metric-card'><div class='metric-label'>Accuracy</div><div class='metric-value'>{acc_score}%</div></div>", unsafe_allow_html=True)
    with t2: st.markdown(f"<div class='metric-card'><div class='metric-label'>Est. CAPEX</div><div class='metric-value'>{metrics.get('capex')}</div></div>", unsafe_allow_html=True)
    with t3: st.markdown(f"<div class='metric-card'><div class='metric-label'>Est. OPEX</div><div class='metric-value'>{metrics.get('opex')}</div></div>", unsafe_allow_html=True)
    with t4: st.markdown(f"<div class='metric-card'><div class='metric-label'>Breakeven</div><div class='metric-value'>{metrics.get('breakeven')}</div></div>", unsafe_allow_html=True)
    with t5: st.markdown(f"<div class='metric-card'><div class='metric-label'>Viability</div><div class='metric-value'>{metrics.get('viability')}</div></div>", unsafe_allow_html=True)
    with t6: st.markdown(f"<div class='metric-card'><div class='metric-label'>Risk Level</div><div class='metric-value'>{metrics.get('risk')}</div></div>", unsafe_allow_html=True)

    st.write("---")
    
    # 2. FINANCIAL CHART
    st.subheader("📈 Projected Growth Trajectory")
    chart_data = pd.DataFrame({
        "Month": [0, 6, 12, 18, 24],
        "Costs ($k)": [180, 210, 240, 260, 280],
        "Revenue ($k)": [0, 50, 150, 320, 580]
    }).set_index("Month")
    st.line_chart(chart_data)

    # 3. FULL REPORT
    with st.spinner("Finalizing Full Report..."):
        report_prompt = f"Generate a detailed Strategic Synthesis for: {st.session_state.user_idea}. Data: {full_context}. Sections: The Story, Requirements, Cost Model, Bull/Bear Scenarios, Accuracy Gaps."
        report_res = client.models.generate_content(model=MODEL_ID, contents=report_prompt)
        st.markdown(report_res.text)

    # 4. EXPORTS
    c1, c2 = st.columns(2)
    with c1: st.download_button("📩 Download Report", report_res.text, file_name="Venture_Report.txt")
    with c2:
        qa_log = "\n".join([f"Q: {q}\nA: {a}\n---" for q, a in zip(st.session_state.questions, st.session_state.answers)])
        st.download_button("📄 Download Annexure (Q&A)", qa_log, file_name="Session_Log.txt")

    if st.button("New Scan"):
        st.session_state.clear()
        st.rerun()