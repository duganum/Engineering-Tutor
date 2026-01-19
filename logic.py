def analyze_and_send_report(user_name, user_email, problem_title, chat_history):
    """
    Analyzes the conversation for a simplified report and sends it via email.
    """
    # 1. AI Analysis Section
    # We use a neutral system instruction to minimize token usage
    model = get_gemini_model("Analyze engineering student performance concisely.")
    
    # Streamlined Prompt (Simplified for speed and quota saving)
    prompt = f"""
    Task: Evaluate the engineering tutoring session below.
    Student: {user_name}
    Topic: {problem_title}
    
    Conversation History:
    {chat_history}
    
    Format the report with these 4 headers:
    1. Achievement Score (0-10)
    2. Specific Strengths
    3. Areas for Improvement
    4. Feedback for the Student
    """
    
    report_text = "Analysis report could not be generated due to AI quota limits."
    
    try:
        if model:
            # Use generation_config to limit response length (saves quota)
            response = model.generate_content(
                prompt, 
                generation_config={"max_output_tokens": 500, "temperature": 0.7}
            )
            report_text = response.text
    except Exception as ai_err:
        report_text = f"AI Analysis Error: {str(ai_err)}"

    # 2. Email Section
    # Update 'sender' to the Gmail address you created the App Password for
    sender = "your-gmail@gmail.com" 
    receiver = "dugan.um@gmail.com"
    
    try:
        # Check if password exists in secrets
        if "EMAIL_PASSWORD" not in st.secrets:
            raise ValueError("EMAIL_PASSWORD not found in Streamlit Secrets.")
            
        pw = st.secrets["EMAIL_PASSWORD"]
        
        msg = MIMEText(f"Student: {user_name} ({user_email})\n\n{report_text}")
        msg['Subject'] = f"[Tutor Report] {user_name} - {problem_title}"
        msg['From'] = sender
        msg['To'] = receiver

        # Standard Gmail SMTP logic
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, pw)
            server.sendmail(sender, receiver, msg.as_string())
            
        return report_text # Success

    except Exception as e:
        # If email fails, we still return the report_text so the student can see it
        error_msg = f"Report generated, but email failed to send.\nReason: {str(e)}\n\n--- Report ---\n{report_text}"
        return error_msg
