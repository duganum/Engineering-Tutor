import streamlit as st
import json
import re
import numpy as np
import matplotlib.pyplot as plt
from logic_v2_GitHub import get_gemini_model, load_problems, check_numeric_match, analyze_and_send_report
from render_v2_GitHub import render_problem_diagram, render_lecture_visual

# 1. Page Configuration
st.set_page_config(page_title="Socratic Engineering Tutor", layout="wide")

# 2. CSS: Minimal Button Height (60px) and UI consistency
st.markdown("""
    <style>
    div.stButton > button {
        height: 60px;
        padding: 5px 10px;
        font-size: 14px;
        white-space: normal;
        word-wrap: break-word;
        line-height: 1.2;
        display: flex;
        align-items: center;
        justify-content: center;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# 3. Initialize Session State
if "page" not in st.session_state: st.session_state.page = "landing"
if "chat_sessions" not in st.session_state: st.session_state.chat_sessions = {}
if "grading_data" not in st.session_state: st.session_state.grading_data = {}
if "user_name" not in st.session_state: st.session_state.user_name = None
if "lecture_topic" not in st.session_state: st.session_state.lecture_topic = None

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
            else:
                st.warning("Identification is required for academic reporting.")
    st.stop()

# --- Page 1: Main Menu ---
if st.session_state.page == "landing":
    st.title("🚀 Engineering Dynamics")  # Heading moved to the top
    st.subheader(f"Welcome, {st.session_state.user_name}!") # Welcome moved below
    st.info("Texas A&M University - Corpus Christi | Dr. Dugan Um")
    
    # Section A: Interactive Lectures (Now with Relative Motion)
    st.markdown("---")
    st.subheader("💡 Interactive Learning Agents")
    col_l1, col_l2, col_l3, col_l4 = st.columns(4)
    lectures = [
        ("Projectile Motion", "K_2.2"), 
        ("Normal & Tangent", "K_2.3"), 
        ("Polar Coordinates", "K_2.4"),
        ("Relative Motion", "K_2.5")
    ]
    for i, (name, pref) in enumerate(lectures):
        with [col_l1, col_l2, col_l3, col_l4][i]:
            if st.button(f"🎓 Lecture: {name}", key=f"lec_{pref}", use_container_width=True):
                st.session_state.lecture_topic = name
                st.session_state.page = "lecture"
                st.rerun()

    # Section B: Practice Problems
    st.markdown("---")
    st.subheader("📝 Engineering Review Problems")
    categories = {}
    for p in PROBLEMS:
        cat_main = p.get('category', 'General').split(":")[0].strip()
        
        # Mapping Kinematics to Particle Kinematics for display
        if cat_main == "Kinematics":
            cat_main = "Particle Kinematics"
            
        if cat_main not in categories: categories[cat_main] = []
        categories[cat_main].append(p)

    for cat_name, probs in categories.items():
        st.markdown(f"#### {cat_name}")
        for i in range(0, len(probs), 3):
            cols = st.columns(3)
            for j in range(3):
                if i + j < len(probs):
                    prob = probs[i + j]
                    sub_label = prob.get('category', '').split(":")[-1].strip()
                    with cols[j]:
                        if st.button(f"**{sub_label}**\n({prob['id']})", key=f"btn_{prob['id']}", use_container_width=True):
                            st.session_state.current_prob = prob
                            st.session_state.page = "chat"
                            st.rerun()
    st.markdown("---")

# --- Page 2: Socratic Chat (Practice Problems) ---
elif st.session_state.page == "chat":
    prob = st.session_state.current_prob
    p_id = prob['id']
    if p_id not in st.session_state.grading_data: st.session_state.grading_data[p_id] = {'solved': set()}
    solved = st.session_state.grading_data[p_id]['solved']
    
    cols = st.columns([2, 1])
    with cols[0]:
        st.subheader(f"📌 {prob['category']}")
        st.info(prob['statement'])
        st.image(render_problem_diagram(p_id), width=400)
    
    with cols[1]:
        st.metric("Variables Found", f"{len(solved)} / {len(prob['targets'])}")
        st.progress(len(solved) / len(prob['targets']) if len(prob['targets']) > 0 else 0)
        feedback = st.text_area("Notes for Dr. Um:", placeholder="What was the hardest part?")
        if st.button("⬅️ Submit Session", use_container_width=True):
            history_text = ""
            if p_id in st.session_state.chat_sessions:
                for msg in st.session_state.chat_sessions[p_id].history:
                    role = "Tutor" if msg.role == "model" else "Student"
                    history_text += f"{role}: {msg.parts[0].text}\n"
            report = analyze_and_send_report(st.session_state.user_name, prob['category'], history_text + feedback)
            st.session_state.last_report = report
            st.session_state.page = "report_view"; st.rerun()

    if p_id not in st.session_state.chat_sessions:
        sys_prompt = (
            f"You are the Engineering Tutor for {st.session_state.user_name} at TAMUCC. "
            f"Context: {prob['statement']}. Use LaTeX for all math. "
            "STRICT RULES: 1. Do NOT answer your own questions. 2. NEVER ask 'what diagram' questions. "
            "3. Respond ONLY after the student types something. 4. Use English only."
        )
        model = get_gemini_model(sys_prompt)
        st.session_state.chat_sessions[p_id] = model.start_chat(history=[])

    for message in st.session_state.chat_sessions[p_id].history:
        with st.chat_message("assistant" if message.role == "model" else "user"):
            st.markdown(message.parts[0].text)

    if not st.session_state.chat_sessions[p_id].history:
        st.write("👋 **Tutor Ready.** Please describe the first step of your analysis to begin.")

    if user_input := st.chat_input("Your analysis..."):
        for target, val in prob['targets'].items():
            if target not in solved and check_numeric_match(user_input, val):
                st.session_state.grading_data[p_id]['solved'].add(target)
        st.session_state.chat_sessions[p_id].send_message(user_input); st.rerun()

# --- Page 3: Interactive Lecture ---
elif st.session_state.page == "lecture":
    topic = st.session_state.lecture_topic
    st.title(f"🎓 Lab: {topic}")
    col_sim, col_chat = st.columns([1, 1])
    
    with col_sim:
        params = {}
        if topic == "Projectile Motion":
            params['v0'] = st.slider("v0", 5, 100, 30); params['angle'] = st.slider("theta", 0, 90, 45)
        elif topic == "Normal & Tangent":
            params['v'] = st.slider("v", 1, 50, 20); params['rho'] = st.slider("rho", 5, 100, 50)
            st.latex(r"a_n = \frac{v^2}{\rho}")
        elif topic == "Polar Coordinates":
            params['r'] = st.slider("r", 1, 50, 20); params['theta'] = st.slider("theta", 0, 360, 45)
        elif topic == "Relative Motion":
            v_ax = st.slider("vA_x", -20, 20, 15)
            v_ay = st.slider("vA_y", -20, 20, 5)
            v_bx = st.slider("vB_x", -20, 20, 10)
            v_by = st.slider("vB_y", -20, 20, -5)
            params['vA'] = [v_ax, v_ay]
            params['vB'] = [v_bx, v_by]
            st.latex(r"\vec{v}_A = \vec{v}_B + \vec{v}_{A/B}")
        
        st.image(render_lecture_visual(topic, params))
        
        st.markdown("---")
        st.subheader("📊 Session Completion")
        lecture_feedback = st.text_area("Final Summary:", placeholder="Summarize the governing equations.")
        
        if st.button("🚀 Submit Lecture Report (Score 0-10)", use_container_width=True):
            history_text = ""
            if "lecture_session" in st.session_state and st.session_state.lecture_session:
                for msg in st.session_state.lecture_session.history:
                    role = "Professor" if msg.role == "model" else "Student"
                    history_text += f"{role}: {msg.parts[0].text}\n"
            
            with st.spinner("Analyzing mastery..."):
                report = analyze_and_send_report(st.session_state.user_name, f"LECTURE: {topic}", history_text + f"\n--- STUDENT FEEDBACK ---\n{lecture_feedback}")
                st.session_state.last_report = report
                st.session_state.page = "report_view"; st.rerun()

        if st.button("🏠 Exit", use_container_width=True):
            st.session_state.lecture_session = None; st.session_state.page = "landing"; st.rerun()

    with col_chat:
        st.subheader("💬 Socratic Discussion")
        if "lecture_session" not in st.session_state or st.session_state.lecture_session is None:
            sys_msg = (
                f"You are a Professor at TAMUCC teaching {topic}. Respond only in English and use LaTeX. "
                "Guide the student through the vector derivations or equations using the Socratic method. "
                "Do not give answers immediately. Ask one targeted question at a time."
            )
            model = get_gemini_model(sys_msg)
            st.session_state.lecture_session = model.start_chat(history=[])
            st.session_state.lecture_session.send_message(f"Hello {st.session_state.user_name}. Looking at the {topic} simulation, how would you define the relationship between the vectors shown?")
        
        for msg in st.session_state.lecture_session.history:
            with st.chat_message("assistant" if msg.role == "model" else "user"):
                st.markdown(msg.parts[0].text)
        
        if lecture_input := st.chat_input("Discuss the physics..."):
            st.session_state.lecture_session.send_message(lecture_input); st.rerun()

# --- Page 4: Report View ---
elif st.session_state.page == "report_view":
    st.title("📊 Performance Summary")
    st.markdown(st.session_state.get("last_report", "No report available."))
    if st.button("Return to Main Menu"):
        st.session_state.page = "landing"; st.rerun()
