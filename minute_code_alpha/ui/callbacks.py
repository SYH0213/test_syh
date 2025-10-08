"""
[ai-seong-han-juni]
이 파일은 UI 팀의 '안내 데스크 직원' 역할을 합니다.
사용자가 화면에서 버튼을 누르거나, 파일을 선택하는 등 어떤 행동을 했을 때,
그 행동에 맞춰 실제 기능을 실행하는 일을 담당합니다.
예를 들어, '처리 시작' 버튼을 누르면 '프로젝트 매니저'에게 회의록 처리를 지시하고,
그 결과를 받아서 화면에 요약본이나 대화록을 보여주는 식이죠.
"""
# -*- coding: utf-8 -*-
import gradio as gr
import os
import logging
import re
import uuid
import json
from slugify import slugify

# 우리가 만든 모듈들을 가져옵니다.
from ..pipelines.main_pipeline import run_pipeline
from ..settings import (
    AUDIO_INPUT_DIR_NAME,
    RESULTS_DIR_NAME,
    AVAILABLE_LLMS,
    DEFAULT_MEETING_TOPIC,
    DEFAULT_KEYWORDS
)
from .handlers import (
    get_audio_files_for_df,
    get_audio_files_for_dropdown,
    refresh_audio_dropdown,
    upload_file,
    save_recording
)
from ..chatbot.graph import run_query

# --- 기본 설정 ---
# 프로젝트의 중요한 폴더 위치를 설정합니다.
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(ROOT_DIR, AUDIO_INPUT_DIR_NAME)
RESULTS_DIR = os.path.join(ROOT_DIR, RESULTS_DIR_NAME)

# --- UI 헬퍼 함수 ---

def create_zoom_link(url):
    """Zoom 링크를 받아서 클릭 가능한 마크다운 링크로 만듭니다."""
    if url and "zoom.us" in url:
        return gr.Markdown(f">➡️ <a href='{url}' target='_blank' style='color: blue; text-decoration: underline;'>클릭하여 Zoom 회의 열기</a>")
    elif not url:
        return gr.Markdown("")
    return gr.Markdown("<span style='color: red;'>유효한 Zoom 회의 링크를 입력해주세요.</span>")

def get_processed_meetings():
    """처리된 회의록 목록을 스캔하여 드롭다운용으로 반환합니다."""
    processed_meetings = []
    if not os.path.exists(RESULTS_DIR):
        return processed_meetings

    for folder_name in os.listdir(RESULTS_DIR):
        folder_path = os.path.join(RESULTS_DIR, folder_name)
        if os.path.isdir(folder_path):
            base_filename = '_'.join(folder_name.split('_')[:-1])
            corrected_file = f"corrected_{base_filename}.txt"
            if os.path.exists(os.path.join(folder_path, corrected_file)):
                # 1. Transliterate base_filename to an ASCII slug
                slugified_name = slugify(base_filename, separator='_', lowercase=True, replacements=[['.', '_']])
                # 2. Apply final sanitization (ChromaDB specific) - remove any remaining non-allowed chars
                collection_name = re.sub(r'[^a-zA-Z0-9._-]', '_', slugified_name)

                # 3. Ensure collection_name meets ChromaDB's rules (min 3 chars, starts/ends with alphanumeric)
                # Remove leading/trailing underscores that might violate start/end rule
                collection_name = collection_name.strip('_')
                
                # If it became empty after stripping, or is too short, use a fallback
                if not collection_name or len(collection_name) < 3:
                    # Fallback to a sanitized version of the full folder_name if base_filename is too short/empty
                    temp_name = slugify(folder_name, separator='_', lowercase=True, replacements=[['.', '_']])
                    temp_name = re.sub(r'[^a-zA-Z0-9._-]', '_', temp_name).strip('_')
                    if len(temp_name) >= 3:
                        collection_name = temp_name
                    else:
                        # Last resort: generate a unique, valid name
                        collection_name = "meeting_" + str(uuid.uuid4())[:8].replace('-', '_') # Ensure it's always valid and long enough
                processed_meetings.append((folder_name, collection_name))
    
    return sorted(processed_meetings, key=lambda x: x[0], reverse=True)

