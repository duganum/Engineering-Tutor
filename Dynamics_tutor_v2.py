import streamlit as st
import json
import re
import numpy as np
import matplotlib.pyplot as plt
from logic_v2_GitHub import get_gemini_model, load_problems, check_numeric_match, analyze_and_send_report
from render_v2_GitHub import render_problem_diagram, render_lecture_visual

# 1. Page Configuration & Unified Button UI
st.set_page_config(page_title="Socratic Engineering Tutor", layout="wide")

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

# 2. Initialize Session State
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
    st.title(f"🚀 Welcome, {st.session_state.user_name}!")
    st.info("Texas A&M University - Corpus Christi | Dr. Dugan Um")
    st.markdown("---")

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
            if cat["is_lecture"]:
                if st.button(f"{cat['icon']}: {cat['name']}", key=f"lec_{cat['id_prefix']}", use_container_width=True):
                    st.session_state.lecture_topic = cat['name']
                    st.session_state.page = "lecture"; st.rerun()
            else:
                st.button(f"{cat['icon']}: {cat['name']}", key=f"stat_{cat['id_prefix']}", use_container_width=True, disabled=True)
        
        row_probs = [p for p in PROBLEMS if p['id'].startswith(cat['id_prefix'])]
        problem_cols = [col1, col2, col3]
        for i in range(3):
            with problem_cols[i]:
                if i < len(row_probs):
                    prob = row_probs[i]
                    sub_label = prob.get('category', '').split(":")[-1].strip()
                    if st.button(f"**{sub_label}**\nID: {prob['id']}", key=f"btn_{prob['id']}", use_container_width=True):
                        st.session_state.current_prob = prob
                        st.session_state.page = "chat"; st.rerun()
                else:
                    st.button(" ", key=f"blank_{cat['id_prefix']}_{i}", use_container_width=True, disabled=True)
        st.markdown("---")

# --- Page 3: Interactive Lecture Agent (INTERACTIVE MODE) ---
elif st.session_state.page == "lecture":
    topic = st.session_state.lecture_topic
    st.title(f"🎓 Interactive Lab: {topic}")
    col_sim, col_chat = st.columns([1, 1])
    
    with col_sim:
        params = {}
        if topic == "Projectile Motion":
            params['v0'] = st.slider("v0 (m/s)", 5, 100, 30)
            params['angle'] = st.slider("theta (deg)", 0, 90, 45)
            st.latex(r"v = v_x e_t + v_y e_n")
        elif topic == "Normal & Tangent":
            params['v'] = st.slider("v (Speed)", 1, 50, 20)
            params['rho'] = st.slider("rho (Radius)", 5, 100, 50)
            st.latex(r"a_n = \frac{v^2}{\rho}")
        elif topic == "Polar Coordinates":
            params['r'] = st.slider("r (Radial)", 1, 50, 20)
            params['theta'] = st.slider("theta (Angle)", 0, 360, 45)
        
        st.image(render_lecture_visual(topic, params))
        if st.button("🏠 Exit Menu"):
            st.session_state.lecture_session = None; st.session_state.page = "landing"; st.rerun()

    with col_chat:
        if "lecture_session" not in st.session_state or st.session_state.lecture_session is None:
            # ENFORCED SOCRATIC INTERACTION PROMPT
            sys_msg = (
                f"You are a Physics Professor at TAMUCC teaching {topic}. "
                "STRICT RULES for interactivity: "
                "1. NEVER explain the whole concept at once. "
                "2. Break the derivation into 5-6 small steps. "
                "3. After each step, ASK a specific question and WAIT for the student to answer. "
                "4. Use LaTeX for formulas. "
                "5. Start by asking the student to look at the sliders and describe what they see."
            )
            model = get_gemini_model(sys_msg)
            st.session_state.lecture_session = model.start_chat(history=[])
            st.session_state.lecture_session.send_message(f"Hello {st.session_state.user_name}. Let's derive {topic} step-by-step. To start, look at the simulation and tell me: what happens to the path if you change the speed?")

        for msg in st.session_state.lecture_session.history:
            with st.chat_message("assistant" if msg.role == "model" else "user"):
                st.write(msg.parts[0].text)
        if lecture_input := st.chat_input("Your answer..."):
            st.session_state.lecture_session.send_message(lecture_input); st.rerun()

# (Remaining Page 2 & 4 Chat/Report logic remains the same)
