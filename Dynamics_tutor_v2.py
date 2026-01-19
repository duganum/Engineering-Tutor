import streamlit as st
import json
import re
from logic import get_gemini_model, load_problems, check_numeric_match, analyze_and_send_report

st.set_page_config(page_title="Socratic Engineering Tutor", layout="wide")

# 1. Initialize Session State
if "page" not in st.session_state: st.session_state.page = "landing"
if "chat_sessions" not in st.session_state: st.session_state.chat_sessions = {}
if "grading_data" not in st.session_state: st.session_state.grading_data = {}
if "user_info" not in st.session_state: st.session_state.user_info = None

PROBLEMS = load_problems()

# --- Page 0: Student Registration ---
if st.session_state.user_info is None:
    st.title("🛡️ Student Registration")
    st.markdown("### Welcome to the Engineering Mechanics Tutor")
    st.info("Texas A&M University - Corpus Christi | Dr. Dugan Um")
    
    with st.form("registration_form"):
        u_name = st.text_input("Full Name")
        u_email = st.text_input("Email Address")
        submit = st.form_submit_button("Start Tutoring")
        if submit:
            if u_name and u_email:
                st.session_state.user_info = {"name": u_name, "email": u_email}
                st.rerun()
            else:
                st.warning("Please enter both your name and email address.")
    st.stop()

# --- Page 1: Main Menu ---
if st.session_state.page == "landing":
    st.title("🚀 Engineering Mechanics Socratic Tutor")
    st.markdown(f"### Welcome, **{st.session_state.user_info['name']}**!")
    
    if not PROBLEMS:
        st.error("❌ No problems found. Please ensure 'problems.json' is present.")
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
        
        if st.button("⬅️ Exit & Send Report"):
            history_text = ""
            if p_id in st.session_state.chat_sessions:
                for msg in st.session_state.chat_sessions[p_id].history:
                    role = "Tutor" if msg.role == "model" else "Student"
                    history_text += f"{role}: {msg.parts[0].text}\n"
            
            with st.spinner("Finalizing report..."):
                report = analyze_and_send_report(
                    st.session_state.user_info['name'],
                    st.session_state.user_info['email'],
                    prob['category'],
                    history_text
                )
                st.session_state.last_report = report
                st.session_state.page = "report_view"
                st.rerun()

    # Chat Session Logic
    if p_id not in st.session_state.chat_sessions:
        sys_prompt = (
            f"You are a Socratic Engineering Tutor. PROBLEM: {prob['statement']}. "
            f"Targets to find: {list(prob['targets'].keys())}. Rules: 1. Ask ONE guiding question. "
            "2. Do not give direct answers. 3. Format response as JSON: {'tutor_message': '...'}"
        )
        model = get_gemini_model(sys_prompt)
        if model:
            session = model.start_chat(history=[])
            session.send_message("Briefly introduce the problem and ask the first step.")
            st.session_state.chat_sessions[p_id] = session

    # Display History
    chat_container = st.container()
    with chat_container:
        if p_id in st.session_state.chat_sessions:
            for message in st.session_state.chat_sessions[p_id].history:
                if "Introduce the problem" in message.parts[0].text: continue
                with st.chat_message("assistant" if message.role == "model" else "user"):
                    raw_text = message.parts[0].text
                    # Clean internal status tags
                    clean_text = re.sub(r'\(Internal Status:.*?\)', '', raw_text).strip()
                    # Try to extract tutor_message from JSON
                    match = re.search(r'"tutor_message":\s*"(.*?)"', clean_text, re.DOTALL)
                    st.markdown(match.group(1) if match else clean_text)

    # Input
    if user_input := st.chat_input("Your response..."):
        new_match = False
        for target, val in prob['targets'].items():
            if target not in solved:
                if check_numeric_match(user_input, val):
                    st.session_state.grading_data[p_id]['solved'].add(target)
                    new_match = True
        
        state_info = f"\n(Internal Status: Solved={list(solved)}. NewMatch={new_match})"
        st.session_state.chat_sessions[p_id].send_message(user_input + state_info)
        st.rerun()

# --- Page 3: Report View ---
elif st.session_state.page == "report_view":
    st.title("📊 Academic Report")
    st.success("Report successfully sent to Dr. Dugan Um.")
    st.markdown("---")
    st.markdown(st.session_state.get("last_report", "No report content found."))
    if st.button("Return to Menu"):
        st.session_state.page = "landing"
        st.rerun()