def format_summary_json_to_markdown(summary_json_str: str) -> str:
    """
    요약 결과인 JSON 문자열을 사용자가 보기 좋은 Markdown 형식으로 변환합니다.
    """
    if not summary_json_str or "요약 파일을 찾을 수 없습니다." in summary_json_str:
        return "요약 내용이 없습니다."

    try:
        # LLM의 응답에 포함될 수 있는 비-JSON 텍스트(예: 설명, 코드 블록 마커)를 정리
        json_start_index = summary_json_str.find('{')
        json_end_index = summary_json_str.rfind('}')
        if json_start_index == -1 or json_end_index == -1:
            return summary_json_str # JSON 객체를 찾을 수 없으면 원본 반환

        summary_json_str = summary_json_str[json_start_index:json_end_index+1]
        data = json.loads(summary_json_str)
        
        md = ""

        if data.get("decisions"):
            md += "### 주요 결정사항\n"
            for item in data["decisions"]:
                md += f"- {item.get('text', 'N/A')}\n"
            md += "\n"

        if data.get("action_items"):
            md += "### Action Items\n"
            for item in data["action_items"]:
                assignee = item.get('assignee', '미지정')
                task = item.get('task', 'N/A')
                due = f" (기한: {item.get('due')})" if item.get('due') else ""
                md += f"- **{assignee}**: {task}{due}\n"
            md += "\n"

        if data.get("key_points"):
            md += "### 핵심 논의\n"
            for item in data["key_points"]:
                topic = item.get('topic', '소주제 없음')
                summary_text = item.get('summary', 'N/A')
                md += f"- **({topic})**: {summary_text}\n"
            md += "\n"
        
        return md if md else "요약 내용에서 표시할 항목을 찾지 못했습니다."

    except json.JSONDecodeError:
        logging.error(f"요약 내용 JSON 파싱 실패. 원본 텍스트를 반환합니다.")
        return summary_json_str
    except Exception as e:
        logging.error(f"요약 내용 마크다운 변환 중 오류: {e}")
        return f"요약 내용을 표시하는 중 오류가 발생했습니다: {e}"

# --- Gradio 콜백 래퍼 함수 (ui.handlers의 함수들을 Gradio에 연결하기 위함) ---

def upload_wrapper(file, progress=gr.Progress(track_tqdm=True)):
    """upload_file에 DATA_DIR을 전달하고 Gradio 프로그레스 바를 활성화하는 래퍼 함수"""
    return upload_file(file, DATA_DIR, progress)

def save_recording_wrapper(temp_file, fname):
    """save_recording에 DATA_DIR을 전달하기 위한 래퍼 함수"""
    return save_recording(temp_file, fname, DATA_DIR)

# --- Gradio 콜백 함수 (사용자 행동에 반응하는 함수들) ---

def run_processing_and_update_ui(audio_filename, llm_choice, topic, keywords_str, progress=gr.Progress(track_tqdm=True)):
    """처리 파이프라인을 실행하고 UI를 업데이트합니다."""
    if not audio_filename:
        return "처리할 오디오 파일을 먼저 선택해주세요.", "", "", gr.Dropdown(choices=[name for name, _ in get_processed_meetings()]), {}

    progress(0, desc="준비 중...")
    audio_path = os.path.join(DATA_DIR, audio_filename)
    keywords = [k.strip() for k in keywords_str.split(',') if k.strip()]

    results_path, message = run_pipeline(audio_path, llm_choice, topic, keywords)
    progress(0.9, desc="결과 파일 로딩 중...")

    if not results_path:
        return f"**처리 실패:** {message}", "", "", gr.Dropdown(choices=[name for name, _ in get_processed_meetings()]), {}

    summary_markdown = "요약 파일을 찾을 수 없습니다."
    corrected_text = "교정된 텍스트 파일을 찾을 수 없습니다."
    try:
        base_filename = os.path.splitext(audio_filename)[0]
        summary_path = os.path.join(results_path, f"summary_{base_filename}.md")
        corrected_path = os.path.join(results_path, f"corrected_{base_filename}.txt")
        
        with open(summary_path, 'r', encoding='utf-8') as f:
            summary_json_str = f.read()
            summary_markdown = format_summary_json_to_markdown(summary_json_str)

        with open(corrected_path, 'r', encoding='utf-8') as f:
            corrected_text = f.read()
    except Exception as e:
        logging.error(f"결과 파일 읽기 오류: {e}")
        message += f"\n결과 파일 로딩 중 오류 발생: {e}"

    progress(1, desc="완료")
    new_meetings = get_processed_meetings()
    return f"**{message}** 결과는 '{results_path}' 폴더에 저장되었습니다.", summary_markdown, corrected_text, gr.Dropdown(choices=[name for name, _ in new_meetings]), dict(new_meetings)

