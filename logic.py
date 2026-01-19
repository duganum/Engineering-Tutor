import os
import json
import re
import streamlit as st
import google.generativeai as genai

def get_gemini_model(system_instruction):
    """Streamlit Secrets에 저장된 GEMINI_API_KEY를 사용하여 모델을 초기화합니다."""
    # 1. Secrets에서 올바른 키 이름을 가져오도록 수정 (GEMINI_API_KEY)
    api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
    
    if api_key:
        try:
            genai.configure(api_key=api_key)
            
            # 2. 가장 안정적인 모델명으로 직접 지정 (가장 빠른 응답 속도)
            model = genai.GenerativeModel(
                model_name='gemini-1.5-flash',
                system_instruction=system_instruction
            )
            return model
        except Exception as e:
            # 에러 발생 시 화면에 원인 출력 (디버깅용)
            st.error(f"Gemini 초기화 에러: {str(e)}")
            return None
    else:
        # 키를 찾지 못했을 때 메시지
        st.error("API Key를 찾을 수 없습니다. Streamlit Secrets에 'GEMINI_API_KEY'가 등록되어 있는지 확인하세요.")
    return None

def load_problems():
    """problems.json 파일에서 문제를 로드합니다."""
    try:
        with open("problems.json", "r", encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"문제 로드 에러: {str(e)}")
        return []

def check_numeric_match(user_text, target_value, tolerance=0.03):
    """학생의 답변 중 숫자가 정답과 3% 이내로 일치하는지 확인합니다."""
    # 숫자 추출 정규식
    numbers = re.findall(r"[-+]?\d*\.\d+|\d+", user_text)
    for num in numbers:
        try:
            val = float(num)
            # 0으로 나누기 방지를 위한 1e-9 추가
            if abs(val - target_value) / (abs(target_value) + 1e-9) < tolerance:
                return True
        except ValueError:
            continue
    return False
