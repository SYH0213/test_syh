"""
[ai-seong-han-juni]
이 파일은 우리 프로젝트의 '최종 지휘자' 역할을 합니다.
지금까지 만든 모든 담당자들과 팀들을 한데 모아,
이 프로젝트를 실제로 시작하고 실행시키는 역할을 하죠.
컴퓨터에게 "자, 이제 회의록 정리 앱을 시작해!"라고 명령하는 파일입니다.
"""
# -*- coding: utf-8 -*-
import os
import logging

# 우리가 만든 UI의 '인테리어 디자이너'를 가져옵니다.
from .ui.layout import create_ui
# '규칙집'에서 필요한 폴더 이름들을 가져옵니다.
from .settings import (
    AUDIO_INPUT_DIR_NAME,
    RESULTS_DIR_NAME,
    TEMP_DIR_NAME
)

# --- 기본 설정 및 디렉터리 생성 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_directories():
    """프로젝트에 필요한 모든 디렉터리를 생성합니다."""
    # 현재 파일이 있는 곳을 기준으로 프로젝트의 가장 위쪽 폴더를 찾습니다.
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
    
    # '규칙집'에 적힌 폴더 이름들을 가져와서 실제 폴더를 만듭니다.
    dir_names = [AUDIO_INPUT_DIR_NAME, RESULTS_DIR_NAME, TEMP_DIR_NAME]
    
    for dir_name in dir_names:
        path = os.path.join(ROOT_DIR, dir_name)
        os.makedirs(path, exist_ok=True) # 폴더가 없으면 만들고, 있으면 그냥 넘어갑니다.
        logging.info(f"Directory '{path}' is ready.")

# --- 애플리케이션 실행 ---
if __name__ == "__main__":
    # 1. 필요한 폴더들을 미리 만들어둡니다.
    setup_directories()
    
    # 2. UI '인테리어 디자이너'에게 화면을 만들어달라고 요청합니다.
    app = create_ui()
    
    # 3. 만들어진 화면을 컴퓨터에 띄워서 사용자가 볼 수 있게 합니다.
    app.launch()
