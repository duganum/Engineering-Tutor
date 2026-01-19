import streamlit as st
import google.generativeai as genai
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def get_gemini_model(system_instruction):
    """
    Configures and returns the Gemini model.
    Fixes the 'NotFound' error by using the explicit model path.
    """
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    
    # Use 'models/gemini-1.5-flash' to ensure the API finds the resource
    return genai.GenerativeModel(
        model_name='models/gemini-1.5-flash',
        system_instruction=system_instruction
    )

def load_problems():
    """Loads problem set from the local JSON file."""
    try:
        with open('problems.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading problems: {e}")
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
    """Generates an AI summary and emails it to the instructor using SSL."""
    
    # 1. AI Analysis
    # We use a neutral system instruction for the summary generator
    model = get_gemini_model("You are an educational assistant. Summarize the tutoring session.")
    
    report_prompt = f"""
    Please analyze this session for student {user_name} on the problem '{problem_title}'.
    Full Chat History: {chat_history}
    
    Provide a score (0-10) and a brief summary of their performance for the instructor.
    """
    
    try:
        response = model.generate_content(report_prompt)
        report_text = response.text
    except Exception as e:
        st.error(f"AI Analysis failed: {e}")
        return

    # 2. Email Setup
    sender_email = st.secrets["EMAIL_SENDER"]
    instructor_email = "dugan.um@gmail.com"
    app_password = st.secrets["EMAIL_PASSWORD"] # MUST be the 16-digit App Password

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = instructor_email
    msg['Subject'] = f"Engineering Tutor Report: {user_name} - {problem_title}"
    msg.attach(MIMEText(report_text, 'plain'))

    # 3. Secure SMTP Connection
    try:
        # SMTP_SSL on Port 465 is highly recommended for Streamlit Cloud
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(sender_email, app_password)
        server.send_message(msg)
        server.quit()
        st.success(f"Excellent! Your session report has been sent to Dr. Um.")
    except Exception as e:
        # If this fails with (535), check the App Password for spaces
        st.error(f"Report generated, but email delivery failed: {e}")
