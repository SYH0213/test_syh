"""
[ai-seong-han-juni]
이 파일은 '텍스트 교정 담당자'의 역할을 합니다.
음성인식으로 만들어진 회의록 원본은 오타가 있거나 문장이 어색할 수 있어요.
이 담당자는 회의록을 읽어서, 어떤 AI 모델(GPT 또는 Gemini)을 사용할지 확인한 다음,
AI에게 "이 문장들을 자연스럽게 다듬어줘!"라고 요청하는 일을 합니다.
"""
# -*- coding: utf-8 -*-
import logging

# 우리가 만든 '플러그'와 '명령서'를 가져옵니다.
from .llm_clients import get_openai_client, get_gemini_chain
from .prompts import GEMINI_CORRECTION_PROMPT_V2


def _correct_with_gpt(client, text, topic, keywords):
    """(내부용) GPT-4o를 사용하여 텍스트를 교정합니다."""
    # 원본 코드에서는 이 프롬프트들이 정의되지 않은 채 사용되고 있었습니다.
    # 원본의 의도를 살려, 아래와 같이 시스템/사용자 프롬프트를 구성합니다.
    system_prompt = "당신은 회의록을 자연스러운 한국어 문장으로 교정하는 전문가입니다."
    user_prompt = f"""다음 텍스트는 '{topic}'에 대한 회의 내용입니다. 
주요 키워드는 {keywords} 입니다. 
문맥에 맞게 문장을 다듬고, 맞춤법 및 띄어쓰기를 수정해주세요. 
특히, 키워드가 포함된 문장은 더 자연스럽게 만들어주세요.

원본 텍스트:
{text}

교정된 텍스트:
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.5,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"GPT-4o 교정 중 오류 발생: {e}")
        return text # 오류 발생 시 원본 텍스트 반환

def _correct_with_gemini(text, topic, keywords):
    """(내부용) Gemini를 사용하여 텍스트를 교정합니다."""
    # Gemini는 Langchain 체인을 사용합니다.
    chain = get_gemini_chain(GEMINI_CORRECTION_PROMPT_V2, ["text", "topic", "keywords"])
    if not chain: return text
    try:
        return chain.run(text=text, topic=topic, keywords=", ".join(keywords))
    except Exception as e:
        logging.error(f"Gemini 교정 중 오류 발생: {e}")
        return text # 오류 발생 시 원본 텍스트 반환

def correct_text(llm_choice, text, topic, keywords):
    """선택된 LLM을 사용하여 텍스트를 교정합니다."""
    logging.info(f"LLM({llm_choice})으로 텍스트 교정을 시작합니다...")
    if llm_choice == "gpt-4o":
        client = get_openai_client()
        if not client: return text
        return _correct_with_gpt(client, text, topic, keywords)
    elif llm_choice == "gemini-2.5-pro":
        return _correct_with_gemini(text, topic, keywords)
    else:
        logging.warning(f"지원하지 않는 LLM({llm_choice})입니다. 원본 텍스트를 반환합니다.")
        return text
