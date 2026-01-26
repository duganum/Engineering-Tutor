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
    st.write("실시간 시뮬레이션을 통해 속도($v$)와 가속도($a$)의 유도 과정을 학습하세요.")
    
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

# --- Page 2: Problem Solving Chat ---
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
        st.markdown("---")
        st.write("### End Session")
        feedback = st.text_area("Optional Feedback:", placeholder="What was difficult?")
        
        if st.button("⬅️ Submit Session"):
            history_text = ""
            if p_id in st.session_state.chat_sessions:
                for msg in st.session_state.chat_sessions[p_id].history:
                    role = "Tutor" if msg.role == "model" else "Student"
                    history_text += f"{role}: {msg.parts[0].text}\n"
            
            with st.spinner("Analyzing..."):
                report = analyze_and_send_report(st.session_state.user_name, prob['category'], history_text + feedback)
                st.session_state.last_report = report
                st.session_state.page = "report_view"; st.rerun()

    # AI Logic (Problem Solving)
    if p_id not in st.session_state.chat_sessions:
        sys_prompt = f"You are a Socratic Tutor for {st.session_state.user_name}. Problem: {prob['statement']}. Guide them."
        model = get_gemini_model(sys_prompt)
        if model:
            session = model.start_chat(history=[])
            session.send_message("Let's tackle this. What is the first coordinate or component we should consider?")
            st.session_state.chat_sessions[p_id] = session

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
    st.title(f"🎓 Physics Lab: {topic} Dynamics")
    
    col_sim, col_chat = st.columns([1, 1])
    
    with col_sim:
        st.subheader("🛠️ Parameters & Vector Analysis")
        params = {}
        
        if topic == "Projectile Motion":
            params['v0'] = st.slider("Initial Speed ($v_0$)", 5, 100, 30)
            params['angle'] = st.slider("Launch Angle ($\theta$)", 0, 90, 45)
            st.latex(r"v_x = v_0 \cos \theta, \quad v_y = v_0 \sin \theta - gt")
            st.latex(r"x = v_x t, \quad y = v_y t - \frac{1}{2}gt^2")
            
            
        elif topic == "Normal & Tangent":
            params['v'] = st.slider("Constant Speed ($v$)", 1, 50, 20)
            params['rho'] = st.slider("Radius of Curvature ($\rho$)", 5, 100, 50)
            st.latex(r"a_n = \frac{v^2}{\rho}, \quad a_t = \dot{v}")
            st.info("💡 속도가 일정해도 방향이 변하면 법선 가속도($a_n$)가 발생함을 확인하세요.")
            
            
        elif topic == "Polar Coordinates":
            params['r'] = st.slider("Radial Distance ($r$)", 1, 50, 20)
            params['theta'] = st.slider("Angle ($\theta$)", 0, 360, 45)
            st.latex(r"v = \dot{r} e_r + r \dot{\theta} e_\theta")
            st.latex(r"a = (\ddot{r} - r\dot{\theta}^2)e_r + (r\ddot{\theta} + 2\dot{r}\dot{\theta})e_\theta")
            

        st.image(render_lecture_visual(topic, params))
        
        if st.button("🏠 Exit to Main Menu"):
            st.session_state.lecture_session = None
            st.session_state.page = "landing"; st.rerun()

    with col_chat:
        st.subheader("💬 Socratic Tutor: Derivation")
        if "lecture_session" not in st.session_state or st.session_state.lecture_session is None:
            sys_msg = (
                f"You are a Physics Professor at TAMUCC. Topic: {topic}. "
                "Explain the derivation of velocity and acceleration. "
                "Focus on the geometry and how components change with the sliders. "
                "Ask one guiding question at a time to help students catch the logic."
            )
            model = get_gemini_model(sys_msg)
            st.session_state.lecture_session = model.start_chat(history=[])
            # SyntaxError를 해결하기 위해 문자열을 한 줄로 구성했습니다.
            st.session_state.lecture_session.send_message(f"안녕하세요 {st.session_state.user_name} 학생! 시뮬레이션을 보며 {topic}의 가속도 수식이 왜 그렇게 나오는지 함께 유도해 봅시다. 슬라이더를 조작해 보세요. 속도를 높이면 법선 가속도의 크기는 어떻게 변하나요?")

        for msg in st.session_state.lecture_session.history:
            with st.chat_message("assistant" if msg.role == "model" else "user"):
                st.write(msg.parts[0].text)

        if lecture_input := st.chat_input("수식 유도에 대해 질문하세요..."):
            st.session_state.lecture_session.send_message(lecture_input); st.rerun()

# --- Page 4: Report View ---
elif st.session_state.page == "report_view":
    st.title("📊 Performance Summary")
    st.markdown(st.session_state.get("last_report", "No report available."))
    if st.button("Return to Problem Menu"):
        st.session_state.page = "landing"; st.rerun()
