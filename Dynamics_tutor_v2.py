import streamlit as st
import json
import re
from logic import get_gemini_model, load_problems, check_numeric_match, analyze_and_send_report

st.set_page_config(page_title="Socratic Engineering Tutor", layout="wide")

# 1. Initialize Session State
if "page" not in st.session_state: st.session_state.page = "landing"
if "chat_sessions" not in st.session_state: st.session_state.chat_sessions = {}
if "grading_data" not in st.session_state: st.session_state.grading_data = {}
if "user_name" not in st.session_state: st.session_state.user_name = None

# Load Problems from local JSON
PROBLEMS = load_problems()

# --- Page 0: Name Entry (Required for Report) ---
if st.session_state.user_name is None:
    st.title("🛡️ Engineering Mechanics Portal")
    st.markdown("### Please identify yourself to begin the tutoring session.")
    
    with st.form("name_form"):
        name_input = st.text_input("Enter your Full Name")
        submit_name = st.form_submit_button("Access Tutor")
        
        if submit_name:
            if name_input.strip():
                st.session_state.user_name = name_input.strip()
                st.rerun()
            else:
                st.warning("You must enter a name for academic tracking and reporting.")
    st.stop()

# --- Page 1: Main Menu (Problem Selection) ---
if st.session_state.page == "landing":
    st.title(f"🚀 Welcome, {st.session_state.user_name}")
    st.info("Texas A&M University - Corpus Christi | Dr. Dugan Um")
    st.markdown("""
    Select a dynamics problem from the list below. 
    The Socratic Tutor will guide you through the solution. 
    Once finished, an **Achievement Score (0-10)** will be generated and sent to Dr. Um.
    """)
    
    if not PROBLEMS:
        st.error("❌ 'problems.json' not found or empty.")
        st.stop()

    # Categorize and Display Problems
    categories = {}
    for p in PROBLEMS:
        cat_main = p.get('category', 'General').split(":")[0].strip()
        if cat_main not in categories: categories[cat_main] = []
        categories[cat_main].append(p)

    for cat_name, probs in categories.items():
        st.header(cat_name)
        cols = st.columns(3)
        for idx, prob in enumerate(probs):
            with cols[idx % 3]:
                sub_label = prob.get('category', '').split(":")[-1].strip()
                if st.button(f"**{sub_label}**\n\nID: {prob['id']}", key=f"btn_{prob['id']}", use_container_width=True):
                    st.session_state.current_prob = prob
                    st.session_state.page = "chat"
                    st.rerun()

# --- Page 2: Socratic Chat Interface ---
elif st.session_state.page == "chat":
    prob = st.session_state.current_prob
    p_id = prob['id']

    if p_id not in st.session_state.grading_data:
        st.session_state.grading_data[p_id] = {'solved': set()}
    
    solved = st.session_state.grading_data[p_id]['solved']
    
    # Header & Progress
    cols = st.columns([2, 1])
    with cols[0]:
        st.subheader(f"📌 {prob['category']}")
        st.info(prob['statement'])
    with cols[1]:
        total_targets = len(prob['targets'])
        st.metric("Variables Found", f"{len(solved)} / {total_targets}")
        st.progress(len(solved) / total_targets if total_targets > 0 else 0)
        
        if st.button("⬅️ Submit Session & Score"):
            history_text = ""
            if p_id in st.session_state.chat_sessions:
                for msg in st.session_state.chat_sessions[p_id].history:
                    role = "Tutor" if msg.role == "model" else "Student"
                    history_text += f"{role}: {msg.parts[0].text}\n"
            
            with st.spinner("Calculating Achievement Score..."):
                report = analyze_and_send_report(st.session_state.user_name, prob['category'], history_text)
                st.session_state.last_report = report
                st.session_state.page = "report_view"
                st.rerun()

    # Initialize Gemini 2.0 Chat
    if p_id not in st.session_state.chat_sessions:
        sys_prompt = (
            f"You are a Socratic Engineering Tutor. Student Name: {st.session_state.user_name}. "
            f"PROBLEM: {prob['statement']}. Numerical Targets: {list(prob['targets'].keys())}. "
            "INSTRUCTIONS: 1. Ask ONE guiding question at a time. "
            "2. Help the student develop Free Body Diagrams (FBD) and equations. "
            "3. Never provide the final numerical answer yourself. "
            "4. Format response in JSON: {'tutor_message': '...'}"
        )
        model = get_gemini_model(sys_prompt)
        if model:
            try:
                session = model.start_chat(history=[])
                session.send_message("Briefly introduce the problem and ask for the first conceptual step.")
                st.session_state.chat_sessions[p_id] = session
            except Exception as e:
                st.error(f"Chat Initialization Error: {e}")

    # Display Chat History
    if p_id in st.session_state.chat_sessions:
        for message in st.session_state.chat_sessions[p_id].history:
            # Skip the initial system-trigger message
            if "Introduce the problem" in message.parts[0].text: continue
            
            role = "assistant" if message.role == "model" else "user"
            with st.chat_message(role):
                raw_text = message.parts[0].text
                # Remove internal metadata tags from student view
                display_text = re.sub(r'\(Internal Status:.*?\)', '', raw_text).strip()
                # Extract text from JSON format
                match = re.search(r'"tutor_message":\s*"(.*?)"', display_text, re.DOTALL)
                st.markdown(match.group(1) if match else display_text)

    # Input Logic
    if user_input := st.chat_input("Type your response or numerical answer here..."):
        new_match = False
        # Check if student provided a correct target value
        for target, val in prob['targets'].items():
            if target not in solved:
                if check_numeric_match(user_input, val):
                    st.session_state.grading_data[p_id]['solved'].add(target)
                    new_match = True
        
        # Inject hidden status to guide the AI tutor
        state_info = f"\n(Internal Status: CurrentSolved={list(st.session_state.grading_data[p_id]['solved'])}. NewMatchFound={new_match})"
        st.session_state.chat_sessions[p_id].send_message(user_input + state_info)
        st.rerun()

# --- Page 3: Report & Score View ---
elif st.session_state.page == "report_view":
    st.title("📊 Achievement & Analysis")
    st.success(f"Report for {st.session_state.user_name} has been emailed to Dr. Dugan Um. If you have any questions regarding this AI tutor, please contact him at dugan.um@gmail.com")
    st.markdown("---")
    st.markdown(st.session_state.get("last_report", "No report available."))
    
    if st.button("Confirm and Return to Problem Menu"):
        # Reset current session data if they want to try another problem
        st.session_state.page = "landing"
        st.rerun()

