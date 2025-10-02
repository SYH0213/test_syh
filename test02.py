# -*- coding: utf-8 -*-
import os
import sys
import time
import logging
from openai import OpenAI
from dotenv import load_dotenv
#수정
# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_api_key():
    """
    .env 파일에서 OpenAI API 키를 로드하고 설정합니다.
    """
    try:
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logging.error("OPENAI_API_KEY가 .env 파일에 없습니다.")
            return None
        return api_key
    except Exception as e:
        logging.error(f"API 키 로드 중 오류 발생: {e}")
        return None

def transcribe_audio_with_whisper(client, audio_file_path):
    """
    Whisper API를 사용하여 오디오 파일을 텍스트로 변환합니다.
    처리 시간도 함께 측정합니다.
    """
    if not os.path.exists(audio_file_path):
        logging.error(f"오디오 파일을 찾을 수 없습니다: {audio_file_path}")
        return None, 0

    logging.info(f"'{audio_file_path}' 파일의 음성 인식을 시작합니다...")
    
    try:
        with open(audio_file_path, "rb") as audio_file:
            start_time = time.time()
            transcript = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file
            )
            end_time = time.time()
        
        processing_time = end_time - start_time
        logging.info(f"음성 인식 완료. (처리 시간: {processing_time:.2f}초)")
        return transcript.text, processing_time
        
    except Exception as e:
        logging.error(f"Whisper API 호출 중 오류 발생: {e}")
        return None, 0

def save_transcript_to_file(transcript, original_filename):
    """
    변환된 텍스트를 파일로 저장합니다.
    """
    try:
        output_filename = f"transcript_{os.path.basename(original_filename)}.txt"
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(transcript)
        logging.info(f"변환된 텍스트를 '{output_filename}' 파일에 저장했습니다.")
        return output_filename
    except Exception as e:
        logging.error(f"파일 저장 중 오류 발생: {e}")
        return None

def main():
    """
    메인 실행 함수
    """
    # 1. API 키 로드
    api_key = load_api_key()
    if not api_key:
        sys.exit(1) # API 키가 없으면 프로그램 종료

    # OpenAI 클라이언트 초기화
    client = OpenAI(api_key=api_key)

    # 2. 오디오 파일 경로 설정
    audio_path = "data/20250923_script2.wav"

    # 3. Whisper API로 음성 변환
    transcribed_text, duration = transcribe_audio_with_whisper(client, audio_path)

    if transcribed_text:
        # 4. 결과 출력 및 저장
        print("\n--- 변환된 텍스트 ---")
        print(transcribed_text)
        print("--------------------")
        save_transcript_to_file(transcribed_text, audio_path)

if __name__ == "__main__":
    main()
