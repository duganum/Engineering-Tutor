import streamlit as st
import json
import re
from logic import get_gemini_model, load_problems, check_numeric_match

st.set_page_config(page_title="Socratic Physics Agency", layout="wide")

# 1. 세션 상태 초기화
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

    # grading_data 초기화 확인
    if p_id not in st.session_state.grading_data:
        st.session_state.grading_data[p_id] = {'solved': set()}
    
    current_grading = st.session_state.grading_data[p_id]
    solved = list(current_grading['solved'])
    
    # 1. 시스템 프롬프트 설정
    sys_prompt = (
        f"You are a Socratic Physics Tutor. PROBLEM: {prob['statement']}. "
        f"Student goals: {list(prob['targets'].keys())}. Found so far: {solved}. "
        "RULES: 1. Be encouraging. 2. If student gives a formula, ask for the numbers. "
        "3. NEVER provide final numbers. 4. Respond ONLY in JSON: {'tutor_message': '...'}"
    )

    # 2. 채팅 세션 초기화
    if p_id not in st.session_state.chat_sessions:
        model = get_gemini_model(sys_prompt)
        if model:
            session = model.start_chat(history=[])
            # 첫 번째 환영 메시지 유도
            try:
                session.send_message("Introduce the problem and ask for the first step.")
                st.session_state.chat_sessions[p_id] = session
            except Exception as e:
                st.error(f"Failed to start conversation: {e}")
        else:
            st.error("API Error: Could not initialize model. Check your Secrets.")

    # UI 헤더 구성
    cols = st.columns([2, 1])
    with cols[0]:
        st.subheader(f"Problem: {prob['category']}")
        st.info(prob['statement'])
    with cols[1]:
        st.metric("Targets Found", f"{len(solved)} / {len(prob['targets'])}")
        if st.button("⬅️ Back to Menu"):
            st.session_state.page = "landing"
            st.rerun()

    # 3. 채팅 히스토리 표시 (리런 시 사라지지 않도록 보장)
    if p_id in st.session_state.chat_sessions:
        # history를 순회하며 메시지 렌더링
        for message in st.session_state.chat_sessions[p_id].history:
            # 첫 유도 메시지 제외
            if "Introduce the problem" in message.parts[0].text:
                continue
                
            role = "assistant" if message.role == "model" else "user"
            with st.chat_message(role):
                text = message.parts[0].text
                # 내부 상태 텍스트 제거
                display_text = re.sub(r'\(Internal Status:.*?\)', '', text).strip()
                # JSON 응답에서 메시지만 추출
                match = re.search(r'"tutor_message":\s*"(.*?)"', display_text, re.DOTALL)
                if match:
                    st.markdown(match.group(1))
                else:
                    st.markdown(display_text)

    # 4. 사용자 입력 처리
    if user_input := st.chat_input("Enter your response..."):
        # 즉시 사용자 메시지 표시
        with st.chat_message("user"):
            st.markdown(user_input)
        
        # 정답 체크
        for target, val in prob['targets'].items():
            if check_numeric_match(user_input, val):
                st.session_state.grading_data[p_id]['solved'].add(target)

        # AI 응답 생성
        with st.chat_message("assistant"):
            solved_list = list(st.session_state.grading_data[p_id]['solved'])
            state_info = f"\n(Internal Status: Solved={solved_list})"
            try:
                # 메시지 전송 (이 호출이 세션 내 history를 업데이트함)
                response = st.session_state.chat_sessions[p_id].send_message(user_input + state_info)
                
                # 메시지 파싱 및 출력
                json_match = re.search(r'"tutor_message":\s*"(.*?)"', response.text, re.DOTALL)
                msg = json_match.group(1) if json_match else response.text
                st.markdown(msg)
                
                # 화면 강제 동기화
                st.rerun()
                
            except Exception as e:
                st.error("Lost connection to Gemini. Please try again.")
