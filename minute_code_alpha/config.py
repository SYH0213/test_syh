"""
[ai-seong-han-juni]
이 파일은 우리 프로젝트의 '비밀 금고' 같은 역할을 합니다.
중요한 비밀번호(API 키)들을 코드에 직접 써놓지 않고,
.env 라는 비밀 파일에 숨겨두고, 필요할 때마다 여기서 안전하게 꺼내 씁니다.
덕분에 우리 코드가 더 안전해져요!
"""
# -*- coding: utf-8 -*-
import os
from dotenv import load_dotenv

# .env 파일을 찾아서 그 안에 있는 변수들을 환경변수로 만들어줍니다.
# 이제 코드 어디에서든 os.getenv("키_이름")으로 값을 불러올 수 있습니다.
load_dotenv()

def get_api_key(key_name: str) -> str:
    """
    환경변수에서 API 키를 가져옵니다.
    
    Args:
        key_name (str): 가져올 API 키의 이름 (예: "OPENAI_API_KEY")

    Returns:
        str: 찾아온 API 키 문자열
    """
    api_key = os.getenv(key_name)
    if not api_key:
        # 키가 없으면, 사용자에게 알려주는 경고 메시지를 출력합니다.
        print(f"경고: {key_name}을(를) .env 파일에서 찾을 수 없습니다.")
    return api_key

def check_api_keys(llm_choice: str):
    """필요한 API 키가 .env 파일에 모두 설정되었는지 확인합니다."""
    missing_keys = []
    # Pyannote 토큰은 항상 필요합니다.
    if not get_api_key("PYANNOTE_TOKEN"):
        missing_keys.append("PYANNOTE_TOKEN")
    # OpenAI 키는 STT와 GPT 모델 사용 시 필요합니다.
    if not get_api_key("OPENAI_API_KEY"):
        missing_keys.append("OPENAI_API_KEY")
    
    # Gemini 모델 선택 시 Google API 키가 필요합니다.
    if llm_choice == "gemini-2.5-pro" and not get_api_key("GOOGLE_API_KEY"):
        missing_keys.append("GOOGLE_API_KEY")
        
    if missing_keys:
        # 중복 제거 및 정렬
        unique_missing_keys = sorted(list(set(missing_keys)))
        return f"API 키가 .env 파일에 설정되지 않았습니다: {', '.join(unique_missing_keys)}"
    
    return None
