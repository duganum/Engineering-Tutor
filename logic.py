import streamlit as st
import google.generativeai as genai
import json
import smtplib
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def get_gemini_model(system_instruction):
    """Configures and returns the Gemini model using a robust model alias."""
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        # Changed from 'models/gemini-1.5-flash-latest' to 'gemini-1.5-flash'
        # This alias is more compatible with standard API calls
        return genai.GenerativeModel(
            model_name='gemini-1.5-flash', 
            system_instruction=system_instruction
        )
    except Exception as e:
        st.error(f"Model Configuration Error: {e}")
        return None

def load_problems():
    """Loads problems from the local JSON file."""
    try:
        with open('problems.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading problems.json: {e}")
        return []

def check_numeric_match(user_val, correct_val, tolerance=0.05):
    """Extracts numbers from string and checks within 5% tolerance."""
    try:
        # Use regex to find the first number (integer or float) in the string
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

def analyze_and_send_report(user_name, user_email, problem_title, chat_history):
    """Generates AI summary and sends email via SSL."""
    
    model = get_gemini_model("You are an academic evaluator. Summarize the student's performance.")
    if not model:
        return "Error: Could not initialize AI for reporting."

    report_prompt = f"Analyze session for {user_name} ({user_email}) on problem: {problem_title}. History: {chat_history}"
    
    try:
        response = model.generate_content(report_prompt)
        report_text = response.text
    except Exception as e:
        report_text = f"AI Analysis failed, but session completed. Error: {e}"

    # Email Logic
    sender = st.secrets["EMAIL_SENDER"]
    password = st.secrets["EMAIL_PASSWORD"] 
    receiver = "dugan.um@gmail.com"

    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = receiver
    msg['Subject'] = f"Engineering Tutor Report: {user_name}"
    msg.attach(MIMEText(report_text, 'plain'))

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(sender, password)
        server.send_message(msg)
        server.quit()
        return report_text
    except Exception as e:
        st.error(f"Email failed: {e}")
        return report_text

