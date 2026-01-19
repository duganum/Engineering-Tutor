import os
import json
import re
import streamlit as st
import google.generativeai as genai

def get_gemini_model(system_instruction):
    """
    Secrets에서 키를 가져와 Gemini 모델을 초기화합니다.
    404 에러 방지를 위해 가장 호환성이 높은 모델 이름을 사용합니다.
    """
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key:
        st.error("API Key가 Secrets에 설정되지 않았습니다.")
        return None

    try:
        genai.configure(api_key=api_key)
        
        # 1. 가장 호환성이 높은 모델 이름을 순서대로 시도합니다.
        # 최신 SDK에서는 'gemini-1.5-flash'를 기본으로 사용합니다.
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash', 
            system_instruction=system_instruction
        )
        return model
        
    except Exception as e:
        # 만약 위 설정에서 에러가 날 경우, 직접 모델 리스트에서 사용 가능한 것을 찾습니다.
        try:
            available_models = [m.name for m in genai.list_models() 
                                if 'generateContent' in m.supported_generation_methods]
            # 'flash'가 포함된 모델 중 가장 첫 번째 것을 선택
            target_model = next((m for m in available_models if "flash" in m), "models/gemini-1.5-flash")
            
            return genai.GenerativeModel(
                model_name=target_model,
                system_instruction=system_instruction
            )
        except Exception as inner_e:
            st.error(f"모델을 초기화할 수 없습니다: {str(inner_e)}")
            return None

def load_problems():
    """problems.json 파일에서 문제를 로드합니다."""
    try:
        with open("problems.json", "r", encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []

def check_numeric_match(user_text, target_value, tolerance=0.03):
    """학생의 답변 숫자와 정답 숫자를 비교합니다."""
    numbers = re.findall(r"[-+]?\d*\.\d+|\d+", user_text)
    for num in numbers:
        try:
            val = float(num)
            if abs(val - target_value) / (abs(target_value) + 1e-9) < tolerance:
                return True
        except ValueError:
            continue
    return False
