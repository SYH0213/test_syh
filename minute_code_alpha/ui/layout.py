"""
[ai-seong-han-juni]
이 파일은 UI 팀의 '인테리어 디자이너' 역할을 합니다.
사용자에게 보여지는 화면의 전체적인 디자인과 배치를 담당하죠.
어떤 버튼이 어디에 놓이고, 어떤 글씨가 어떤 크기로 보일지 등
화면의 모든 요소를 보기 좋게 배치하는 일을 합니다.
그리고 각 버튼이나 입력창이 어떤 '안내 데스크 직원(callbacks.py)'과 연결되어야 하는지 알려줍니다.
"""
# -*- coding: utf-8 -*-
import gradio as gr
import os

# 우리가 만든 모듈들을 가져옵니다.
from .callbacks import (
    create_zoom_link,
    get_processed_meetings,
    upload_wrapper,
    save_recording_wrapper,
    run_processing_and_update_ui,
    handle_chat_message,
    load_meeting_data,
    refresh_chatbot_dropdown
)
from .handlers import (
    get_audio_files_for_df,
    get_audio_files_for_dropdown
)
from ..settings import (
    DATA_DIR,
    RESULTS_DIR,
    AVAILABLE_LLMS,
    DEFAULT_MEETING_TOPIC,
    DEFAULT_KEYWORDS
)

# --- 기본 설정 ---
# 프로젝트의 중요한 폴더 위치를 설정합니다.
# 이제 모든 경로는 settings.py에서 관리합니다.

