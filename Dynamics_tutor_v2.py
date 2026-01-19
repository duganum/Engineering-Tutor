import streamlit as st
import json
import re
from logic import get_gemini_model, load_problems, check_numeric_match

st.set_page_config(page_title="Socratic Engineering Tutor", layout="wide")

# 1. 세션 상태 초기화
if "page" not in st.session_state: st.session_state.page = "landing"
if "chat_sessions" not in st.session_state: st.session_state.chat_sessions = {}
if "grading_data" not in st.session_state: st.session_state.grading_data = {}

# 데이터 로드
PROBLEMS = load_problems()

# --- Page 1: 문제 선택 화면 ---
if st.session_state.page == "landing":
    st.title("🚀 Engineering Mechanics Socratic Tutor")
    st.write("학습할 주제를 선택하세요. 각 섹션에는 개념 이해를 돕는 문제들이 준비되어 있습니다.")
    
    # [디버깅] 데이터가 없을 경우 경고 표시
    if not PROBLEMS:
        st.error("❌ 문제를 불러올 수 없습니다. 'problems.json' 파일이 GitHub에 있는지, 혹은 JSON 형식이 맞는지 확인하세요.")
        st.stop()

    # 카테고리별로 문제 분류 (예외 처리 강화)
    categories = {}
    for p in PROBLEMS:
        full_cat = p.get('category', 'General: Unknown')
        if ":" in full_cat:
            cat_main = full_cat.split(":")[0].strip()
        else:
            cat_main = full_cat  # 콜론이 없는 경우 전체를 대분류로 사용

        if cat_main not in categories:
            categories[cat_main] = []
        categories[cat_main].append(p)

    # 카테고리별 레이아웃 렌더링
    for cat_name, probs in categories.items():
        st.header(cat_name)
        cols = st.columns(3)
        for idx, prob in enumerate(probs):
            with cols[idx % 3]:
                # 소제목 추출 안전하게 처리
                full_cat = prob.get('category', '')
                sub_cat = full_cat.split(":")[1].strip() if ":" in full_cat else "Problem"
                
                # 버튼 생성
                btn_label = f"**{sub_cat}**\n\nID: {prob['id']}"
                if st.button(btn_label, key=f"btn_{prob['id']}", use_container_width=True):
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
    
    # 1. 시스템 프롬프트
    sys_prompt = (
        f"You are a Socratic Engineering Tutor. PROBLEM: {prob['statement']}. "
        f"Target values: {list(prob['targets'].keys())}. "
        f"Found so far: {solved}. "
        "RULES: 1. Ask ONE guiding question at a time. 2. Focus on the concept/FBD first. "
        "3. NEVER provide the final answer first. 4. Respond ONLY in JSON: {'tutor_message': '...'}"
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
                st.error(f"AI 연결 실패: {e}")
        else:
            st.error("모델 초기화에 실패했습니다.")

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

    # 4. 사용자 입력 처리
    if user_input := st.chat_input("의견이나 정답을 입력하세요..."):
        with st.chat_message("user"):
            st.markdown(user_input)
        
        # 정답 체크
        new_match = False
        for target, val in prob['targets'].items():
            if target not in st.session_state.grading_data[p_id]['solved']:
                if check_numeric_match(user_input, val):
                    st.session_state.grading_data[p_id]['solved'].add(target)
                    new_match = True

        with st.chat_message("assistant"):
            try:
                solved_list = list(st.session_state.grading_data[p_id]['solved'])
                state_info = f"\n(Internal Status: Solved={solved_list}. NewMatch={new_match})"
                st.session_state.chat_sessions[p_id].send_message(user_input + state_info)
                st.rerun()
            except Exception:
                st.error("Gemini 응답 생성 중 오류가 발생했습니다.")
