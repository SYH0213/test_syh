"""
[ai-seong-han-juni]
이 파일은 '화자 분리 담당자'의 역할을 합니다.
하나의 오디오 파일에는 여러 사람의 목소리가 섞여있어요.
이 담당자는 목소리를 분석해서 '이건 1번 사람 목소리', '저건 2번 사람 목소리'처럼
각 목소리의 주인을 찾아내고 구분해주는 일을 합니다.
"""
# -*- coding: utf-8 -*-
import os
import logging
import torch
from pyannote.audio import Pipeline

# '비밀 금고'에서 Pyannote 서비스에 접속하기 위한 비밀번호(토큰)를 가져옵니다.
from ..config import get_api_key

def diarize_audio(audio_path: str):
    """
    pyannote.audio를 사용하여 오디오 파일의 화자를 분리합니다.
    
    Args:
        audio_path (str): 화자를 분리할 오디오 파일의 전체 경로.

    Returns:
        pyannote.core.Annotation: 화자 분리 결과. 실패 시 None.
    """
    token = get_api_key("PYANNOTE_TOKEN")
    if not token:
        logging.error("PYANNOTE_TOKEN이 없어 화자 분리를 진행할 수 없습니다.")
        return None
    if not os.path.exists(audio_path):
        logging.error(f"오디오 파일을 찾을 수 없습니다: {audio_path}")
        return None
    
    logging.info(f"오디오 파일({audio_path})에 대한 화자 분리를 시작합니다...")
    try:
        # 컴퓨터에 GPU(그래픽카드)가 있으면 GPU를 쓰고, 없으면 CPU를 사용합니다.
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logging.info(f"Pyannote: 사용 장치를 '{device}'(으)로 설정합니다.")

        # 미리 학습된 화자 분리 모델을 불러옵니다.
        pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1", use_auth_token=token)
        pipeline.to(device)

        # 오디오 파일에 파이프라인을 실행하여 화자를 분리합니다.
        diarization = pipeline(audio_path)
        logging.info("화자 분리 완료.")
        return diarization
    except Exception as e:
        logging.error(f"화자 분리 중 오류 발생: {e}")
        return None