def create_ui():
    """Gradio UI를 생성하고 반환합니다."""
    with gr.Blocks(theme=gr.themes.Soft(), title="AI 회의록 정리") as demo:
        gr.Markdown("<h1><center>Minute Factory: AI 회의록 정리</center></h1>")

        with gr.Tabs():
            with gr.TabItem("음성 파일 관리"):
                gr.Markdown("음성/영상 파일을 업로드하거나 서버의 파일을 관리합니다. (mp4, m4a 등은 wav로 자동 변환)")
                with gr.Row():
                    audio_list_df = gr.Dataframe(
                        headers=["파일명", "크기", "수정일"],
                        value=get_audio_files_for_df(DATA_DIR),
                        interactive=False
                    )
                with gr.Row():
                    with gr.Column():
                        file_uploader = gr.File(label="음성/영상 파일 업로드 (WAV 자동 변환)")
                        upload_status = gr.Markdown("")
                
            with gr.TabItem("음성 녹음"):
                gr.Markdown("마이크를 사용하여 새 음성을 녹음하고 서버에 저장합니다.")
                record_status = gr.Markdown("")
                mic_audio = gr.Audio(sources=["microphone"], type="filepath", label="음성 녹음")
                save_filename_box = gr.Textbox(label="저장할 파일명 (확장자 제외)", placeholder="예: 주간회의_240927")
                save_button = gr.Button("녹음 저장하기")

            with gr.TabItem("Zoom 회의"):
                gr.Markdown("## Zoom 회의 참여 및 녹화 안내")
                gr.Markdown(
                    "**회의 참여:** 아래에 Zoom 회의 링크를 입력하면 참여할 수 있는 링크가 생성됩니다.\n"
                    "**회의 녹화:** 이 앱은 Zoom 회의를 직접 녹화할 수 없습니다. 대신, Zoom의 자체 녹화 기능을 사용하세요."
                )
                with gr.Row():
                    zoom_url_input = gr.Textbox(label="Zoom 회의 링크", placeholder="https://zoom.us/j/1234567890")
                zoom_link_output = gr.Markdown("")
                gr.Markdown(
                    "### 녹화 파일을 업로드하는 방법\n"
                    "1. Zoom 회의 중 '기록' (Record) 버튼을 눌러 **'이 컴퓨터에 기록'**을 선택합니다.\n"
                    "2. 회의가 끝나면 녹화 파일이 동영상(.mp4) 또는 오디오(.m4a) 파일로 컴퓨터에 저장됩니다.\n"
                    "3. **'1. 파일 업로드 및 관리'** 탭으로 이동하여 저장된 파일을 업로드하세요.\n"
                    "4. 업로드된 파일은 자동으로 음성(.wav) 파일로 변환되어 목록에 추가됩니다."
                )

            with gr.TabItem("처리 & 요약"):
                gr.Markdown("오디오 파일을 선택하고 처리 및 요약을 실행합니다.")
                with gr.Row():
                    audio_dropdown = gr.Dropdown(label="처리할 오디오 파일", choices=get_audio_files_for_dropdown(DATA_DIR), allow_custom_value=True)
                    refresh_button = gr.Button("파일 목록 새로고침")
                
                gr.Markdown("회의 정보를 입력하세요.")
                with gr.Row():
                    topic_input = gr.Textbox(label="회의 주제", value=DEFAULT_MEETING_TOPIC)
                    keywords_input = gr.Textbox(label="주요 키워드 (쉼표로 구분)", value=", ".join(DEFAULT_KEYWORDS))
                
                llm_dropdown = gr.Radio(label="사용할 LLM", choices=AVAILABLE_LLMS, value=AVAILABLE_LLMS[0])
                
                start_button = gr.Button("처리 시작", variant="primary")
                process_status = gr.Markdown("")

                with gr.Accordion("처리 결과 보기", open=True):
                    summary_output = gr.Markdown(label="회의 요약")
                    corrected_output = gr.Textbox(label="교정된 대화록", lines=15, interactive=False)

            with gr.TabItem("회의록 검색 Q&A"):
                with gr.Column():
                    with gr.Row():
                        chatbot_meeting_selector = gr.Dropdown(
                            label="대화할 회의록 선택", 
                            choices=[name for name, _ in get_processed_meetings()],
                            value=None
                        )
                        chatbot_refresh_button = gr.Button("회의록 목록 새로고침")
                    
                    with gr.Tabs():
                        with gr.TabItem("📜 대화록"):
                            transcript_output = gr.Chatbot(label="전체 대화 내용", height=500)
                        with gr.TabItem("📝 요약"):
                            summary_output_qa = gr.Markdown(label="회의 요약 내용")
                        with gr.TabItem("❓ 질문하기"):
                            chatbot_history = gr.Chatbot(label="대화 내용", height=500, type="messages")
                            chatbot_question = gr.Textbox(label="질문 입력", placeholder="회의록 내용을 기반으로 질문을 입력하세요...")
                            chatbot_submit_button = gr.Button("전송", variant="primary")

                available_meetings_state = gr.State(dict(get_processed_meetings()))
                selected_collection_state = gr.State()

        # --- 이벤트 핸들러 연결 ---
        
        file_uploader.upload(
            fn=upload_wrapper,
            inputs=[file_uploader],
            outputs=[upload_status, audio_list_df, audio_dropdown]
        )

        save_button.click(
            fn=save_recording_wrapper,
            inputs=[mic_audio, save_filename_box],
            outputs=[record_status, audio_list_df, audio_dropdown]
        )

        zoom_url_input.change(
            fn=create_zoom_link,
            inputs=[zoom_url_input],
            outputs=[zoom_link_output]
        )

        refresh_button.click(fn=lambda: refresh_audio_dropdown(DATA_DIR), outputs=[audio_dropdown])

        # Q&A 탭 이벤트 핸들러
        chatbot_refresh_button.click(
            fn=refresh_chatbot_dropdown,
            outputs=[chatbot_meeting_selector, available_meetings_state]
        )
        
        # 처리 & 요약 탭에서 처리가 완료되면 Q&A 탭의 드롭다운과 상태를 함께 업데이트
        start_button.click(
            fn=run_processing_and_update_ui,
            inputs=[audio_dropdown, llm_dropdown, topic_input, keywords_input],
            outputs=[process_status, summary_output, corrected_output, chatbot_meeting_selector, available_meetings_state]
        )

        # 회의록 선택 시 데이터 로드
        chatbot_meeting_selector.change(
            fn=load_meeting_data,
            inputs=[chatbot_meeting_selector, available_meetings_state],
            outputs=[summary_output_qa, transcript_output, selected_collection_state]
        )

        # 챗봇 질문/답변
        chatbot_submit_button.click(
            fn=handle_chat_message,
            inputs=[chatbot_question, chatbot_history, selected_collection_state],
            outputs=[chatbot_history, chatbot_question]
        )
        chatbot_question.submit(
            fn=handle_chat_message,
            inputs=[chatbot_question, chatbot_history, selected_collection_state],
            outputs=[chatbot_history, chatbot_question]
        )
        
    return demo
