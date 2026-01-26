import streamlit as st
import google.generativeai as genai
import json
import smtplib
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def get_gemini_model(system_instruction):
    """Configures and returns the Gemini model using verified 2.0-flash string."""
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
        
        return genai.GenerativeModel(
            model_name='models/gemini-2.0-flash', 
            system_instruction=system_instruction
        )
    except Exception as e:
        st.error(f"Failed to initialize Gemini: {e}")
        return None

def load_problems():
    """Loads problems from problems_v2_GitHub.json."""
    try:
        # Match the filename exactly as it appears in your repository
        with open('problems_v2_GitHub.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading problems.json: {e}")
        return []

def check_numeric_match(user_val, correct_val, tolerance=0.05):
    """Extracts numbers and checks if answer is within 5% tolerance."""
    try:
        u_match = re.search(r"[-+]?\d*\.\d+|\d+", str(user_val))
        if not u_match:
            return False
            
        u = float(u_match.group())
        c = float(correct_val)
        
        if c == 0: 
            return abs(u) < tolerance
        return abs(u - c) <= abs(tolerance * c)
    except (ValueError, TypeError, AttributeError):
        return False

def analyze_and_send_report(user_name, problem_title, chat_history):
    """Generates AI summary, captures student feedback, and emails it to Dr. Um."""
    
    # 1. Update instructions so the AI knows to look for the Feedback Tag
    report_instruction = (
        "You are an academic evaluator analyzing a Socratic tutoring session. "
        "Your report must include:\n"
        "1. An Achievement Score (0-10).\n"
        "2. A summary of the student's conceptual strengths and weaknesses.\n"
        "3. CRITICAL: Look for the section labeled '--- STUDENT FEEDBACK ---' at the bottom of the history. "
        "Create a dedicated section in your report titled '**Student's Direct Feedback**' and quote the student exactly."
    )
    
    model = get_gemini_model(report_instruction)
    if not model:
        return "AI Analysis Unavailable"

    prompt = (
        f"Student Name: {user_name}\n"
        f"Problem Topic: {problem_title}\n\n"
        f"FULL DATA (Includes Chat and Feedback):\n{chat_history}\n\n"
        "Please format the report professionally for Dr. Um. Ensure the 'ACHIEVEMENT SCORE' is at the top."
    )
    
    try:
        response = model.generate_content(prompt)
        report_text = response.text
    except Exception as e:
        report_text = f"Analysis failed: {str(e)}. However, the session was recorded."

    # 2. Email Configuration
    sender = st.secrets["EMAIL_SENDER"]
    password = st.secrets["EMAIL_PASSWORD"] 
    receiver = "dugan.um@gmail.com" 

    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = receiver
    msg['Subject'] = f"Dynamics Report ({user_name}): {problem_title}"
    msg.attach(MIMEText(report_text, 'plain'))

    # 3. Securely send the email
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(sender, password)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        # We don't want to crash the UI for the student if the email fails
        print(f"SMTP Error: {e}")
    
    return report_text
