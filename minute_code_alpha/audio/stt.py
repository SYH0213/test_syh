"""
[ai-seong-han-juni]
이 파일은 'STT(Speech-to-Text) 담당자'의 역할을 합니다.
'화자 분리 담당자'가 "이건 1번 사람 목소리야" 하고 오디오 조각을 넘겨주면,
이 담당자는 그 오디오를 듣고 "안녕하세요" 처럼 사람이 한 말을 글자로 받아쓰는 일을 합니다.
"""
# -*- coding: utf-8 -*-
import os
import logging
from openai import OpenAI # OpenAI 클라이언트 객체의 타입을 명시하기 위해 import 합니다.
from pydub import AudioSegment # AudioSegment 객체의 타입을 명시하기 위해 import 합니다.

def transcribe_segment(client: OpenAI, audio_segment: AudioSegment, segment_path: str, prompt: str, model: str) -> str:
    """
    Whisper API를 사용하여 오디오 세그먼트를 텍스트로 변환합니다.

    Args:
        client (OpenAI): 미리 생성된 OpenAI 클라이언트.
        audio_segment (AudioSegment): pydub으로 잘린 오디오 조각.
        segment_path (str): 오디오 조각을 임시로 저장할 파일 경로.
        prompt (str): Whisper 모델에 전달할 프롬프트 (힌트).
        model (str): 사용할 Whisper 모델 이름 (예: "whisper-1").

    Returns:
        str: 변환된 텍스트. 실패 시 빈 문자열.
    """
    try:
        # 1. 오디오 조각을 임시 파일로 저장합니다.
        audio_segment.export(segment_path, format="wav")
        
        # 2. 저장된 임시 파일을 열어서 Whisper AI에게 보냅니다.
        with open(segment_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model=model,
                file=audio_file,
                prompt=prompt,
                language="ko" # 한국어로 인식하도록 설정
            )
        return transcript.text
    except Exception as e:
        logging.error(f"Whisper API 호출 중 오류 발생: {e}")
        return ""
    finally:
        # 3. 작업이 끝나면 임시 파일을 항상 삭제합니다.
        if os.path.exists(segment_path):
            os.remove(segment_path)
