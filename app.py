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
st.caption("Strategic Planning Agent v1.9 | Business Intelligence Engine")

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
    st.progress(current_idx / 20, text=f"Progress: {current_idx}/20")
    
    if len(st.session_state.questions) <= current_idx:
        with st.spinner("Prioritizing core business drivers..."):
            try:
                history = "\n".join([f"Q: {q}\nA: {a}" for q, a in zip(st.session_state.questions, st.session_state.answers)])
                
                # NEW PHASED LOGIC: First 7 questions cover the "Big 3"
                phase_instruction = ""
                if current_idx < 7:
                    phase_instruction = "PHASE: CORE DISCOVERY. Focus ONLY on: Target Customer, Primary Revenue Stream, and Big Ticket Costs. Do not ask 'Why' or for validation."
                else:
                    phase_instruction = "PHASE: FINE-TUNING. Focus on: Operational scale, Risks, Marketing, or Team requirements."

                prompt = f"""
                You are a Strategic Business Architect. Idea: {st.session_state.user_idea}.
                {phase_instruction}
                HISTORY: {history}
                
                RULES:
                1. Ask ONE simple, short question to build a financial model.
                2. MUST end in a question mark (?). 
                3. Use plain English (10th-grade level). 
                4. DO NOT ask 'How do you know' or 'Why'. Assume the user's premise is true.
                5. Do NOT repeat topics.
                """
                response = client.models.generate_content(model=MODEL_ID, contents=prompt)
                st.session_state.questions.append(response.text if response.text else "What is your main way to make money?")
                st.rerun()
            except Exception:
                st.error("Connection flickered. Please click Retry.")
                if st.button("Retry"): st.rerun()
                st.stop()

    # UI Display
    st.markdown(f"""
        <div class='question-box'>
            <small style='color:#2563eb; font-weight:bold;'>STRATEGIC INQUIRY {current_idx + 1}</small>
            <p style='font-size:1.4em; margin-top:10px;'>{st.session_state.questions[current_idx]}</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.write("") 
    user_ans = st.text_input("Your Answer:", key=f"ans_{current_idx}", placeholder="Keep it simple and direct...")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Next Question →", key=f"btn_{current_idx}"):
            if user_ans:
                st.session_state.answers.append(user_ans)
                if len(st.session_state.answers) >= 20: st.session_state.step = "REPORT"
                st.rerun()
            else:
                st.warning("Please type a response to continue the scan.")
    
    with c2:
        if current_idx >= 7:
            if st.button("🚀 Fast-Track: Generate Initial Model"):
                st.session_state.step = "REPORT"
                st.rerun()

# STEP: REPORT
elif st.session_state.step == "REPORT":
    st.warning("⚠️ **DISCLAIMER:** This indicative model is based solely on user inputs. [cite: 124]")
    
    with st.spinner("Calculating Indicative Metrics..."):
        full_context = "\n".join([f"Q: {q}\nA: {a}" for q, a in zip(st.session_state.questions, st.session_state.answers)])
        
        # Dashboard Data Logic
        summary_prompt = f"Analyze: {st.session_state.user_idea}. Data: {full_context}. Output JSON: 'capex', 'opex', 'breakeven', 'viability', 'risk'."
        summary_res = client.models.generate_content(model=MODEL_ID, contents=summary_prompt)
        json_str = summary_res.text.replace('```json', '').replace('```', '').strip()
        try:
            metrics = json.loads(json_str)
        except:
            metrics = {"capex": "N/A", "opex": "N/A", "breakeven": "N/A", "viability": "N/A", "risk": "N/A"}

    # EXECUTIVE DASHBOARD [cite: 125, 178]
    t1, t2, t3, t4, t5, t6 = st.columns(6)
    with t1: st.markdown(f"<div class='metric-card'><div class='metric-label'>Accuracy</div><div class='metric-value'>{int((len(st.session_state.answers)/20)*100)}%</div></div>", unsafe_allow_html=True)
    with t2: st.markdown(f"<div class='metric-card'><div class='metric-label'>Est. CAPEX</div><div class='metric-value'>{metrics.get('capex')}</div></div>", unsafe_allow_html=True)
    with t3: st.markdown(f"<div class='metric-card'><div class='metric-label'>Est. OPEX</div><div class='metric-value'>{metrics.get('opex')}</div></div>", unsafe_allow_html=True)
    with t4: st.markdown(f"<div class='metric-card'><div class='metric-label'>Breakeven</div><div class='metric-value'>{metrics.get('breakeven')}</div></div>", unsafe_allow_html=True)
    with t5: st.markdown(f"<div class='metric-card'><div class='metric-label'>Viability</div><div class='metric-value'>{metrics.get('viability')}</div></div>", unsafe_allow_html=True)
    with t6: st.markdown(f"<div class='metric-card'><div class='metric-label'>Risk Level</div><div class='metric-value'>{metrics.get('risk')}</div></div>", unsafe_allow_html=True)

    st.write("---")
    
    # 2. THE BUSINESS STORY & MODEL [cite: 81, 91]
    with st.spinner("Synthesizing Final Report..."):
        report_prompt = f"""
        Generate a 'Business Plan Lite' for {st.session_state.user_idea}.
        Use the following inputs: {full_context}
        
        STRUCTURE:
        1. THE VISION: A summary of the business story. 
        2. OPERATIONAL REQUIREMENTS: What is needed to launch? [cite: 91]
        3. FINANCIAL MODEL: CAPEX/OPEX breakdown. [cite: 124, 175]
        4. BULL vs BEAR: Best/Worst case scenarios. [cite: 221]
        5. ACCURACY GAPS: What is missing for a 100% accurate plan? 
        """
        response = client.models.generate_content(model=MODEL_ID, contents=report_prompt)
        st.markdown(response.text)
        st.download_button("📩 Download Professional Report", response.text, file_name="Venture_Report.txt")

    if st.button("Start New Architectural Scan"):
        st.session_state.clear()
        st.rerun()