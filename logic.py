import os
import json
import re
import streamlit as st
import google.generativeai as genai
import smtplib
from email.mime.text import MIMEText

def get_gemini_model(system_instruction):
    api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key: return None
    try:
        genai.configure(api_key=api_key)
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        target_model = next((m for m in available_models if "flash" in m), "models/gemini-1.5-flash")
        return genai.GenerativeModel(model_name=target_model, system_instruction=system_instruction)
    except: return None

def load_problems():
    try:
        with open("problems.json", "r", encoding='utf-8') as f:
            return json.load(f)
    except: return []

def check_numeric_match(user_text, target_value, tolerance=0.03):
    numbers = re.findall(r"[-+]?\d*\.\d+|\d+", user_text)
    for num in numbers:
        try:
            val = float(num)
            if abs(val - target_value) / (abs(target_value) + 1e-9) < tolerance: return True
        except: continue
    return False

def analyze_and_send_report(user_name, user_email, problem_title, chat_history):
    # Dynamic model retrieval to avoid 404
    model = get_gemini_model("You are an expert educational analyst.")
    
    prompt = f"""
    Analyze the following engineering tutoring session.
    Student: {user_name}, Problem: {problem_title}
    
    Conversation History:
    {chat_history}
    
    Provide a professional report in English including:
    1. Achievement Score (0-10 scale)
    2. Bloom's Taxonomy Level reached (Remembering, Understanding, Applying, Analyzing, Evaluating, Creating)
    3. Specific strengths and areas for improvement.
    4. Feedback for the student.
    """
    
    report_text = "Analysis failed."
    try:
        if model:
            response = model.generate_content(prompt)
            report_text = response.text
        
        # Email settings
        sender = "your-gmail@gmail.com" # Replace with your actual sender email
        pw = st.secrets["EMAIL_PASSWORD"]
        
        msg = MIMEText(f"Student: {user_name} ({user_email})\n\n{report_text}")
        msg['Subject'] = f"[Tutor Report] {user_name} - {problem_title}"
        msg['From'] = sender
        msg['To'] = "dugan.um@gmail.com"

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, pw)
            server.sendmail(sender, "dugan.um@gmail.com", msg.as_string())
        return report_text
    except Exception as e:
        return f"Report generated but email failed: {str(e)}\n\n{report_text}"
