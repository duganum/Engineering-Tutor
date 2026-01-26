import streamlit as st
import json
import re
import numpy as np
import matplotlib.pyplot as plt
from logic_v2_GitHub import get_gemini_model, load_problems, check_numeric_match, analyze_and_send_report
from render_v2_GitHub import render_problem_diagram, render_lecture_visual

# 1. Page Configuration
st.set_page_config(page_title="Socratic Engineering Tutor", layout="wide")

# 2. CSS to Unify Button Heights and Widths
st.markdown("""
    <style>
    div.stButton > button {
        height: 100px;
        white-space: normal;
        word-wrap: break-word;
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

# --- Page 1: Main Menu (Fixed Statics and Enabled Lectures) ---
if st.session_state.page == "landing":
    st.title(f"🚀 Welcome, {st.session_state.user_name}!")
    st.info("Texas A&M University - Corpus Christi | Dr. Dugan Um")
    st.markdown("---")

    # Full category list including Statics (S) and Kinematics (K)
    all_categories = [
        {"name": "Equilibrium of Particles", "id_prefix": "S_1.1", "is_lecture": False, "icon": "🏛️ Statics"},
        {"name": "Truss Analysis", "id_prefix": "S_1.2", "is_lecture": False, "icon": "🏛️ Statics"},
        {"name": "Centroids & Geometry", "id_prefix": "S_1.3", "is_lecture": False, "icon": "🏛️ Statics"},
        {"name": "Moments & Beams", "id_prefix": "S_1.4", "is_lecture": False, "icon": "🏛️ Statics"},
        {"name": "Projectile Motion", "id_prefix": "K_2.2", "is_lecture": True, "icon": "🎓 Lecture"},
        {"name": "Normal & Tangent", "id_prefix": "K_2.3", "is_lecture": True, "icon": "🎓 Lecture"},
        {"name": "Polar Coordinates", "id_prefix": "K_2.4", "is_lecture": True, "icon": "🎓 Lecture"}
    ]

    for cat in all_categories:
        col_lec, col1, col2, col3 = st.columns([1, 1, 1, 1])
        
        with col_lec:
            # Enable buttons for Kinematics lectures; Show labels for Statics
            if cat["is_lecture"]:
                if st.button(f"{cat['icon']}: {cat['name']}", key=f"lec_{cat['id_prefix']}", use_container_width=True):
                    st.session_state.lecture_topic = cat['name']
                    st.session_state.page = "lecture"
                    st.rerun()
            else:
                # Statics labels are disabled as they don't have interactive lecture agents yet
                st.button(f"{cat['icon']}: {cat['name']}", key=f"stat_{cat['id_prefix']}", use_container_width=True, disabled=True)
        
        # Grid filtering for associated problems
        row_probs = [p for p in PROBLEMS if p['id'].startswith(cat['id_prefix'])]
        problem_cols = [col1, col2, col3]
        
        for i in range(3):
            with problem_cols[i]:
                if i < len(row_probs):
                    prob = row_probs[i]
                    sub_label = prob.get('category', '').split(":")[-1].strip()
                    if st.button(f"**{sub_label}**\nID: {prob['id']}", key=f"btn_{prob['id']}", use_container_width=True):
                        st.session_state.current_prob = prob
                        st.session_state.page = "chat"
                        st.rerun()
                else:
                    # Maintain height symmetry
                    st.button(" ", key=f"blank_{cat['id_prefix']}_{i}", use_container_width=True, disabled=True)
        st.markdown("---")

# --- Page 2: Socratic Chat ---
elif st.session_state.page == "chat":
    prob = st.session_state.current_prob
    p_id = prob['id']
    if p_id not in st.session_state.grading_data: st.session_state.grading_data[p_id] = {'solved': set()}
    solved = st.session_state.grading_data[p_id]['solved']
    
    cols = st.columns([2, 1])
    with cols[0]:
        st.subheader(f"📌 {prob['category']}")
        st.info(prob['statement'])
        st.image(render_problem_diagram(p_id), width=350)
    
    with cols[1]:
        st.metric("Variables Found", f"{len(solved)} / {len(prob['targets'])}")
        st.progress(len(solved) / len(prob['targets']) if len(prob['targets']) > 0 else 0)
        st.write("### End Session")
        feedback = st.text_area("Feedback:", placeholder="What was difficult?")
        
        if st.button("⬅️ Submit Session"):
            history_text = ""
            if p_id in st.session_state.chat_sessions:
                for msg in st.session_state.chat_sessions[p_id].history:
                    role = "Tutor" if msg.role == "model" else "Student"
                    history_text += f"{role}: {msg.parts[0].text}\n"
            with st.spinner("Analyzing..."):
                report = analyze_and_send_report(st.session_state.user_name, prob['category'], history_text + feedback)
                st.session_state.last_report = report
                st.session_state.page = "report_view"
                st.rerun()

    if p_id not in st.session_state.chat_sessions:
        sys_prompt = f"You are a Socratic Tutor. Topic: {prob['category']}. Lead in English."
        model = get_gemini_model(sys_prompt)
        st.session_state.chat_sessions[p_id] = model.start_chat(history=[])
        st.session_state.chat_sessions[p_id].send_message("Let's look at the diagram. Where should we start?")

    for message in st.session_state.chat_sessions[p_id].history:
        with st.chat_message("assistant" if message.role == "model" else "user"):
            st.markdown(re.sub(r'\(Internal Status:.*?\)', '', message.parts[0].text).strip())

    if user_input := st.chat_input("Response..."):
        for target, val in prob['targets'].items():
            if target not in solved and check_numeric_match(user_input, val):
                st.session_state.grading_data[p_id]['solved'].add(target)
        st.session_state.chat_sessions[p_id].send_message(user_input); st.rerun()

# --- Page 3: Interactive Lecture Agent ---
elif st.session_state.page == "lecture":
    topic = st.session_state.lecture_topic
    st.title(f"🎓 Lab: {topic}")
    col_sim, col_chat = st.columns([1, 1])
    
    with col_sim:
        params = {}
        if topic == "Projectile Motion":
            params['v0'] = st.slider("v0", 5, 100, 30)
            params['angle'] = st.slider("theta", 0, 90, 45)
            st.latex(r"v_x = v_0 \cos \theta, \quad v_y = v_0 \sin \theta - gt")
        elif topic == "Normal & Tangent":
            params['v'] = st.slider("v", 1, 50, 20)
            params['rho'] = st.slider("rho", 5, 100, 50)
            st.latex(r"a_n = \frac{v^2}{\rho}")
        elif topic == "Polar Coordinates":
            params['r'] = st.slider("r", 1, 50, 20)
            params['theta'] = st.slider("theta", 0, 360, 45)
            st.latex(r"v = \dot{r} e_r + r \dot{\theta} e_\theta")

        st.image(render_lecture_visual(topic, params))
        if st.button("🏠 Exit to Menu"):
            st.session_state.lecture_session = None; st.session_state.page = "landing"; st.rerun()

    with col_chat:
        if "lecture_session" not in st.session_state or st.session_state.lecture_session is None:
            sys_msg = (
                f"You are a Professor at TAMUCC. Topic: {topic}. English only. "
                "Use the Dot Product Proof (T·T = 1 implies T·dT/dt = 0) for Normal Acceleration."
            )
            model = get_gemini_model(sys_msg)
            st.session_state.lecture_session = model.start_chat(history=[])
            st.session_state.lecture_session.send_message(f"Hello {st.session_state.user_name}! Let's explore the derivation of {topic} formulas.")

        for msg in st.session_state.lecture_session.history:
            with st.chat_message("assistant" if msg.role == "model" else "user"):
                st.write(msg.parts[0].text)
        if lecture_input := st.chat_input("Question..."):
            st.session_state.lecture_session.send_message(lecture_input); st.rerun()

# --- Page 4: Report View ---
elif st.session_state.page == "report_view":
    st.title("📊 Performance Summary")
    st.markdown(st.session_state.get("last_report", "No report available."))
    if st.button("Return to Menu"):
        st.session_state.page = "landing"; st.rerun()
