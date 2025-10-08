"""
[ai-seong-han-juni]
이 파일은 '회의록 요약 담당자'의 역할을 합니다.
이 담당자는 길고 복잡한 회의록 전체를 받아서, 어떤 AI 모델(GPT 또는 Gemini)을 쓸지 확인하고,
AI에게 "이 회의 내용을 핵심만 뽑아서 보기 좋게 정리해줘!" 라고 요청하는 일을 합니다.
결과물은 보통 JSON이라는 구조화된 형식으로 나와서, 나중에 웹사이트에 보여주기 좋습니다.
"""
# -*- coding: utf-8 -*-
import logging
import re

# 우리가 만든 '플러그'와 '명령서'를 가져옵니다.
from .llm_clients import get_openai_client, get_gemini_chain
from .prompts import (
    MEETING_SUMMARY_SYSTEM_PROMPT,
    MEETING_SUMMARY_USER_PROMPT,
    GEMINI_SUMMARY_PROMPT_TEMPLATE
)

def _summarize_with_gpt(client, text, topic, keywords):
    """(내부용) GPT-4o를 사용하여 텍스트를 JSON 형식으로 요약합니다."""
    logging.info("GPT-4o를 사용하여 JSON 요약을 시작합니다.")
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"}, # 응답을 JSON 형식으로 받도록 요청
            messages=[
                {"role": "system", "content": MEETING_SUMMARY_SYSTEM_PROMPT},
                {"role": "user", "content": MEETING_SUMMARY_USER_PROMPT.format(
                    topic=topic, 
                    keywords=', '.join(keywords), 
                    text=text
                )}
            ],
            temperature=0.5,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"GPT-4o JSON 요약 중 오류 발생: {e}")
        return "{\"error\": \"GPT-4o 요약 생성에 실패했습니다.\"}"

def _summarize_with_gemini(text, topic, keywords):
    """(내부용) Gemini를 사용하여 텍스트를 JSON 형식으로 요약합니다."""
    logging.info("Gemini 2.5 Pro를 사용하여 JSON 요약을 시작합니다.")
    chain = get_gemini_chain(GEMINI_SUMMARY_PROMPT_TEMPLATE, ["text", "topic", "keywords"])
    if not chain: 
        return "{\"error\": \"Gemini 체인 생성에 실패했습니다.\"}"
    try:
        result = chain.run(text=text, topic=topic, keywords=", ".join(keywords))
        # LLM 응답에서 JSON 코드 블록(```json ... ```)을 정리하고 순수한 JSON만 추출
        match = re.search(r'```json\n(.*?)\n```', result, re.DOTALL)
        if match:
            return match.group(1).strip()
        return result.strip()
    except Exception as e:
        logging.error(f"Gemini JSON 요약 중 오류 발생: {e}")
        return "{\"error\": \"Gemini 요약 생성에 실패했습니다.\"}"

def summarize_text(llm_choice, text, topic, keywords):
    """선택된 LLM을 사용하여 텍스트를 요약합니다."""
    logging.info(f"LLM({llm_choice})으로 텍스트 요약을 시작합니다...")
    if llm_choice == "gpt-4o":
        client = get_openai_client()
        if not client: return "{\"error\": \"OpenAI 클라이언트 초기화 실패\"}"
        return _summarize_with_gpt(client, text, topic, keywords)
    elif llm_choice == "gemini-2.5-pro":
        return _summarize_with_gemini(text, topic, keywords)
    else:
        logging.warning(f"지원하지 않는 LLM 모델({llm_choice})입니다. 요약을 건너<0xEB><0x9B><0x81>니다.")
        return "{\"error\": \"지원하지 않는 모델입니다.\"}"

