import streamlit as st
import json
import re
import numpy as np
import matplotlib.pyplot as plt
from logic_v2_GitHub import get_gemini_model, load_problems, check_numeric_match, analyze_and_send_report
from render_v2_GitHub import render_problem_diagram, render_lecture_visual

# 1. Page Configuration
st.set_page_config(page_title="Socratic Engineering Tutor", layout="wide")

# 2. CSS: 버튼 높이 최소화(60px) 및 3열 그리드 최적화
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
    .stMarkdown h4 {
        margin-top: 10px;
        margin-bottom: 5px;
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

# --- Page 1: Main Menu (3-Column Layout) ---
if st.session_state.page == "landing":
    st.title(f"🚀 Welcome, {st.session_state.user_name}!")
    st.info("Texas A&M University - Corpus Christi | Dr. Dugan Um")
    
    # Section A: Interactive Lectures (3 Columns)
    st.markdown("---")
    st.subheader("💡 Interactive Learning Agents")
    
    col_l1, col_l2, col_l3 = st.columns(3)
    with col_l1:
        if st.button("🎓 Lecture: Projectile", key="lec_proj", use_container_width=True):
            st.session_state.lecture_topic = "Projectile Motion"
            st.session_state.page = "lecture"; st.rerun()
    with col_l2:
        if st.button("🎓 Lecture: N-T Accel", key="lec_nt", use_container_width=True):
            st.session_state.lecture_topic = "Normal & Tangent"
            st.session_state.page = "lecture"; st.rerun()
    with col_l3:
        if st.button("🎓 Lecture: Polar", key="lec_polar", use_container_width=True):
            st.session_state.lecture_topic = "Polar Coordinates"
            st.session_state.page = "lecture"; st.rerun()
            
    # Section B: Practice Problems (3-Column Grid)
    st.markdown("---")
    st.subheader("📝 Practice Problems")
    
    categories = {}
    for p in PROBLEMS:
        cat_main = p.get('category', 'General').split(":")[0].strip()
        if cat_main not in categories: categories[cat_main] = []
        categories[cat_main].append(p)

    for cat_name, probs in categories.items():
        st.markdown(f"#### {cat_name}")
        # 각 카테고리 내에서 3개씩 끊어서 한 줄씩 생성
        for i in range(0, len(probs), 3):
            cols = st.columns(3)
            for j in range(3):
                if i + j < len(probs):
                    prob = probs[i + j]
                    sub_label = prob.get('category', '').split(":")[-1].strip()
                    with cols[j]:
                        if st.button(f"**{sub_label}**\n({prob['id']})", key=f"btn_{prob['id']}", use_container_width=True):
                            st.session_state.current_prob = prob
                            st.session_state.page = "chat"; st.rerun()
    st.markdown("---")

# --- (이하 Chat, Lecture, Report 로직 동일 유지) ---
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
                st.session_state.page = "report_view"; st.rerun()
    if p_id not in st.session_state.chat_sessions:
        sys_prompt = f"You are a Socratic Tutor. Lead in English."
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
        st.image(render_lecture_visual(topic, params))
        if st.button("🏠 Exit"):
            st.session_state.lecture_session = None; st.session_state.page = "landing"; st.rerun()
    with col_chat:
        if "lecture_session" not in st.session_state or st.session_state.lecture_session is None:
            sys_msg = f"You are a Professor at TAMUCC. Topic: {topic}. Respond only in English. Socratic interaction."
            model = get_gemini_model(sys_msg)
            st.session_state.lecture_session = model.start_chat(history=[])
            st.session_state.lecture_session.send_message(f"Hello {st.session_state.user_name}. Let's derive {topic} formulas. What happens to the path if you change the speed?")
        for msg in st.session_state.lecture_session.history:
            with st.chat_message("assistant" if msg.role == "model" else "user"): st.write(msg.parts[0].text)
        if lecture_input := st.chat_input("Your answer..."):
            st.session_state.lecture_session.send_message(lecture_input); st.rerun()

elif st.session_state.page == "report_view":
    st.title("📊 Report View")
    st.markdown(st.session_state.get("last_report", ""))
    if st.button("Return"): st.session_state.page = "landing"; st.rerun()
