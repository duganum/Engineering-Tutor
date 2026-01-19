import os
import json
import re
import streamlit as st
import google.generativeai as genai

def get_gemini_model(system_instruction):
    """Finds the correct model name and initializes Gemini."""
    api_key = st.secrets.get("GOOGLE_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if api_key:
        genai.configure(api_key=api_key)
        try:
            # List models to find the specific naming convention (e.g. gemini-1.5-flash-latest)
            available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            target = next((m for m in available if "flash" in m.lower()), "models/gemini-1.5-flash")
            
            return genai.GenerativeModel(
                model_name=target,
                system_instruction=system_instruction
            )
        except Exception:
            return genai.GenerativeModel(model_name='gemini-1.5-flash', system_instruction=system_instruction)
    return None

def load_problems():
    """Loads problems from your JSON file."""
    try:
        with open("problems.json", "r") as f:
            return json.load(f)
    except Exception:
        return []

def check_numeric_match(user_text, target_value, tolerance=0.03):
    """Checks if any number in the student's text is within 3% of the target."""
    numbers = re.findall(r"[-+]?\d*\.\d+|\d+", user_text)
    for num in numbers:
        try:
            val = float(num)
            if abs(val - target_value) / (target_value + 1e-9) < tolerance:
                return True
        except ValueError:
            continue
    return False