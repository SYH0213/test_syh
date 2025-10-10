"""
[ai-seong-han-juni]
이 파일은 우리 프로젝트의 '규칙집' 같은 역할을 합니다.
오디오 파일을 어디에 저장할지, 결과 파일은 어디에 둘지, 어떤 AI 모델을 기본으로 사용할지 등
프로젝트의 여러 가지 설정값들을 한곳에 모아두는 곳이죠.
이렇게 규칙을 정해두면, 모든 담당자들이 헷갈리지 않고 정해진 대로 일을 처리할 수 있습니다.
"""
# -*- coding: utf-8 -*-
import os

# --- 경로 설정 ---
# 프로젝트의 최상위 폴더 (Module)
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 데이터 및 결과 폴더 (최상위 폴더 기준)
DATA_DIR = os.path.join(ROOT_DIR, "data")
RESULTS_DIR = os.path.join(ROOT_DIR, "results")
TEMP_DIR = os.path.join(ROOT_DIR, "temp")
CHROMA_PERSIST_DIR = os.path.join(ROOT_DIR, "chroma_db")


# --- 모델 및 처리 설정 ---
# STT 모델
STT_MODEL = "whisper-1"

# 사용 가능한 LLM 모델
AVAILABLE_LLMS = ["gpt-4o", "gemini-2.5-pro"]

# 기본 회의 주제 및 키워드 (UI에서 오버라이드 가능)
DEFAULT_MEETING_TOPIC = "회의"
DEFAULT_KEYWORDS = ["핵심", "내용", "정리"]
