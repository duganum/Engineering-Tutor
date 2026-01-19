import streamlit as st
import json
import re
from logic import get_gemini_model, load_problems, check_numeric_match

st.set_page_config(page_title="Socratic Physics Agency", layout="wide")

# 1. 세션 상태 초기화 (새로고침 시 데이터 보존)
if "page" not in st.session_state: st.session_state.page = "landing"
if "chat_sessions" not in st.session_state: st.session_state.chat_sessions = {}
if "grading_data" not in st.session_state: st.session_state.grading_data = {}

PROBLEMS = load_problems()

# --- Page 1: 문제 선택 화면 ---
if st.session_state.page == "landing":
    st.title("🚀 Dynamics Socratic Agency")
    st.write("Welcome. Select a problem to begin your session.")
    
    for prob in PROBLEMS:
        if st.button(f"Analyze Problem {prob['id']}: {prob['category']}"):
            st.session_state.current_prob = prob
            st.session_state.page = "chat"
            st.rerun()

# --- Page 2: 소크라테스식 대화 화면 ---
elif st.session_state.page == "chat":
    prob = st.session_state.current_prob
    p_id = prob['id']

    # 데이터 구조 안전하게 생성
    if p_id not in st.session_state.grading_data:
        st.session_state.grading_data[p_id] = {'solved': set()}
    
    solved = list(st.session_state.grading_data[p_id]['solved'])
    
    # 1. 시스템 프롬프트 (튜터의 성격 정의)
    sys_prompt = (
        f"You are a Socratic Physics Tutor. PROBLEM: {prob['statement']}. "
        f"Student goals: {list(prob['targets'].keys())}. Found so far: {solved}. "
        "RULES: 1. Be encouraging. 2. If student gives a formula, ask for the numbers. "
        "3. NEVER provide final numbers. 4. Respond ONLY in JSON: {'tutor_message': '...'}"
    )

    # 2. 채팅 세션 초기화 (최초 1회만 실행)
    if p_id not in st.session_state.chat_sessions:
        model = get_gemini_model(sys_prompt)
        if model:
            session = model.start_chat(history=[])
            try:
                # 튜터가 먼저 인사하게 유도
                session.send_message("Introduce the problem and ask for the first step.")
                st.session_state.chat_sessions[p_id] = session
            except Exception as e:
                st.error(f"Connection failed: {e}")
        else:
            st.error("API Error: Could not initialize model.")

    # UI 구성 (문제 지문 및 진행도)
    cols = st.columns([2, 1])
    with cols[0]:
        st.subheader(f"Problem: {prob['category']}")
        st.info(prob['statement'])
    with cols[1]:
        st.metric("Targets Found", f"{len(solved)} / {len(prob['targets'])}")
        if st.button("⬅️ Back to Menu"):
            st.session_state.page = "landing"
            st.rerun()

    # 3. 채팅 히스토리 표시 (리런 시에도 대화 내용 유지)
    if p_id in st.session_state.chat_sessions:
        for message in st.session_state.chat_sessions[p_id].history:
            if "Introduce the problem" in message.parts[0].text:
                continue
                
            role = "assistant" if message.role == "model" else "user"
            with st.chat_message(role):
                text = message.parts[0].text
                # 내부 상태 태그 제거 및 JSON 파싱
                display_text = re.sub(r'\(Internal Status:.*?\)', '', text).strip()
                match = re.search(r'"tutor_message":\s*"(.*?)"', display_text, re.DOTALL)
                st.markdown(match.group(1) if match else display_text)

    # 4. 사용자 입력 처리 및 AI 응답 생성
    if user_input := st.chat_input("Enter your response..."):
        with st.chat_message("user"):
            st.markdown(user_input)
        
        # 정답 체크 (숫자가 포함되어 있는지 확인)
        for target, val in prob['targets'].items():
            if check_numeric_match(user_input, val):
                st.session_state.grading_data[p_id]['solved'].add(target)

        # AI에게 현재 진행 상태와 함께 메시지 전송
        with st.chat_message("assistant"):
            try:
                current_solved = list(st.session_state.grading_data[p_id]['solved'])
                state_info = f"\n(Internal Status: Solved={current_solved})"
                
                # 메시지 전송 및 응답 받기
                response = st.session_state.chat_sessions[p_id].send_message(user_input + state_info)
                
                # 결과 출력 후 화면 강제 새로고침 (상태 동기화)
                st.rerun()
            except Exception:
                st.error("Lost connection to Gemini. Please try again.")
