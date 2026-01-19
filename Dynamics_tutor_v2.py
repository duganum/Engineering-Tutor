import streamlit as st
import json
import re
from logic import get_gemini_model, load_problems, check_numeric_match, analyze_and_send_report

st.set_page_config(page_title="Socratic Engineering Tutor", layout="wide")

# Initialize Session State
if "page" not in st.session_state: st.session_state.page = "landing"
if "chat_sessions" not in st.session_state: st.session_state.chat_sessions = {}
if "grading_data" not in st.session_state: st.session_state.grading_data = {}
if "user_name" not in st.session_state: st.session_state.user_name = None

PROBLEMS = load_problems()

# --- Page 0: Name Entry ---
if st.session_state.user_name is None:
    st.title("🛡️ Student Access")
    st.markdown("### Please enter your name to begin.")
    
    with st.form("name_form"):
        name_input = st.text_input("Full Name")
        submit_name = st.form_submit_button("Start Session")
        
        if submit_name:
            if name_input.strip():
                st.session_state.user_name = name_input.strip()
                st.rerun()
            else:
                st.warning("Please enter your name for the academic report.")
    st.stop()

# --- Page 1: Main Menu ---
if st.session_state.page == "landing":
    st.title(f"🚀 Welcome, {st.session_state.user_name}!")
    st.info("Texas A&M University - Corpus Christi | Dr. Dugan Um")
    
    if not PROBLEMS:
        st.error("❌ No problems found in 'problems.json'.")
        st.stop()

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
    
    cols = st.columns([2, 1])
    with cols[0]:
        st.subheader(f"📌 {prob['category']}")
        st.info(prob['statement'])
    with cols[1]:
        total_targets = len(prob['targets'])
        st.metric("Progress", f"{len(solved)} / {total_targets}")
        st.progress(len(solved) / total_targets if total_targets > 0 else 0)
        
        if st.button("⬅️ Finish & Send Report"):
            history_text = ""
            if p_id in st.session_state.chat_sessions:
                for msg in st.session_state.chat_sessions[p_id].history:
                    role = "Tutor" if msg.role == "model" else "Student"
                    history_text += f"{role}: {msg.parts[0].text}\n"
            
            with st.spinner("Calculating score and sending report..."):
                report = analyze_and_send_report(st.session_state.user_name, prob['category'], history_text)
                st.session_state.last_report = report
                st.session_state.page = "report_view"
                st.rerun()

    # Initialize Gemini Chat
    if p_id not in st.session_state.chat_sessions:
        sys_prompt = (
            f"You are a Socratic Engineering Tutor. Student: {st.session_state.user_name}. "
            f"PROBLEM: {prob['statement']}. Numerical Targets: {list(prob['targets'].keys())}. "
            "RULES: 1. Ask ONE guiding question at a time. 2. Never give the final answer. "
            "3. Format JSON: {'tutor_message': '...'}"
        )
        model = get_gemini_model(sys_prompt)
        if model:
            try:
                session = model.start_chat(history=[])
                session.send_message("Introduce problem and ask for the first step.")
                st.session_state.chat_sessions[p_id] = session
            except Exception as e:
                st.error(f"API Error: {e}")

    # Display History
    if p_id in st.session_state.chat_sessions:
        for message in st.session_state.chat_sessions[p_id].history:
            if "Introduce problem" in message.parts[0].text: continue
            with st.chat_message("assistant" if message.role == "model" else "user"):
                text = message.parts[0].text
                display_text = re.sub(r'\(Internal Status:.*?\)', '', text).strip()
                match = re.search(r'"tutor_message":\s*"(.*?)"', display_text, re.DOTALL)
                st.markdown(match.group(1) if match else display_text)

    # Input Handling
    if user_input := st.chat_input("Enter your answer or thought..."):
        new_match = False
        for target, val in prob['targets'].items():
            if target not in solved:
                if check_numeric_match(user_input, val):
                    st.session_state.grading_data[p_id]['solved'].add(target)
                    new_match = True
        
        st.session_state.chat_sessions[p_id].send_message(f"{user_input} (Internal Status: NewMatch={new_match})")
        st.rerun()

# --- Page 3: Report View ---
elif st.session_state.page == "report_view":
    st.title("📊 Performance Report")
    st.success(f"Report for {st.session_state.user_name} has been emailed to Dr. Um.")
    st.markdown("---")
    st.markdown(st.session_state.get("last_report", "No report available."))
    if st.button("Confirm and Return to Menu"):
        st.session_state.page = "landing"
        st.rerun()
