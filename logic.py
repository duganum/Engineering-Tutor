import os
import json
import re
import streamlit as st
import google.generativeai as genai

def get_gemini_model(system_instruction):
    """Secrets의 GEMINI_API_KEY를 사용하여 모델을 안전하게 초기화합니다."""
    # Streamlit Secrets와 이름이 정확히 일치해야 합니다.
    api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        st.error("API Key를 찾을 수 없습니다. Streamlit Secrets 설정을 확인하세요.")
        return None

    try:
        genai.configure(api_key=api_key)
        
        # 모델명 앞에 'models/'를 붙이는 것이 가장 호환성이 좋습니다.
        model = genai.GenerativeModel(
            model_name='models/gemini-1.5-flash',
            system_instruction=system_instruction
        )
        return model
    except Exception as e:
        st.error(f"모델 초기화 실패: {str(e)}")
        return None

def load_problems():
    """problems.json 파일에서 문제를 로드합니다."""
    try:
        with open("problems.json", "r", encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []

def check_numeric_match(user_text, target_value, tolerance=0.03):
    """학생 답변 중 숫자가 정답과 3% 이내로 일치하는지 확인합니다."""
    # 텍스트 내의 모든 숫자 추출
    numbers = re.findall(r"[-+]?\d*\.\d+|\d+", user_text)
    for num in numbers:
        try:
            val = float(num)
            # 상대 오차 계산 (0 나누기 방지 1e-9 추가)
            if abs(val - target_value) / (abs(target_value) + 1e-9) < tolerance:
                return True
        except ValueError:
            continue
    return False
