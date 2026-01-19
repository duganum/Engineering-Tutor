import streamlit as st
import json
import re
from logic import get_gemini_model, load_problems, check_numeric_match, analyze_and_send_report

st.set_page_config(page_title="Socratic Engineering Tutor", layout="wide")

# 1. 세션 상태 초기화
if "page" not in st.session_state: st.session_state.page = "landing"
if "chat_sessions" not in st.session_state: st.session_state.chat_sessions = {}
if "grading_data" not in st.session_state: st.session_state.grading_data = {}
if "user_info" not in st.session_state: st.session_state.user_info = None

# 데이터 로드
PROBLEMS = load_problems()

# --- Page 0: 사용자 정보 입력 (최초 1회) ---
if st.session_state.user_info is None:
    st.title("🔐 Student Registration")
    st.markdown("### Welcome! Please register to start the tutor.")
    with st.form("registration_form"):
        u_name = st.text_input("Full Name")
        u_email = st.text_input("Email Address")
        submit = st.form_submit_button("Start Learning")
        if submit:
            if u_name and u_email:
                st.session_state.user_info = {"name": u_name, "email": u_email}
                st.rerun()
            else:
                st.warning("Please enter both your name and email.")
    st.stop()

# --- Page 1: 문제 선택 화면 ---
if st.session_state.page == "landing":
    st.title("🚀 Engineering Mechanics Socratic Tutor")
    
    # Dugan Um 교수님 정보 및 안내
    st.markdown(f"""
    ### Welcome, **{st.session_state.user_info['name']}**!
    This is a **free engineering tutor** developed by **Dr. Dugan Um** at **Texas A&M University - Corpus Christi**.
    
    학습할 주제를 선택하세요. 각 섹션에는 개념 이해를 돕는 문제들이 준비되어 있습니다.
    
    ---
    *📢 **Notice:** Your learning progress and session analysis (Bloom's Taxonomy) will be automatically transmitted to **dugan.um@gmail.com** for educational assessment when you return to the menu.*
    """, unsafe_allow_html=True)
    
    if not PROBLEMS:
        st.error("❌ 문제를 불러올 수 없습니다. 'problems.json' 파일 형식을 확인하세요.")
        st.stop()

    # 카테고리별 분류 및 버튼 생성
    categories = {}
    for p in PROBLEMS:
        full_cat = p.get('category', 'General: Unknown')
        cat_main = full_cat.split(":")[0].strip() if ":" in full_cat else full_cat
        if cat_main not in categories: categories[cat_main] = []
        categories[cat_main].append(p)

    for cat_name, probs in categories.items():
        st.header(cat_name)
        cols = st.columns(3)
        for idx, prob in enumerate(probs):
            with cols[idx % 3]:
                full_cat = prob.get('category', '')
                sub_cat = full_cat.split(":")[1].strip() if ":" in full_cat else "Problem"
                if st.button(f"**{sub_cat}**\n\nID: {prob['id']}", key=f"btn_{prob['id']}", use_container_width=True):
                    st.session_state.current_prob = prob
                    st.session_state.page = "chat"
                    st.rerun()

# --- Page 2: 소크라테스식 대화 화면 ---
elif st.session_state.page == "chat":
    prob = st.session_state.current_prob
    p_id = prob['id']

    if p_id not in st.session_state.grading_data:
        st.session_state.grading_data[p_id] = {'solved': set()}
    
    solved = list(st.session_state.grading_data[p_id]['solved'])
    
    # UI 헤더
    cols = st.columns([2, 1])
    with cols[0]:
        st.subheader(f"📌 {prob['category']}")
        st.info(prob['statement'])
    with cols[1]:
        total_targets = len(prob['targets'])
        current_done = len(solved)
        st.metric("Progress", f"{current_done} / {total_targets}")
        st.progress(current_done / total_targets if total_targets > 0 else 0)
        
        # [수정] Back to Menu 클릭 시 리포트 생성 및 전송
        if st.button("⬅️ Back to Menu & Send Report"):
            history_text = ""
            if p_id in st.session_state.chat_sessions:
                for msg in st.session_state.chat_sessions[p_id].history:
                    role = "Tutor" if msg.role == "model" else "Student"
                    history_text += f"{role}: {msg.parts[0].text}\n"
            
            with st.spinner("AI가 학업 성취도를 분석하여 보고서를 전송 중입니다..."):
                report = analyze_and_send_report(
                    st.session_state.user_info['name'],
                    st.session_state.user_info['email'],
                    prob['category'],
                    history_text
                )
                st.session_state.last_report = report
                st.session_state.page = "report_view"
                st.rerun()

    # 채팅 세션 및 메시지 처리 (기존 로직과 동일)
    # ... (생략: 기존의 채팅 히스토리 표시 및 chat_input 처리 코드를 그대로 유지하세요)
    # -------------------------------------------------------------------------
    # (참고: 이전 답변의 '3. 채팅 히스토리 표시'와 '4. 사용자 입력 처리' 부분을 여기에 넣으시면 됩니다.)
    # -------------------------------------------------------------------------

# --- Page 3: 리포트 출력 화면 ---
elif st.session_state.page == "report_view":
    st.title("📊 Academic Achievement Report")
    st.success("The report has been successfully sent to Dr. Dugan Um.")
    st.markdown("---")
    st.markdown(st.session_state.get("last_report", "No report available."))
    st.markdown("---")
    if st.button("Confirm and Return to Menu"):
        st.session_state.page = "landing"
        st.rerun()
