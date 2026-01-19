import streamlit as st
import google.generativeai as genai
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def get_gemini_model(system_instruction):
    """
    Configures and returns the Gemini model.
    Accepts system_instruction as required by Dynamics_tutor_v2.py line 117.
    """
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    return genai.GenerativeModel(
        model_name='gemini-1.5-flash',
        system_instruction=system_instruction
    )

def load_problems():
    """Loads problem set from the local JSON file."""
    try:
        with open('problems.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def check_numeric_match(user_val, correct_val, tolerance=0.05):
    """Checks if the student's answer is within a 5% margin of error."""
    try:
        u = float(user_val)
        c = float(correct_val)
        return abs(u - c) <= abs(tolerance * c)
    except (ValueError, TypeError):
        return False

def analyze_and_send_report(user_name, user_email, problem_title, chat_history):
    """Generates an AI summary of the session and emails it to the instructor."""
    
    # 1. AI Analysis Section
    # We pass a simple instruction for the report generation
    model = get_gemini_model("You are an educational evaluator. Summarize the student's performance.")
    
    report_prompt = f"""
    Analyze the following tutoring session:
    Student Name: {user_name}
    Problem: {problem_title}
    Chat History: {chat_history}
    
    Please provide:
    1. A score from 0-10 based on their understanding.
    2. Key strengths shown.
    3. Specific areas where the student struggled.
    """
    
    try:
        response = model.generate_content(report_prompt)
        report_text = response.text
    except Exception as e:
        st.error(f"AI Analysis failed: {e}")
        return

    # 2. Email Configuration
    sender_email = st.secrets["EMAIL_SENDER"]
    # We send the report to you (the instructor)
    instructor_email = "dugan.um@gmail.com" 
    app_password = st.secrets["EMAIL_PASSWORD"] 

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = instructor_email
    msg['Subject'] = f"Tutor Report: {user_name} - {problem_title}"
    msg.attach(MIMEText(report_text, 'plain'))

    # 3. Secure Email Sending (SMTP_SSL Port 465)
    try:
        # Use SSL for a direct secure connection to Gmail
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(sender_email, app_password)
        server.send_message(msg)
        server.quit()
        st.success(f"Great job {user_name}! Your report has been sent to Dr. Um.")
    except Exception as e:
        # This catches the 535 error if the App Password is wrong or contains spaces
        st.error(f"Report generated, but email failed to send. Error: {e}")
