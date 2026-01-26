import streamlit as st
import json
import re
import numpy as np
import matplotlib.pyplot as plt
from logic_v2_GitHub import get_gemini_model, load_problems, check_numeric_match, analyze_and_send_report
from render_v2_GitHub import render_problem_diagram, render_lecture_visual

st.set_page_config(page_title="Socratic Engineering Tutor", layout="wide")

# 1. Initialize Session State
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
            else: st.warning("Identification is required for academic reporting.")
    st.stop()

# --- Page 1: Main Menu ---
if st.session_state.page == "landing":
    st.title(f"🚀 Welcome, {st.session_state.user_name}!")
    st.info("Texas A&M University - Corpus Christi | Dr. Dugan Um")
    
    st.markdown("---")
    st.subheader("💡 Interactive Learning Agents")
    st.write("Learn the derivation of velocity ($v$) and acceleration ($a$) through real-time simulations.")
    
    col1, col2, col3, _ = st.columns([1, 1, 1, 1])
    
    with col1:
        if st.button("🎓 Lecture: Projectile Motion", use_container_width=True):
            st.session_state.lecture_topic = "Projectile Motion"
            st.session_state.page = "lecture"; st.rerun()
            
    with col2:
        if st.button("🎓 Lecture: Normal & Tangent", use_container_width=True):
            st.session_state.lecture_topic = "Normal & Tangent"
            st.session_state.page = "lecture"; st.rerun()
            
    with col3:
        if st.button("🎓 Lecture: Polar Coordinates", use_container_width=True):
            st.session_state.lecture_topic = "Polar Coordinates"
            st.session_state.page = "lecture"; st.rerun()
            
    st.markdown("---")

    # Practice Problems Section
    st.markdown("### 📝 Practice Problems")
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
                    st.session_state.page = "chat"; st.rerun()

# --- Page 3: Interactive Lecture Agent ---
elif st.session_state.page == "lecture":
    topic = st.session_state.lecture_topic
    st.title(f"🎓 Physics Lab: {topic} Dynamics")
    
    col_sim, col_chat = st.columns([1, 1])
    
    with col_sim:
        st.subheader("🛠️ Parameters & Vector Analysis")
        params = {}
        
        if topic == "Projectile Motion":
            params['v0'] = st.slider("Initial Speed ($v_0$)", 5, 100, 30)
            params['angle'] = st.slider("Launch Angle ($\theta$)", 0, 90, 45)
            st.latex(r"v_x = v_0 \cos \theta, \quad v_y = v_0 \sin \theta - gt")
            
            
        elif topic == "Normal & Tangent":
            params['v'] = st.slider("Constant Speed ($v$)", 1, 50, 20)
            params['rho'] = st.slider("Radius of Curvature ($\rho$)", 5, 100, 50)
            st.latex(r"a_n = \frac{v^2}{\rho}, \quad a_t = \dot{v}")
            st.info("💡 Observe how $a_n$ changes with speed and the radius of curvature.")
            
            
        elif topic == "Polar Coordinates":
            params['r'] = st.slider("Radial Distance ($r$)", 1, 50, 20)
            params['theta'] = st.slider("Angle ($\theta$)", 0, 360, 45)
            st.latex(r"a = (\ddot{r} - r\dot{\theta}^2)e_r + (r\ddot{\theta} + 2\dot{r}\dot{\theta})e_\theta")
            

        st.image(render_lecture_visual(topic, params))
        
        if st.button("🏠 Exit to Main Menu"):
            st.session_state.lecture_session = None
            st.session_state.page = "landing"; st.rerun()

    with col_chat:
        st.subheader("💬 Socratic Tutor: English Lecture")
        if "lecture_session" not in st.session_state or st.session_state.lecture_session is None:
            sys_msg = (
                f"You are a Physics Professor at TAMUCC. Topic: {topic}. "
                "Conduct the entire lecture in English. "
                "Explain the geometric derivation of velocity and acceleration. "
                "Help students understand why $a_n = v^2/rho$ using the simulation values. "
                "Ask one guiding question at a time and be encouraging."
            )
            model = get_gemini_model(sys_msg)
            st.session_state.lecture_session = model.start_chat(history=[])
            # Initial English message
            st.session_state.lecture_session.send_message(
                f"Hello {st.session_state.user_name}! Let's explore the derivation of {topic} equations. "
                "Look at the current simulation. If you double the speed, how do you expect the "
                "normal acceleration to change? Let's find out together."
            )

        for msg in st.session_state.lecture_session.history:
            with st.chat_message("assistant" if msg.role == "model" else "user"):
                st.write(msg.parts[0].text)

        if lecture_input := st.chat_input("Ask a question in English..."):
            st.session_state.lecture_session.send_message(lecture_input); st.rerun()

# --- Page 2 & 4: Problem Solving Chat & Report (기존 유지) ---
# ...
