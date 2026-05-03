import streamlit as st
import pandas as pd
from google import genai

# --- 1. SESSION STATE PERSISTENCE ---
# Standardize initialization at the very top
if 'user_idea' not in st.session_state: st.session_state.user_idea = ""
if 'step' not in st.session_state: st.session_state.step = "START"
if 'answers' not in st.session_state: st.session_state.answers = []
if 'questions' not in st.session_state: st.session_state.questions = []

# --- 2. THE AI CALLER (Replaces the "Hiccupy" Singleton) ---
def call_gemini(prompt):
    """Securely initializes and calls the AI in one go to prevent connection drops."""
    try:
        # Fetching fresh from secrets for every call ensures no 'connection closed' errors
        api_key = st.secrets["GEMINI_API_KEY"]
        temp_client = genai.Client(api_key=api_key)
        response = temp_client.models.generate_content(
            model="gemini-2.5-flash", 
            contents=prompt
        )
        return response.text if response.text else "What is your primary goal?"
    except Exception as e:
        # This will show you a bit more detail if it fails again
        return f"ERROR_STILL: {str(e)}"

# --- 3. UI & SIDEBAR ---
st.set_page_config(page_title="Venture Architect", page_icon="🚀", layout="wide")

st.markdown("""
    <style>
    .stApp { background: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 20px; background-color: #007bff; color: white; height: 3em; font-weight: bold; }
    .question-card { background: white; padding: 25px; border-radius: 15px; border-left: 5px solid #007bff; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .fast-track { background: #e3f2fd; padding: 15px; border-radius: 10px; border: 1px dashed #007bff; }
    </style>
    """, unsafe_allow_html=True)

with st.sidebar:
    st.title("👨‍💻 Architect")
    st.write(f"**Lead:** {st.secrets.get('USER_NAME', 'Adi')}")
    st.write("---")
    if st.button("Reset Session"):
        st.session_state.clear()
        st.rerun()

st.title("🧠 Venture Architect AI")
st.caption("Strategic Planning Agent v1.2 | Powered by Gemini 2.5 Flash")

# --- 4. APP FLOW ---

# STEP: START
if st.session_state.step == "START":
    st.subheader("The Genesis")
    idea = st.text_area("Describe your business idea...", height=150)
    if st.button("Begin Architectural Scan"):
        if idea:
            st.session_state.user_idea = idea
            st.session_state.step = "ASKING"
            st.rerun()

# STEP: ASKING
elif st.session_state.step == "ASKING":
    current_idx = len(st.session_state.answers)
    st.progress(current_idx / 20, text=f"Progress: {current_idx}/20")

    # Generate Question if needed
    if len(st.session_state.questions) <= current_idx:
        with st.spinner("Analyzing context..."):
            history = "\n".join([f"Q: {q}\nA: {a}" for q, a in zip(st.session_state.questions[-5:], st.session_state.answers[-5:])])
            prompt = f"Help a user with: {st.session_state.user_idea}. Context: {history}. Ask Question {current_idx+1} (simple, 1 sentence, no jargon)."
            
            result = call_gemini(prompt)
            
            if "ERROR_STILL" in result:
                st.error("Connection drop. We might need to check your Streamlit Secret naming.")
                st.code(result) # Shows the real error hidden in the hiccup
                if st.button("Retry"): st.rerun()
                st.stop()
            else:
                st.session_state.questions.append(result)

    # Display UI
    st.markdown(f"<div class='question-card'><p style='font-size:1.2em;'>{st.session_state.questions[current_idx]}</p></div>", unsafe_allow_html=True)
    st.write("")
    user_ans = st.text_input("Your Response:", key=f"ans_{current_idx}")

    # Logic Buttons
    if st.button("Submit Response →", key=f"btn_{current_idx}"):
        if user_ans:
            st.session_state.answers.append(user_ans)
            if len(st.session_state.answers) >= 20: st.session_state.step = "REPORT"
            st.rerun()

    # Fast-Track (After 7)
    if current_idx >= 7:
        st.markdown("<div class='fast-track'>💡 Baseline reached. Synthesis available.</div>", unsafe_allow_html=True)
        if st.button("🚀 Fast-Track: Generate Synthesis"):
            st.session_state.step = "REPORT"
            st.rerun()

# STEP: REPORT
elif st.session_state.step == "REPORT":
    st.header("📋 Venture Architecture Report")
    
    with st.spinner("Synthesizing..."):
        history = "\n".join([f"Q: {q}\nA: {a}" for q, a in zip(st.session_state.questions, st.session_state.answers)])
        report_prompt = f"Generate a 2-page VC Report for: {st.session_state.user_idea}. Data: {history}."
        
        final_report = call_gemini(report_prompt)
        st.markdown(final_report)
        st.download_button("📩 Save Report", final_report, file_name="report.txt")

    if st.button("New Scan"):
        st.session_state.clear()
        st.rerun()