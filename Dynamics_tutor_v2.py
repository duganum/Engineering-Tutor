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
    st.title("🛡️ Student Registration")
    st.markdown("### Welcome to Engineering Mechanics Tutor")
    st.info("Texas A&M University - Corpus Christi | Dr. Dugan Um")
    
    with st.form("registration_form"):
        u_name = st.text_input("Full Name (성함)")
        u_email = st.text_input("Email Address (이메일)")
        submit = st.form_submit_button("Start Tutoring")
        if submit:
            if u_name and u_email:
                st.session_state.user_info = {"name": u_name, "email": u_email}
                st.rerun()
            else:
                st.warning("Please enter both name and email.")
    st.stop()

# --- Page 1: 메인 메뉴 (문제 선택 화면) ---
if st.session_state.page == "landing":
    st.title("🚀 Engineering Mechanics Socratic Tutor")
    st.markdown(f"""
    ### Welcome, **{st.session_state.user_info['name']}**!
    This is a **free engineering tutor** developed by **Dr. Dugan Um** at **TAMUCC**.
    
    학습할 주제를 선택하세요. 진행 과정과 AI 분석 리포트는 **dugan.um@gmail.com**으로 자동 전송됩니다.
    """)
    
    if not PROBLEMS:
        st.error("❌ 문제를 불러올 수 없습니다. 'problems.json' 파일 형식을 확인하세요.")
        st.stop()

    # 카테고리별 분류
    categories = {}
    for p in PROBLEMS:
        full_cat = p.get('category', 'General: Unknown')
        cat_main = full_cat.split(":")[0].strip() if ":" in full_cat else full_cat
        if cat_main not in categories: categories[cat_main] = []
        categories[cat_main].append(p)

    # UI 렌더링
    for cat_name, probs in categories.items():
        st.header(cat_name)
        cols = st.columns(3)
        for idx, prob in enumerate(probs):
            with cols[idx % 3]:
                sub_cat = prob.get('category', '').split(":")[1].strip() if ":" in prob.get('category','') else "Problem"
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
        
        if st.button("⬅️ Back to Menu & Send Report"):
            history_text = ""
            if p_id in st.session_state.chat_sessions:
                for msg in st.session_state.chat_sessions[p_id].history:
                    role = "Tutor" if msg.role == "model" else "Student"
                    history_text += f"{role}: {msg.parts[0].text}\n"
            
            with st.spinner("AI가 분석 리포트를 생성하여 교수님께 전송 중입니다..."):
                report = analyze_and_send_report(
                    st.session_state.user_info['name'],
                    st.session_state.user_info['email'],
                    prob['category'],
                    history_text
                )
                st.session_state.last_report = report
                st.session_state.page = "report_view"
                st.rerun()

    # 채팅 세션 초기화
    if p_id not in st.session_state.chat_sessions:
        sys_prompt = (
            f"You are a Socratic Engineering Tutor. PROBLEM: {prob['statement']}. "
            f"Targets: {list(prob['targets'].keys())}. Found: {solved}. "
            "RULES: 1. Ask ONE guiding question at a time. 2. Focus on concepts/FBD first. "
            "3. Response ONLY in JSON: {'tutor_message': '...'}"
        )
        model = get_gemini_model(sys_prompt)
        if model:
            session = model.start_chat(history=[])
            session.send_message("Introduce the problem briefly and ask the first conceptual question.")
            st.session_state.chat_sessions[p_id] = session

    # 채팅 히스토리 표시
    if p_id in st.session_state.chat_sessions:
        for message in st.session_state.chat_sessions[p_id].history:
            if "Introduce the problem" in message.parts[0].text: continue
            role = "assistant" if message.role == "model" else "user"
            with st.chat_message(role):
                text = message.parts[0].text
                display_text = re.sub(r'\(Internal Status:.*?\)', '', text).strip()
                match = re.search(r'"tutor_message":\s*"(.*?)"', display_text, re.DOTALL)
                st.markdown(match.group(1) if match else display_text)

    # 입력 처리
    if user_input := st.chat_input("의견이나 정답을 입력하세요..."):
        with st.chat_message("user"): st.markdown(user_input)
        new_match = False
        for target, val in prob['targets'].items():
            if target not in st.session_state.grading_data[p_id]['solved']:
                if check_numeric_match(user_input, val):
                    st.session_state.grading_data[p_id]['solved'].add(target)
                    new_match = True
        
        with st.chat_message("assistant"):
            solved_list = list(st.session_state.grading_data[p_id]['solved'])
            state_info = f"\n(Internal Status: Solved={solved_list}. NewMatch={new_match})"
            st.session_state.chat_sessions[p_id].send_message(user_input + state_info)
            st.rerun()

# --- Page 3: 리포트 출력 화면 ---
elif st.session_state.page == "report_view":
    st.title("📊 Academic Achievement Report")
    st.success("리포트가 Dugan Um 교수님께 전송되었습니다.")
    st.markdown("---")
    st.markdown(st.session_state.get("last_report", "No report available."))
    if st.button("Confirm and Return to Menu"):
        st.session_state.page = "landing"
        st.rerun()
