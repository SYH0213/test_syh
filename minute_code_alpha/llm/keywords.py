"""
[ai-seong-han-juni]
이 파일은 '키워드 추출 담당자'의 역할을 합니다.
회의록 전체 내용을 받아서, 어떤 AI 모델(GPT 또는 Gemini)을 사용할지 확인한 다음,
우리가 만들어 둔 '명령서(prompts.py)'와 '플러그(llm_clients.py)'를 사용해서
AI에게 "여기서 핵심 단어만 뽑아줘!"라고 요청하는 일을 합니다.
그리고 그 결과를 깔끔하게 정리해서 돌려줍니다.
"""
# -*- coding: utf-8 -*-
import logging

# 우리가 만든 '플러그'와 '명령서'를 가져옵니다.
from .llm_clients import get_openai_client, get_gemini_chain
from .prompts import KEYWORD_EXTRACTION_PROMPT

def extract_keywords(llm_choice, text, topic):
    """선택된 LLM을 사용하여 텍스트에서 키워드를 추출합니다."""
    logging.info(f"LLM({llm_choice})으로 키워드 추출을 시작합니다...")
    
    # 프롬프트 템플릿을 사용합니다.
    prompt_text = KEYWORD_EXTRACTION_PROMPT

    if llm_choice == "gpt-4o":
        client = get_openai_client()
        if not client: return []
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "당신은 주어진 텍스트의 핵심 키워드를 추출하는 전문가입니다."},
                    {"role": "user", "content": prompt_text.format(text=text, topic=topic)}
                ],
                temperature=0.2,
            )
            keywords_str = response.choices[0].message.content.strip()
            return [k.strip() for k in keywords_str.split(',') if k.strip()]
        except Exception as e:
            logging.error(f"GPT-4o 키워드 추출 중 오류 발생: {e}")
            return []
            
    elif llm_choice == "gemini-2.5-pro":
        # Gemini는 Langchain 체인을 사용합니다.
        chain = get_gemini_chain(prompt_text, ["text", "topic"])
        if not chain: return []
        try:
            keywords_str = chain.run(text=text, topic=topic)
            return [k.strip() for k in keywords_str.split(',') if k.strip()]
        except Exception as e:
            logging.error(f"Gemini 키워드 추출 중 오류 발생: {e}")
            return []
    else:
        logging.warning(f"지원하지 않는 LLM: {llm_choice}")
        return []
