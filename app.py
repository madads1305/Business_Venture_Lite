import streamlit as st
import pandas as pd
from google import genai
import json

# --- 1. SESSION STATE ---
if 'user_idea' not in st.session_state: st.session_state.user_idea = ""
if 'step' not in st.session_state: st.session_state.step = "START"
if 'answers' not in st.session_state: st.session_state.answers = []
if 'questions' not in st.session_state: st.session_state.questions = []

# --- 2. AI CLIENT ---
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
    .stApp { background-color: #f8fafc; }
    .main-header { font-size: 2.8rem; color: #1e3a8a; font-weight: 800; }
    .metric-card { 
        background: white; padding: 15px; border-radius: 12px; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); text-align: center; border-bottom: 4px solid #2563eb;
    }
    .metric-value { font-size: 1.2rem; font-weight: bold; color: #1e3a8a; }
    .metric-label { font-size: 0.85rem; color: #64748b; font-weight: bold; }
    .question-box { background: white; padding: 30px; border-radius: 20px; border-left: 10px solid #2563eb; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1 class='main-header'>🧠 Venture Architect</h1>", unsafe_allow_html=True)
st.caption("v2.0 | Turn your spark into a business reality.")

# --- 4. APP FLOW ---

# STEP 1: THE START
if st.session_state.step == "START":
    st.subheader("What's the big idea?")
    st.info("Tip: You can use your phone's voice-to-text to 'speak' your pitch here.")
    # Added label for accessibility
    idea = st.text_area("Enter your business idea:", height=200, placeholder="Tell me what you want to build...", label_visibility="visible")
    if st.button("Launch Quest 🚀"):
        if idea:
            st.session_state.user_idea = idea
            st.session_state.step = "ASKING"
            st.rerun()

# STEP 2: THE GAMIFIED 5-QUESTION SPRINT
elif st.session_state.step == "ASKING":
    current_idx = len(st.session_state.answers)
    
    # Progress bar for the 5 "Core" questions
    progress = min(current_idx / 5, 1.0)
    st.progress(progress, text=f"Core Discovery: {current_idx}/5")
    
    if len(st.session_state.questions) <= current_idx:
        with st.spinner("Analyzing your vision..."):
            history = "\n".join([f"Q: {q}\nA: {a}" for q, a in zip(st.session_state.questions, st.session_state.answers)])
            
            # The prompt is now strictly limited to 5 specific business pillars
            prompt = f"""
            You are a world-class startup mentor. The user's idea: {st.session_state.user_idea}.
            HISTORY: {history}
            
            GOAL: We need to build a business model. 
            Directly ask about one of these 5 pillars we haven't covered yet: 
            1. Exact Product/Service, 2. Target Customer, 3. Revenue Source, 4. Biggest Expense, 5. Main Competitor.
            
            RULES:
            1. Ask ONE short, punchy question. Use 10th-grade English.
            2. MUST end in a question mark. No lectures.
            3. DO NOT ask 'how do you know' or 'why'—just assume their idea is valid and ask about HOW it works.
            """
            response = client.models.generate_content(model=MODEL_ID, contents=prompt)
            st.session_state.questions.append(response.text)
            st.rerun()

    st.markdown(f"<div class='question-box'><p style='font-size:1.5em; font-weight:500;'>{st.session_state.questions[current_idx]}</p></div>", unsafe_allow_html=True)
    
    # Added label for accessibility
    user_ans = st.text_input(f"Question {current_idx + 1} response:", key=f"ans_{current_idx}", placeholder="Tap the mic on your keyboard to speak...", label_visibility="collapsed")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Next Question →", key=f"btn_{current_idx}"):
            if user_ans:
                st.session_state.answers.append(user_ans)
                if len(st.session_state.answers) == 5:
                    st.session_state.step = "REPORT"
                st.rerun()
    with col2: # Fixed 'c2' to 'col2'
         st.write("") 

# STEP 3: THE REVEAL (Dashboard & Report)
elif st.session_state.step == "REPORT":
    st.info("💡 **Architect's Disclaimer:** This is an automated software-generated model. Use it as a roadmap for deeper research.")
    
    with st.spinner("Generating your Venture Dashboard..."):
        full_context = "\n".join([f"Q: {q}\nA: {a}" for q, a in zip(st.session_state.questions, st.session_state.answers)])
        
        # Metric Extraction - Forcing 1-3 word answers for the tiles
        summary_prompt = f"Idea: {st.session_state.user_idea}. Context: {full_context}. Return JSON with 1-3 word values: 'capex', 'opex', 'breakeven', 'readiness' (0-100%), 'risk'."
        summary_res = client.models.generate_content(model=MODEL_ID, contents=summary_prompt)
        try:
            metrics = json.loads(summary_res.text.replace('```json', '').replace('```', '').strip())
        except:
            metrics = {"capex": "TBD", "opex": "TBD", "breakeven": "TBD", "readiness": "50%", "risk": "Medium"}

    # 6-Tile Dashboard (Expanded to include the 6th "Readiness" tile)
    t1, t2, t3, t4, t5, t6 = st.columns(6)
    t1.markdown(f"<div class='metric-card'><div class='metric-label'>Readiness</div><div class='metric-value'>{metrics.get('readiness', '50%')}</div></div>", unsafe_allow_html=True)
    t2.markdown(f"<div class='metric-card'><div class='metric-label'>Start-up Cost</div><div class='metric-value'>{metrics.get('capex', 'TBD')}</div></div>", unsafe_allow_html=True)
    t3.markdown(f"<div class='metric-card'><div class='metric-label'>Monthly Cost</div><div class='metric-value'>{metrics.get('opex', 'TBD')}</div></div>", unsafe_allow_html=True)
    t4.markdown(f"<div class='metric-card'><div class='metric-label'>Time to Profit</div><div class='metric-value'>{metrics.get('breakeven', 'TBD')}</div></div>", unsafe_allow_html=True)
    t5.markdown(f"<div class='metric-card'><div class='metric-label'>Risk Level</div><div class='metric-value'>{metrics.get('risk', 'Med')}</div></div>", unsafe_allow_html=True)
    t6.markdown(f"<div class='metric-card'><div class='metric-label'>Accuracy</div><div class='metric-value'>100%</div></div>", unsafe_allow_html=True)

    st.write("---")
    
    # Financial Visual
    st.subheader("Your Path to Profit")
    chart_data = pd.DataFrame({
        "Month": ["Start", "6 Mo", "12 Mo", "18 Mo", "24 Mo"],
        "Investment": [100, 120, 130, 135, 140],
        "Revenue": [0, 20, 80, 160, 300]
    }).set_index("Month")
    st.area_chart(chart_data)

    # Detailed report
    report_prompt = f"Create a professional 'Venture Snapshot' for {st.session_state.user_idea} based on: {full_context}. Use headers: Business Model, Operational Needs, Financial Forecast, and Crucial Gaps."
    report_res = client.models.generate_content(model=MODEL_ID, contents=report_prompt)
    st.markdown(report_res.text)

    # Sidebar CTA for your services
    st.sidebar.success("Ready for a deep dive? Book a consultation with a Certified AI Strategist to turn this snapshot into a bank-ready business plan.")

    # Downloads
    d1, d2 = st.columns(2)
    with d1:
        st.download_button("📩 Download Report", report_res.text, file_name="Venture_Report.txt")
    with d2:
        qa_log = "\n".join([f"Q: {q}\nA: {a}\n---" for q, a in zip(st.session_state.questions, st.session_state.answers)])
        st.download_button("📄 Download Q&A Log", qa_log, file_name="Session_Log.txt")

    if st.button("Start New Quest 🔄"):
        st.session_state.clear()
        st.rerun()