import streamlit as st
import google.generativeai as genai
import json
import smtplib
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def get_gemini_model(system_instruction):
    """Gemini 2.0 Flash 모델을 설정하고 반환합니다."""
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
        return genai.GenerativeModel(
            model_name='models/gemini-2.0-flash', 
            system_instruction=system_instruction
        )
    except Exception as e:
        st.error(f"Gemini 초기화 실패: {e}")
        return None

def load_problems():
    """저장소의 JSON 파일에서 문제 목록을 불러옵니다."""
    try:
        with open('problems_v2_GitHub.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"problems.json 로드 에러: {e}")
        return []

def check_numeric_match(user_val, correct_val, tolerance=0.05):
    """숫자를 추출하여 정답과 5% 오차 범위 내에 있는지 확인합니다."""
    try:
        u_match = re.search(r"[-+]?\d*\.\d+|\d+", str(user_val))
        if not u_match: return False
        u = float(u_match.group())
        c = float(correct_val)
        if c == 0: return abs(u) < tolerance
        return abs(u - c) <= abs(tolerance * c)
    except (ValueError, TypeError, AttributeError):
        return False

def evaluate_understanding_score(chat_history):
    """
    강의 세션의 대화 내용을 바탕으로 이해도를 0-10점으로 평가합니다.
    수식 사용 여부에 따라 점수 상한선을 둡니다.
    """
    eval_instruction = (
        "You are a strict Engineering Professor at Texas A&M University - Corpus Christi. "
        "Evaluate the student's level of understanding from 0 to 10 based ONLY on the chat history.\n\n"
        "STRICT SCORING RUBRIC:\n"
        "0-3: Little to no participation or irrelevant answers.\n"
        "4-5: Good conversational engagement but NO use of governing equations or technical formulas.\n"
        "6-8: Shows conceptual understanding and correctly identifies/uses the relevant equations.\n"
        "9-10: Complete mastery, correct use of equations, and clear explanation of the physics logic.\n\n"
        "CRITICAL RULE: If the student has not correctly mentioned or applied the RELEVANT EQUATIONS "
        "for the topic, you MUST NOT give a score higher than 5, regardless of how well they talk. "
        "Output ONLY the integer."
    )
    
    model = get_gemini_model(eval_instruction)
    if not model: return 0

    try:
        response = model.generate_content(f"Chat history to evaluate:\n{chat_history}")
        # 숫자만 추출
        score_match = re.search(r"\d+", response.text)
        if score_match:
            score = int(score_match.group())
            return min(max(score, 0), 10) # 0-10 사이 유지
        return 0
    except Exception:
        return 0

def analyze_and_send_report(user_name, topic_title, chat_history):
    """문제 풀이 또는 강의 세션을 분석하여 Dr. Um에게 이메일 리포트를 전송합니다."""
    
    # 이메일 전송 전 점수 산출
    score = evaluate_understanding_score(chat_history)
    
    report_instruction = (
        "You are an academic evaluator. Analyze this engineering session.\n"
        "Your report must include:\n"
        "1. Session Overview\n"
        f"2. Numerical Understanding Score: {score}/10\n"
        "3. Technical Accuracy: Did they use the correct equations?\n"
        "4. Concept Mastery: Strengths and gaps.\n"
        "5. Engagement Level\n"
        "6. CRITICAL: Quote the section '--- STUDENT FEEDBACK ---' exactly."
    )
    
    model = get_gemini_model(report_instruction)
    if not model: return "AI Analysis Unavailable"

    prompt = (
        f"Student Name: {user_name}\n"
        f"Topic: {topic_title}\n"
        f"Assigned Score: {score}/10\n\n"
        f"DATA:\n{chat_history}\n\n"
        "Please format the report professionally for Dr. Dugan Um."
    )
    
    try:
        response = model.generate_content(prompt)
        report_text = response.text
    except Exception as e:
        report_text = f"Analysis failed: {str(e)}"

    # Email configuration
    sender = st.secrets["EMAIL_SENDER"]
    password = st.secrets["EMAIL_PASSWORD"] 
    receiver = "dugan.um@gmail.com" 

    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = receiver
    msg['Subject'] = f"Eng. Tutor ({user_name}): {topic_title} [Score: {score}/10]"
    msg.attach(MIMEText(report_text, 'plain'))

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(sender, password)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        print(f"SMTP Error: {e}")
    
    return report_text
