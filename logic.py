import os
import json
import re
import streamlit as st
import google.generativeai as genai
import smtplib
from email.mime.text import MIMEText

def get_gemini_model(system_instruction):
    """
    404 에러(모델 못 찾음)를 해결하기 위해 사용 가능한 모델을 
    실시간으로 조회하여 초기화합니다.
    """
    api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        st.error("API Key를 찾을 수 없습니다. Secrets 설정을 확인하세요.")
        return None

    try:
        genai.configure(api_key=api_key)
        
        available_models = [
            m.name for m in genai.list_models() 
            if 'generateContent' in m.supported_generation_methods
        ]
        
        target_model = "models/gemini-1.5-flash" # 기본값
        if available_models:
            flash_models = [m for m in available_models if "flash" in m]
            target_model = flash_models[0] if flash_models else available_models[0]
        
        model = genai.GenerativeModel(
            model_name=target_model,
            system_instruction=system_instruction
        )
        return model
        
    except Exception as e:
        st.error(f"모델 초기화 실패 (404 대응 로직): {str(e)}")
        return None

def load_problems():
    """problems.json 파일에서 문제를 로드합니다."""
    try:
        with open("problems.json", "r", encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []

def check_numeric_match(user_text, target_value, tolerance=0.03):
    """숫자 일치 여부를 확인합니다."""
    numbers = re.findall(r"[-+]?\d*\.\d+|\d+", user_text)
    for num in numbers:
        try:
            val = float(num)
            if abs(val - target_value) / (abs(target_value) + 1e-9) < tolerance:
                return True
        except ValueError:
            continue
    return False

def analyze_and_send_report(user_name, user_email, problem_title, chat_history):
    """
    대화를 분석하여 Bloom's Taxonomy 기반 리포트를 생성하고 이메일을 전송합니다.
    """
    # 1. AI에게 대화 분석 요청
    analysis_prompt = f"""
    당신은 교육 전문가입니다. 다음 학생의 공학 튜터링 대화 내용을 분석하여 보고서를 작성하세요.
    
    학생 성함: {user_name}
    학습 주제: {problem_title}
    대화 내역:
    {chat_history}
    
    [작성 가이드라인]
    1. 학업 성취도 점수 (Achievement Score): 0점에서 10점 사이로 평가.
    2. Bloom's Taxonomy 수준: (기억, 이해, 적용, 분석, 평가, 창조) 중 현재 도달한 단계를 명시.
    3. 강점 및 약점: 학생이 잘 이해하고 있는 부분과 보완이 필요한 부분 요약.
    4. 학생을 위한 피드백: 학생에게 직접 전하는 짧은 격려와 조언.
    
    반드시 한국어로 깔끔하고 전문적인 형식으로 작성하세요.
    """
    
    try:
        # 분석용 모델 호출 (시스템 지침 없이 순수 분석용)
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(analysis_prompt)
        report_text = response.text

        # 2. 이메일 전송 (dugan.um@gmail.com)
        # 중요: 시스템 계정과 앱 비밀번호가 Secrets에 설정되어 있어야 합니다.
        sender_email = "your-system-email@gmail.com"  # 발송용 Gmail (수정 필요)
        sender_password = st.secrets["EMAIL_PASSWORD"] # Google 앱 비밀번호
        receiver_email = "dugan.um@gmail.com"

        msg = MIMEText(f"Student: {user_name} ({user_email})\n\n{report_text}")
        msg['Subject'] = f"[Engineering Tutor] Progress Report: {user_name} ({problem_title})"
        msg['From'] = sender_email
        msg['To'] = receiver_email

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, [receiver_email], msg.as_string())
        
        return report_text
    except Exception as e:
        return f"리포트 생성 및 전송 중 오류가 발생했습니다: {str(e)}"
