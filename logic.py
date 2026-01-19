import streamlit as st
import google.generativeai as genai
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def get_gemini_model(system_instruction):
    # 1. Configure the API Key
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    
    # 2. Use the versioned model string
    # Sometimes 'gemini-1.5-flash' alias fails, but this exact version succeeds
    return genai.GenerativeModel(
        model_name='models/gemini-1.5-flash-latest', 
        system_instruction=system_instruction
    )

def load_problems():
    """Loads problems from the local JSON file."""
    try:
        with open('problems.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading problems.json: {e}")
        return {}

def check_numeric_match(user_val, correct_val, tolerance=0.05):
    """Checks if answer is within 5% tolerance."""
    try:
        u, c = float(user_val), float(correct_val)
        return abs(u - c) <= abs(tolerance * c)
    except (ValueError, TypeError):
        return False

def analyze_and_send_report(user_name, user_email, problem_title, chat_history):
    """Generates AI summary and sends email via SSL Port 465."""
    
    # Use the same model setup for the report
    model = get_gemini_model("Summarize this student's physics problem-solving session.")
    
    report_prompt = f"Analyze session for {user_name} on {problem_title}. History: {chat_history}"
    
    try:
        response = model.generate_content(report_prompt)
        report_text = response.text
    except Exception as e:
        st.error(f"AI Analysis failed: {e}")
        return

    # Email Logic
    sender = st.secrets["EMAIL_SENDER"]
    password = st.secrets["EMAIL_PASSWORD"] # 16-digit App Password, no spaces
    receiver = "dugan.um@gmail.com"

    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = receiver
    msg['Subject'] = f"Engineering Report: {user_name}"
    msg.attach(MIMEText(report_text, 'plain'))

    try:
        # SSL connection is the most stable for Streamlit
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(sender, password)
        server.send_message(msg)
        server.quit()
        st.success("Report emailed to Dr. Um!")
    except Exception as e:
        st.error(f"Email failed (Error 535? Check App Password): {e}")

