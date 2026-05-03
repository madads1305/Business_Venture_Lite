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

# --- 2. THE ZHUZH: STYLING & SIDEBAR ---
st.set_page_config(page_title="Venture Architect", page_icon="🚀", layout="wide")

st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(180deg, #f0f2f6 0%, #ffffff 100%);
    }
    .stButton>button {
        width: 100%;
        border-radius: 20px;
        border: none;
        background-color: #007bff;
        color: white;
        font-weight: bold;
        transition: 0.3s;
        height: 3em;
    }
    .stButton>button:hover {
        background-color: #0056b3;
        transform: scale(1.02);
    }
    .question-card {
        background-color: white;
        padding: 25px;
        border-radius: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        border-left: 5px solid #007bff;
    }
    .fast-track-box {
        background-color: #e3f2fd;
        padding: 15px;
        border-radius: 10px;
        border: 1px dashed #007bff;
        margin-top: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

with st.sidebar:
    st.title("👨‍💻 Architect Profile")
    st.markdown(f"**Lead Consultant:** {st.secrets.get('USER_NAME', 'Adi')}")
    st.markdown("---")
    st.write("This tool uses **Gemini 2.5 Flash** to stress-test ideas through 20 strategic questions.")
    st.info("The 'Fast-Track' option becomes available after 7 questions once a baseline model is established.")
    if st.button("Reset Session", key="reset_sidebar"):
        st.session_state.clear()
        st.rerun()

# --- 3. SECURE API CONFIGURATION ---
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    client = genai.Client(api_key=API_KEY)
    MODEL_ID = "gemini-2.5-flash"
except Exception:
    st.error("Missing Gemini API Key in Streamlit Secrets.")
    st.stop()

# --- 4. MAIN INTERFACE ---
st.title("🧠 Venture Architect AI")
st.caption("Strategic Planning Agent v1.2 | High-Level Indicative Modeling")

# STEP: START
if st.session_state.step == "START":
    st.subheader("The Genesis")
    idea = st.text_area("Describe your business idea...", height=150, placeholder="e.g., A subscription-based heater maintenance service for Ottawa transit...")
    if st.button("Begin Architectural Scan"):
        if idea:
            st.session_state.user_idea = idea
            st.session_state.step = "ASKING"
            st.rerun()
        else:
            st.warning("Please provide an initial idea to begin.")

# STEP: ASKING
elif st.session_state.step == "ASKING":
    current_q_idx = len(st.session_state.answers)
    st.progress((current_q_idx) / 20, text=f"Context Maturity: {current_q_idx}/20")
    
    # Generate Question if needed
    if len(st.session_state.questions) <= current_q_idx:
        with st.spinner("Analyzing context..."):
            try:
                # Context pruning for mobile stability
                recent_history = "\n".join([f"Q: {q}\nA: {a}" for q, a in zip(st.session_state.questions[-5:], st.session_state.answers[-5:])])
                
                gamified_prompt = f"""
                You are a 'Venture Architect' host helping a user build a business plan.
                Idea: {st.session_state.user_idea}
                Recent History: {recent_history}
                
                RULES:
                1. Ask Question {current_q_idx + 1} of 20.
                2. ONE simple sentence. NO technical jargon.
                3. Focus on branding, market vibe, or the 'Human' element.
                4. DO NOT explain why you are asking.
                """
                
                response = client.models.generate_content(model=MODEL_ID, contents=gamified_prompt)
                st.session_state.questions.append(response.text if response.text else "Who is your very first customer?")
            except Exception:
                st.error("Connection hiccup. Please try again.")
                if st.button("Retry"): st.rerun()
                st.stop()

    # Display Question
    st.markdown(f"""
        <div class='question-card'>
            <small style='color: #007bff; font-weight: bold;'>STRATEGIC INQUIRY {current_q_idx + 1}</small>
            <p style='font-size: 1.2em; margin-top: 10px;'>{st.session_state.questions[current_q_idx]}</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.write("") 
    user_ans = st.text_input("Your Response:", key=f"input_{current_q_idx}", placeholder="Type your answer...")

    # Action Buttons
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
            else:
                st.warning("Please provide a response.")

    # FAST-TRACK LOGIC
    if current_q_idx >= 7:
        with st.container():
            st.markdown("<div class='fast-track-box'>", unsafe_allow_html=True)
            st.write("💡 **Architect's Insight:** I have enough core data to generate an indicative report now.")
            if st.button("🚀 Fast-Track: Generate Strategic Synthesis"):
                st.session_state.step = "REPORT"
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

# STEP: REPORT
elif st.session_state.step == "REPORT":
    st.header("📋 Venture Architecture Report")
    
    # Calculate a mock maturity score based on how many questions were answered
    q_count = len(st.session_state.answers)
    maturity_percentage = int((q_count / 20) * 100)
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Data Maturity", f"{maturity_percentage}%")
    m2.metric("Market Viability", "Indicative High")
    m3.metric("Est. Launch Complexity", "Medium")
    
    chart_data = pd.DataFrame({
        "Year": ["Y1", "Y2", "Y3", "Y4", "Y5"],
        "Revenue Projection (%)": [10, 35, 85, 170, 300]
    })
    st.line_chart(chart_data, x="Year")

    with st.spinner("Synthesizing Executive Summary..."):
        full_context = "\n".join([f"Q: {q}\nA: {a}" for q, a in zip(st.session_state.questions, st.session_state.answers)])
        report_prompt = f"""
        Act as a Senior Venture Capitalist. 
        Generate a Business Plan Lite for: {st.session_state.user_idea}.
        Inputs Provided: {full_context}
        
        REQUIRED SECTIONS:
        1. Executive Summary
        2. Operational Roadmap
        3. Financial Cost Model (Table format)
        4. ACCURACY SCORE (0-100%): Be honest—if they only answered {q_count} questions, the score should reflect that.
        5. ARCHITECT VERDICT: (Go / No-Go / Pivot)
        """
        response = client.models.generate_content(model=MODEL_ID, contents=report_prompt)
        st.markdown(response.text)
        st.download_button("📩 Download Professional Report", response.text, file_name="Venture_Report.txt")

    if st.button("Start New Architectural Scan"):
        st.session_state.clear()
        st.rerun()