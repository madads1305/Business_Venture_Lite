import streamlit as st
import pandas as pd
# Use the new explicit import style
from google import genai

# --- 1. SECURE CONFIGURATION ---
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
except Exception:
    st.error("Missing Gemini API Key in Streamlit Secrets.")
    st.stop()

# Initialize the 2026 Client
client = genai.Client(api_key=API_KEY)
MODEL_ID = "gemini-2.5-flash"

# --- 2. THE UI (Initial Zhuzh) ---
st.set_page_config(page_title="Venture Architect", page_icon="🚀", layout="centered")

# Custom CSS to make it look a bit sharper
st.markdown("""
    <style>
    .main { background-color: #fcfcfc; }
    .stButton>button { background-color: #007bff; color: white; border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

if "step" not in st.session_state:
    st.session_state.step = "START"
if "answers" not in st.session_state:
    st.session_state.answers = []
if "questions" not in st.session_state:
    st.session_state.questions = []

st.title("🧠 Venture Architect AI")
st.caption("Strategic Planning Agent v1.0")

# --- 3. LOGIC STEPS ---
if st.session_state.step == "START":
    st.subheader("The Genesis")
    idea = st.text_area("Describe your business idea...", height=150)
    if st.button("Begin Architectural Scan"):
        if idea:
            st.session_state.user_idea = idea
            st.session_state.step = "ASKING"
            st.rerun()

elif st.session_state.step == "ASKING":
    current_q_idx = len(st.session_state.answers)
    st.progress((current_q_idx) / 20)
    
    if len(st.session_state.questions) <= current_q_idx:
        with st.spinner("Agent is analyzing context..."):
            history = "\n".join([f"Q: {q}\nA: {a}" for q, a in zip(st.session_state.questions, st.session_state.answers)])
            prompt = f"Business: {st.session_state.user_idea}\nHistory: {history}\n\nAsk the next critical business plan question."
            response = client.models.generate_content(model=MODEL_ID, contents=prompt)
            st.session_state.questions.append(response.text)

    st.info(f"**Question {current_q_idx + 1}**")
    st.write(st.session_state.questions[current_q_idx])
    
    user_ans = st.text_input("Response:", key=f"input_{current_q_idx}")
    
    if st.button("Next →"):
        if user_ans:
            st.session_state.answers.append(user_ans)
            if len(st.session_state.answers) >= 20:
                st.session_state.step = "REPORT"
            st.rerun()

elif st.session_state.step == "REPORT":
    st.header("📋 Venture Architecture Report")
    
    # Quick Dashboard Visual
    chart_data = pd.DataFrame({
        "Year": ["Y1", "Y2", "Y3", "Y4", "Y5"],
        "Revenue Growth": [10, 35, 85, 160, 280]
    })
    st.line_chart(chart_data, x="Year")

    with st.spinner("Synthesizing Final Executive Summary..."):
        full_data = "\n".join([f"Q: {q}\nA: {a}" for q, a in zip(st.session_state.questions, st.session_state.answers)])
        report_prompt = f"Provide a detailed 2-page business summary and accuracy score for: {st.session_state.user_idea}\nData:\n{full_data}"
        response = client.models.generate_content(model=MODEL_ID, contents=report_prompt)
        st.markdown(response.text)
    
    if st.button("Start New Scan"):
        st.session_state.clear()
        st.rerun()