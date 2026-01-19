import streamlit as st
import json
import re
from logic import get_gemini_model, load_problems, check_numeric_match

st.set_page_config(page_title="Socratic Physics Agency", layout="wide")

# Initialize Session State
if "page" not in st.session_state: st.session_state.page = "landing"
if "chat_sessions" not in st.session_state: st.session_state.chat_sessions = {}
if "grading_data" not in st.session_state: st.session_state.grading_data = {}

PROBLEMS = load_problems()

# --- Page 1: Problem Selection ---
if st.session_state.page == "landing":
    st.title("🚀 Dynamics Socratic Agency")
    st.write("Welcome. Select a problem to begin your session.")
    
    for prob in PROBLEMS:
        if st.button(f"Analyze Problem {prob['id']}: {prob['category']}"):
            st.session_state.current_prob = prob
            st.session_state.page = "chat"
            st.rerun()

# --- Page 2: Persistent Socratic Chat ---
elif st.session_state.page == "chat":
    prob = st.session_state.current_prob
    p_id = prob['id']

    # 1. State-aware Prompting
    # grading_data[p_id]가 없을 경우를 대비해 안전하게 가져오기
    current_grading = st.session_state.grading_data.get(p_id, {'solved': set()})
    solved = list(current_grading.get('solved', []))
    remaining = [t for t in prob['targets'].keys() if t not in solved]
    
    sys_prompt = (
        f"You are a Socratic Physics Tutor. PROBLEM: {prob['statement']}. "
        f"Student goals: {list(prob['targets'].keys())}. Found so far: {solved}. "
        "RULES: 1. Be encouraging. 2. If student gives a formula, ask for the numbers. "
        "3. NEVER provide final numbers. 4. Respond ONLY in JSON: {'tutor_message': '...'}"
    )

    # 2. Initialize Chat Session
    if p_id not in st.session_state.chat_sessions:
        model = get_gemini_model(sys_prompt)
        if model:
            session = model.start_chat(history=[])
            st.session_state.chat_sessions[p_id] = session
            # p_id 키를 명확히 생성
            st.session_state.grading_data[p_id] = {'solved': set()}
            # Proactively trigger the first message
            session.send_message("Introduce the problem and ask for the first step.")
        else:
            st.error("API Error: Could not initialize model.")

    # UI Header
    cols = st.columns([2, 1])
    with cols[0]:
        st.subheader(f"Problem: {prob['category']}")
        st.info(prob['statement'])
    with cols[1]:
        st.metric("Targets Found", f"{len(solved)} / {len(prob['targets'])}")
        if st.button("⬅️ Back to Menu"):
            st.session_state.page = "landing"
            st.rerun()

    # 3. Display History
    if p_id in st.session_state.chat_sessions:
        for message in st.session_state.chat_sessions[p_id].history:
            if "Introduce the problem" in message.parts[0].text:
                continue
                
            role = "assistant" if message.role == "model" else "user"
            with st.chat_message(role):
                text = message.parts[0].text
                display_text = re.sub(r'\(Internal Status:.*?\)', '', text).strip()
                match = re.search(r'"tutor_message":\s*"(.*?)"', display_text, re.DOTALL)
                if match:
                    st.markdown(match.group(1))
                else:
                    st.markdown(display_text)

    # 4. Handle Input
    if user_input := st.chat_input("Enter your response..."):
        with st.chat_message("user"):
            st.markdown(user_input)
        
        # Check for numeric progress (에러 발생 구간 수정)
        if p_id not in st.session_state.grading_data:
            st.session_state.grading_data[p_id] = {'solved': set()}

        for target, val in prob['targets'].items():
            if check_numeric_match(user_input, val):
                st.session_state.grading_data[p_id]['solved'].add(target)

        # Update Gemini on current "State" and get response
        with st.chat_message("assistant"):
            # 안전하게 solved 리스트 추출
            solved_list = list(st.session_state.grading_data[p_id]['solved'])
            state_info = f"\n(Internal Status: Solved={solved_list})"
            try:
                response = st.session_state.chat_sessions[p_id].send_message(user_input + state_info)
                json_match = re.search(r'"tutor_message":\s*"(.*?)"', response.text, re.DOTALL)
                msg = json_match.group(1) if json_match else response.text
                st.markdown(msg)
            except Exception:
                st.error("Lost connection to Gemini. Please try again.")
        
        st.rerun()