def handle_chat_message(user_question, history, collection_name):
    """챗봇 메시지를 처리하고 답변을 생성합니다. (messages 포맷)"""
    if not collection_name:
        history.append({"role": "user", "content": user_question})
        history.append({"role": "assistant", "content": "먼저 좌측 상단에서 대화할 회의록을 선택해주세요."})
        return history, ""
        
    history.append({"role": "user", "content": user_question})
    yield history, ""

    response = run_query(user_question, collection_name)
    history.append({"role": "assistant", "content": response})
    yield history, ""

# --- Q&A 탭 콜백 함수 ---

# 화자별 아이콘 리스트 (이모지)
SPEAKER_ICONS = ["😀", "😎", "😊", "🧑", "👩", "🤔", "🤓", "🤖"]

def load_meeting_data(selection, state):
    """드롭다운에서 회의록 선택 시 요약과 대화록을 로드합니다."""
    if not selection:
        return gr.update(value=None), gr.update(value=None), None

    # 1. 파일 경로 찾기
    base_filename = '_'.join(selection.split('_')[:-1])
    results_folder_path = os.path.join(RESULTS_DIR, selection)
    summary_path = os.path.join(results_folder_path, f"summary_{base_filename}.md")
    corrected_path = os.path.join(results_folder_path, f"corrected_{base_filename}.txt")

    # 2. 요약 파일 읽고 마크다운으로 변환
    summary_markdown = "요약 파일을 찾을 수 없습니다."
    try:
        with open(summary_path, 'r', encoding='utf-8') as f:
            summary_json_str = f.read()
            summary_markdown = format_summary_json_to_markdown(summary_json_str)
    except FileNotFoundError:
        logging.warning(f"요약 파일 없음: {summary_path}")
    except Exception as e:
        logging.error(f"요약 파일 읽기 오류: {e}")

    # 3. 대화록 파일 읽고 파싱하기 (chat.png UI 처럼)
    transcript_chat_history = []
    speaker_icon_map = {}
    icon_index = 0
    try:
        with open(corrected_path, 'r', encoding='utf-8') as f:
            full_text = f.read() # 파일 전체를 하나의 문자열로 읽기
        
        lines = full_text.split('\n') # 문자열을 줄바꿈 기준으로 나누어 리스트 생성

        for line in lines:
            if not line.strip(): # 빈 줄은 건너뛰기
                continue

            match = re.search(r'\\[.*?s - .*?s\\]\s*(.*?):\s*(.*)', line)
            if match:
                speaker, text = match.groups()
                speaker = speaker.strip()
                
                # 새로운 화자일 경우, 아이콘 리스트에서 아이콘 할당
                if speaker not in speaker_icon_map:
                    speaker_icon_map[speaker] = SPEAKER_ICONS[icon_index % len(SPEAKER_ICONS)]
                    icon_index += 1
                
                icon = speaker_icon_map[speaker]
                
                # 아이콘, 화자 이름, 대화 내용을 포함하는 왼쪽 정렬 말풍선 생성
                chat_message = f"{icon} **{speaker}**\n{text.strip()}"
                transcript_chat_history.append((chat_message, None))
            else:
                transcript_chat_history.append((line.strip(), None))
    except FileNotFoundError:
        logging.warning(f"대화록 파일 없음: {corrected_path}")
        transcript_chat_history = [("대화록 파일을 찾을 수 없습니다.", None)]
    except Exception as e:
        logging.error(f"대화록 파일 읽기 오류: {e}")
        transcript_chat_history = [("대화록 파일 로딩 중 오류 발생: " + str(e), None)]

    # 4. Collection 이름 가져오기
    collection_name = state.get(selection)

    return summary_markdown, transcript_chat_history, collection_name

def refresh_chatbot_dropdown():
    new_meetings = get_processed_meetings()
    return gr.Dropdown(choices=[name for name, _ in new_meetings]), dict(new_meetings)
