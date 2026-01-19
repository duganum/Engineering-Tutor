import streamlit as st
import json
import re
from logic import get_gemini_model, load_problems, check_numeric_match

st.set_page_config(page_title="Socratic Engineering Tutor", layout="wide")

# 1. 세션 상태 초기화
if "page" not in st.session_state: st.session_state.page = "landing"
if "chat_sessions" not in st.session_state: st.session_state.chat_sessions = {}
if "grading_data" not in st.session_state: st.session_state.grading_data = {}

PROBLEMS = load_problems()

# --- Page 1: 문제 선택 화면 (카테고리별 그룹화) ---
if st.session_state.page == "landing":
    st.title("🚀 Engineering Mechanics Socratic Tutor")
    st.write("학습할 주제를 선택하세요. 각 섹션에는 개념 이해를 돕는 문제들이 준비되어 있습니다.")
    
    # 카테고리별로 문제 분류
    categories = {}
    for p in PROBLEMS:
        cat_main = p['category'].split(":")[0]  # "Statics" 또는 "Kinematics" 추출
        if cat_main not in categories:
            categories[cat_main] = []
        categories[cat_main].append(p)

    # 카테고리별로 레이아웃 배치
    for cat_name, probs in categories.items():
        st.header(cat_name)
        # 3열로 문제 버튼 배치
        cols = st.columns(3)
        for idx, prob in enumerate(probs):
            with cols[idx % 3]:
                # 버튼에 소제목 표시 (예: 1.1 Free Body Diagram)
                sub_cat = prob['category'].split(":")[1] if ":" in prob['category'] else ""
                if st.button(f"{sub_cat}\n\nProblem {prob['id']}", key=prob['id'], use_container_width=True):
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
    
    # 1. 시스템 프롬프트 (수정된 targets 대응)
    sys_prompt = (
        f"You are a Socratic Engineering Tutor. PROBLEM: {prob['statement']}. "
        f"Target values to find: {list(prob['targets'].keys())}. "
        f"So far, the student found: {solved}. "
        "RULES: 1. Ask one guiding question at a time. 2. Focus on the concept first. "
        "3. If a student gives a correct numeric answer, acknowledge it and move to the next step. "
        "4. Respond ONLY in JSON: {'tutor_message': '...'}"
    )

    # 2. 채팅 세션 초기화
    if p_id not in st.session_state.chat_sessions:
        model = get_gemini_model(sys_prompt)
        if model:
            session = model.start_chat(history=[])
            try:
                session.send_message("Introduce the problem briefly and ask the first conceptual question.")
                st.session_state.chat_sessions[p_id] = session
            except Exception as e:
                st.error(f"Connection failed: {e}")

    # UI 헤더
    cols = st.columns([2, 1])
    with cols[0]:
        st.subheader(f"📌 {prob['category']}")
        st.info(prob['statement'])
    with cols[1]:
        progress = len(solved) / len(prob['targets'])
        st.metric("Progress", f"{len(solved)} / {len(prob['targets'])}")
        st.progress(progress)
        if st.button("⬅️ Back to Menu"):
            st.session_state.page = "landing"
            st.rerun()

    # 3. 채팅 히스토리 표시
    if p_id in st.session_state.chat_sessions:
        for message in st.session_state.chat_sessions[p_id].history:
            if "Introduce the problem" in message.parts[0].text: continue
            role = "assistant" if message.role == "model" else "user"
            with st.chat_message(role):
                text = message.parts[0].text
                display_text = re.sub(r'\(Internal Status:.*?\)', '', text).strip()
                match = re.search(r'"tutor_message":\s*"(.*?)"', display_text, re.DOTALL)
                st.markdown(match.group(1) if match else display_text)

    # 4. 사용자 입력 및 정답 체크
    if user_input := st.chat_input("답변을 입력하세요 (예: 39.24)..."):
        with st.chat_message("user"):
            st.markdown(user_input)
        
        # 정답 체크 로직
        new_solved = False
        for target, val in prob['targets'].items():
            if target not in st.session_state.grading_data[p_id]['solved']:
                if check_numeric_match(user_input, val):
                    st.session_state.grading_data[p_id]['solved'].add(target)
                    new_solved = True

        with st.chat_message("assistant"):
            try:
                current_solved = list(st.session_state.grading_data[p_id]['solved'])
                state_info = f"\n(Internal Status: Solved={current_solved}. New match={new_solved})"
                st.session_state.chat_sessions[p_id].send_message(user_input + state_info)
                st.rerun()
            except Exception:
                st.error("Gemini와 연결이 끊겼습니다.")
