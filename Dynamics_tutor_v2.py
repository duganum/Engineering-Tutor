import streamlit as st
import json
import re
from logic_v2_GitHub import get_gemini_model, load_problems, check_numeric_match, analyze_and_send_report
from render_v2_GitHub import render_problem_diagram

st.set_page_config(page_title="Socratic Engineering Tutor", layout="wide")

# 1. Initialize Session State
if "page" not in st.session_state: st.session_state.page = "landing"
if "chat_sessions" not in st.session_state: st.session_state.chat_sessions = {}
if "grading_data" not in st.session_state: st.session_state.grading_data = {}
if "user_name" not in st.session_state: st.session_state.user_name = None

PROBLEMS = load_problems()

# --- Page 0: Name Entry ---
if st.session_state.user_name is None:
    st.title("🛡️ Engineering Mechanics Portal")
    st.markdown("### Texas A&M University - Corpus Christi")
    with st.form("name_form"):
        name_input = st.text_input("Enter your Full Name to begin")
        if st.form_submit_button("Access Tutor"):
            if name_input.strip():
                st.session_state.user_name = name_input.strip()
                st.rerun()
            else: st.warning("Identification is required for academic reporting.")
    st.stop()

# --- Page 1: Main Menu ---
if st.session_state.page == "landing":
    st.title(f"🚀 Welcome, {st.session_state.user_name}!")
    st.info("Texas A&M University - Corpus Christi | Dr. Dugan Um")
    st.markdown("""
    I am your personal Socratic Tutor. Select a problem below, and let's work through the physics together.
    """)
    
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
        st.image(render_problem_diagram(p_id), width=350)
    
    with cols[1]:
        st.metric("Variables Found", f"{len(solved)} / {len(prob['targets'])}")
        st.progress(len(solved) / len(prob['targets']) if len(prob['targets']) > 0 else 0)
        
        # --- NEW FEEDBACK AND SUBMIT LOGIC ---
        st.markdown("---")
        st.write("### End Session")
        feedback = st.text_area("Optional: How was this session? (Any feedback for Dr. Um?)", placeholder="I struggled with the FBD...")
        
        if st.button("⬅️ Submit Session & Score"):
            history_text = ""
            for msg in st.session_state.chat_sessions[p_id].history:
                role = "Tutor" if msg.role == "model" else "Student"
                history_text += f"{role}: {msg.parts[0].text}\n"
            
            # Combine history with the new feedback
            full_history = f"{history_text}\n--- STUDENT FEEDBACK ---\n{feedback}"
            
            with st.spinner("Analyzing performance..."):
                report = analyze_and_send_report(st.session_state.user_name, prob['category'], full_history)
                st.session_state.last_report = report
                st.session_state.page = "report_view"
                st.rerun()

    # AI Initialization
    if p_id not in st.session_state.chat_sessions:
        sys_prompt = (
            f"You are a warm, supportive Socratic Engineering Tutor. Student: {st.session_state.user_name}. "
            f"PROBLEM: {prob['statement']}. Targets: {list(prob['targets'].keys())}. "
            "INSTRUCTIONS: 1. Be encouraging. 2. Ask ONE guiding question at a time. "
            "3. NEVER provide final numerical answers. 4. Respond in PLAIN TEXT ONLY."
        )
        model = get_gemini_model(sys_prompt)
        if model:
            session = model.start_chat(history=[])
            session.send_message(f"Hey {st.session_state.user_name}! How are you feeling about Dynamics lately? Let's tackle this problem. What's the first step you'd take?")
            st.session_state.chat_sessions[p_id] = session

    # Display Chat History
    if p_id in st.session_state.chat_sessions:
        for message in st.session_state.chat_sessions[p_id].history:
            role = "assistant" if message.role == "model" else "user"
            with st.chat_message(role):
                clean_msg = re.sub(r'\(Internal Status:.*?\)', '', message.parts[0].text).strip()
                clean_msg = clean_msg.replace('{"tutor_message": "', '').replace('"}', '')
                st.markdown(clean_msg)

    # Input Logic
    if user_input := st.chat_input("Type your response here..."):
        new_match = False
        for target, val in prob['targets'].items():
            if target not in solved and check_numeric_match(user_input, val):
                st.session_state.grading_data[p_id]['solved'].add(target)
                new_match = True
        state_info = f"\n(Internal Status: Solved={list(solved)}. NewMatch={new_match})"
        st.session_state.chat_sessions[p_id].send_message(user_input + state_info)
        st.rerun()

# --- Page 3: Report View ---
elif st.session_state.page == "report_view":
    st.title("📊 Performance Summary")
    st.success(f"Great work, {st.session_state.user_name}. Your results and feedback have been shared.")
    st.markdown(st.session_state.get("last_report", "No report available."))
    if st.button("Return to Problem Menu"):
        st.session_state.page = "landing"; st.rerun()
