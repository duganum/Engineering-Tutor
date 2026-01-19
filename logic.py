import os
import json
import re
import streamlit as st
import google.generativeai as genai

def get_gemini_model(system_instruction):
    """
    Secrets의 GEMINI_API_KEY를 사용하여 모델을 초기화합니다.
    404 에러 방지를 위해 모델명을 표준화했습니다.
    """
    # 1. Secrets에서 키 가져오기
    api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        st.error("API Key를 찾을 수 없습니다. Streamlit Secrets 설정을 확인하세요.")
        return None

    try:
        # 2. API 설정
        genai.configure(api_key=api_key)
        
        # 3. 모델 생성 (404 에러 해결을 위해 'models/' 접두사 없이 시도)
        # 대부분의 최신 환경에서는 'gemini-1.5-flash'가 표준입니다.
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash', 
            system_instruction=system_instruction
        )
        
        # 모델이 정상 작동하는지 가벼운 테스트 (선택 사항)
        return model
        
    except Exception as e:
        # 상세 에러 로그 출력
        st.error(f"모델 초기화 중 오류 발생: {str(e)}")
        return None

def load_problems():
    """problems.json 파일에서 문제를 로드합니다."""
    try:
        # 파일 경로와 인코딩 확인
        with open("problems.json", "r", encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("problems.json 파일을 찾을 수 없습니다.")
        return []
    except Exception as e:
        st.error(f"문제 로드 오류: {e}")
        return []

def check_numeric_match(user_text, target_value, tolerance=0.03):
    """
    학생 답변 중 숫자가 정답과 3% 이내로 일치하는지 확인합니다.
    예: 정답이 39.24일 때, 사용자가 39.2를 입력해도 정답 처리
    """
    # 정규식을 이용해 텍스트에서 숫자(정수 및 실수)만 모두 추출
    numbers = re.findall(r"[-+]?\d*\.\d+|\d+", user_text)
    
    for num in numbers:
        try:
            val = float(num)
            # 상대 오차 계산 (분모가 0이 되는 것을 방지하기 위해 아주 작은 값 1e-9 추가)
            if abs(val - target_value) / (abs(target_value) + 1e-9) < tolerance:
                return True
        except ValueError:
            continue
            
    return False
