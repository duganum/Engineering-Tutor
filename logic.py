import streamlit as st
import google.generativeai as genai
import json
import smtplib
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def get_gemini_model(system_instruction):
    """Configures and returns the Gemini model using the stable alias."""
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
        
        return genai.GenerativeModel(
            model_name='gemini-1.5-flash', 
            system_instruction=system_instruction
        )
    except Exception as e:
        st.error(f"Failed to initialize Gemini: {e}")
        return None

def load_problems():
    """Loads problems from problems.json."""
    try:
        with open('problems.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading problems.json: {e}")
        return []

def check_numeric_match(user_val, correct_val, tolerance=0.05):
    """Checks if the user's numeric answer is within tolerance."""
    try:
        u_match = re.search(r"[-+]?\d*\.\d+|\d+", str(user_val))
        if not u_match:
            return False
            
        u = float(u_match.group())
        c = float(correct_val)
        
        if c == 0: return abs(u) < tolerance
        return abs(u - c) <= abs(tolerance * c)
    except:
        return False

def analyze_and_send_report(problem_title, chat_history):
    """Generates summary and emails it to Dr. Um."""
    model = get_gemini_model("You are a professor evaluating a student's Socratic tutoring session.")
    if not model:
        return "AI Analysis Unavailable"

    # Hardcoded student name since registration is removed
    user_name = "Engineering Student"
    prompt = f"Student: {user_name}\nProblem: {problem_title}\n\nChat History:\n{chat_history}"
    
    try:
        response = model.generate_content(prompt)
        report_text = response.text
    except:
        report_text = "Analysis failed, but session was recorded."

    sender = st.secrets["EMAIL_SENDER"]
    password = st.secrets["EMAIL_PASSWORD"] 
    # Hardcoded receiver
    receiver = "dugan.um@gmail.com"

    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = receiver
    msg['Subject'] = f"Engineering Tutor Report: {problem_title}"
    msg.attach(MIMEText(report_text, 'plain'))

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(sender, password)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        st.error(f"Email error: {e}")
    
    return report_text
