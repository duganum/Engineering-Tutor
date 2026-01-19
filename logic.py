import streamlit as st
import google.generativeai as genai
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def get_gemini_model():
    # Uses the "Tier 1" key you just set up
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    return genai.GenerativeModel('gemini-1.5-flash')

def load_problems():
    with open('problems.json', 'r') as f:
        return json.load(f)

def check_numeric_match(user_val, correct_val, tolerance=0.05):
    try:
        u = float(user_val)
        c = float(correct_val)
        return abs(u - c) <= abs(tolerance * c)
    except:
        return False

def analyze_and_send_report(user_name, user_email, problem_title, chat_history):
    # 1. Generate Report with Gemini
    model = get_gemini_model()
    prompt = f"Analyze this tutoring session for {user_name} on {problem_title}. History: {chat_history}. Summarize score (0-10) and feedback."
    
    try:
        response = model.generate_content(prompt)
        report_text = response.text
    except Exception as e:
        st.error(f"AI Analysis failed: {e}")
        return

    # 2. Send Email using the 16-digit App Password
    sender_email = st.secrets["EMAIL_SENDER"]
    receiver_email = "dugan.um@gmail.com" # Your copy
    password = st.secrets["EMAIL_PASSWORD"] # This MUST be the 16-digit App Password

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = f"Engineering Report: {user_name} - {problem_title}"
    msg.attach(MIMEText(report_text, 'plain'))

    try:
        # Port 465 is the "Golden Standard" for Streamlit + Gmail
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(sender_email, password)
        server.send_message(msg)
        server.quit()
        st.success("Report generated and emailed successfully!")
    except Exception as e:
        st.error(f"Report generated but email failed: {e}")
