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
    """Loads problems from problems.json."""
    try:
        with open('problems.json', 'r') as f:
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
    """Generates AI summary with an Achievement Score and emails it to Dr. Um."""
    # Updated instruction to include scoring
    report_instruction = (
        "You are an academic evaluator. Analyze the student's Socratic tutoring session. "
        "Provide a summary of their conceptual understanding and assign an 'Achievement Score' "
        "from 0 to 10 based on their progress and accuracy."
    )
    
    model = get_gemini_model(report_instruction)
    if not model:
        return "AI Analysis Unavailable"

    prompt = (
        f"Student Name: {user_name}\n"
        f"Problem Topic: {problem_title}\n\n"
        f"Full Chat History:\n{chat_history}\n\n"
        "Please include a clear section titled 'ACHIEVEMENT SCORE: X/10' at the top of your report."
    )
    
    try:
        response = model.generate_content(prompt)
        report_text = response.text
    except:
        report_text = "Analysis generation failed, but session record exists."

    sender = st.secrets["EMAIL_SENDER"]
    password = st.secrets["EMAIL_PASSWORD"] 
    receiver = "dugan.um@gmail.com" 

    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = receiver
    msg['Subject'] = f"Dynamics Report ({user_name}): {problem_title}"
    msg.attach(MIMEText(report_text, 'plain'))

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(sender, password)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        st.error(f"Email failed: {e}")
    
    return report_text
