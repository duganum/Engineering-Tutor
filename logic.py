import os
import json
import re
import streamlit as st
import google.generativeai as genai

def get_gemini_model(system_instruction):
    """Gemini 모델을 안전하게 초기화합니다."""
    # Secrets에서 키 가져오기
    api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        st.error("API Key가 없습니다. Streamlit Secrets 설정을 확인하세요.")
        return None

    try:
        genai.configure(api_key=api_key)
        
        # 모델 설정: system_instruction을 명시적 인자로 전달
        # 주의: 'models/gemini-1.5-flash' 형식을 사용해야 안전합니다.
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            system_instruction=system_instruction
        )
        return model
    except Exception as e:
        st.error(f"모델 초기화 실패: {str(e)}")
        return None

def load_problems():
    """문제 파일을 로드합니다."""
    try:
        with open("problems.json", "r", encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        return []

def check_numeric_match(user_text, target_value, tolerance=0.03):
    """숫자 일치 여부를 확인합니다."""
    numbers = re.findall(r"[-+]?\d*\.\d+|\d+", user_text)
    for num in numbers:
        try:
            val = float(num)
            if abs(val - target_value) / (abs(target_value) + 1e-9) < tolerance:
                return True
        except ValueError:
            continue
    return False
