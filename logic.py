import os
import json
import re
import streamlit as st
import google.generativeai as genai

def get_gemini_model(system_instruction):
    """
    404 에러(모델 못 찾음)를 해결하기 위해 사용 가능한 모델을 
    실시간으로 조회하여 초기화합니다.
    """
    api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        st.error("API Key를 찾을 수 없습니다. Secrets 설정을 확인하세요.")
        return None

    try:
        genai.configure(api_key=api_key)
        
        # [해결책] 서버에서 사용 가능한 모델 리스트를 직접 가져옵니다.
        available_models = [
            m.name for m in genai.list_models() 
            if 'generateContent' in m.supported_generation_methods
        ]
        
        # 1. 'gemini-1.5-flash'가 포함된 모델을 우선 선택
        # 2. 없으면 리스트의 첫 번째 모델 선택
        # 3. 리스트가 비어있으면 기본값 사용
        target_model = "models/gemini-1.5-flash" # 기본값
        if available_models:
            flash_models = [m for m in available_models if "flash" in m]
            target_model = flash_models[0] if flash_models else available_models[0]
        
        model = genai.GenerativeModel(
            model_name=target_model,
            system_instruction=system_instruction
        )
        return model
        
    except Exception as e:
        st.error(f"모델 초기화 실패 (404 대응 로직): {str(e)}")
        return None

def load_problems():
    """problems.json 파일에서 문제를 로드합니다."""
    try:
        with open("problems.json", "r", encoding='utf-8') as f:
            return json.load(f)
    except Exception:
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
