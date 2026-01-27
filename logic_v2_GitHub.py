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
    """강의 세션의 대화 내용을 바탕으로 이해도를 0-10점으로 평가합니다."""
    eval_instruction = (
        "You are an expert engineering professor. Your task is to evaluate the student's level of understanding "
        "based on the chat history. Rate the understanding from 0 to 10.\n"
        "0: No participation or complete misunderstanding.\n"
        "5: Basic grasp but struggles with core engineering logic.\n"
        "10: Perfect conceptual mastery.\n"
        "CRITICAL: Output ONLY the integer (e.g., '8'). No text, no explanation."
    )
    
    model = get_gemini_model(eval_instruction)
    if not model: return 0

    try:
        response = model.generate_content(f"Chat history to evaluate:\n{chat_history}")
        # Extract only the number from the response
        score_match = re.search(r"\d+", response.text)
        return int(score_match.group()) if score_match else 0
    except Exception:
        return 0

def analyze_and_send_report(user_name, topic_title, chat_history):
    """문제 풀이 또는 강의 세션을 분석하여 Dr. Um에게 이메일 리포트를 전송합니다."""
    
    # Get the numerical score first to include in the report
    score = evaluate_understanding_score(chat_history)
    
    report_instruction = (
        "You are an academic evaluator at Texas A&M University - Corpus Christi. "
        "Analyze this engineering education session (Problem Solving or Interactive Lecture).\n"
        "Your report must include:\n"
        "1. Session Overview: Focus of the discussion (e.g., Projectile Motion).\n"
        "2. Understanding Score: A summary of why the student earned their score.\n"
        "3. Concept Mastery: Strengths and gaps in the student's understanding.\n"
        "4. Engagement Level: How effectively the student interacted with the Socratic Tutor.\n"
        "5. CRITICAL: Quote exactly the section labeled '--- STUDENT FEEDBACK ---' in a part titled '**Student Feedback**'."
    )
    
    model = get_gemini_model(report_instruction)
    if not model: return "AI Analysis Unavailable"

    prompt = (
        f"Student Name: {user_name}\n"
        f"Topic: {topic_title}\n"
        f"Understanding Score (0-10): {score}\n\n"
        f"DATA:\n{chat_history}\n\n"
        "Please format the report professionally for Dr. Dugan Um."
    )
    
    try:
        response = model.generate_content(prompt)
        report_text = response.text
    except Exception as e:
        report_text = f"Analysis failed: {str(e)}"

    # Email 전송 로직
    sender = st.secrets["EMAIL_SENDER"]
    password = st.secrets["EMAIL_PASSWORD"] 
    receiver = "dugan.um@gmail.com" 

    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = receiver
    msg['Subject'] = f"Engineering Tutor Report ({user_name}): {topic_title} - Score: {score}/10"
    msg.attach(MIMEText(report_text, 'plain'))

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(sender, password)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        print(f"SMTP Error: {e}")
    
    return report_text
