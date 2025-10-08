"""
[ai-seong-han-juni]
이 파일은 여러 종류의 AI 서비스에 연결할 수 있는 '멀티탭 플러그' 같은 거예요.
OpenAI 플러그(GPT용), Google 플러그(Gemini용)가 있어서,
우리가 필요할 때마다 원하는 AI 서비스에 딱 맞춰 코드를 연결할 수 있게 도와줍니다.
이 플러그들은 '비밀 금고(config.py)'에서 API 키를 가져와 사용합니다.
"""
# -*- coding: utf-8 -*-
import logging
from openai import OpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

# 방금 만든 '비밀 금고'에서 API 키를 가져오는 함수를 불러옵니다.
from ..config import get_api_key

def get_openai_client():
    """OpenAI 클라이언트를 생성하고 반환합니다."""
    api_key = get_api_key("OPENAI_API_KEY")
    if not api_key:
        logging.error("OPENAI_API_KEY가 .env 파일에 설정되지 않았습니다.")
        return None
    return OpenAI(api_key=api_key)

def get_gemini_chain(template_string, input_vars):
    """LangChain과 Gemini를 사용하는 LLMChain을 생성합니다."""
    api_key = get_api_key("GOOGLE_API_KEY")
    if not api_key:
        logging.error("GOOGLE_API_KEY가 .env 파일에 설정되지 않았습니다.")
        return None
    
    prompt = PromptTemplate(template=template_string, input_variables=input_vars)
    llm = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.5, google_api_key=api_key)
    return LLMChain(llm=llm, prompt=prompt)

def get_chat_openai_llm():
    """LangChain에서 사용할 ChatOpenAI 인스턴스를 생성하고 반환합니다."""
    api_key = get_api_key("OPENAI_API_KEY")
    if not api_key:
        logging.error("OPENAI_API_KEY가 .env 파일에 설정되지 않았습니다.")
        return None
    # 챗봇의 RAG 파이프라인에서는 창의성보다는 정확성이 중요하므로 temperature를 0으로 설정합니다.
    return ChatOpenAI(model="gpt-4-turbo", temperature=0, openai_api_key=api_key)

def get_openai_embeddings():
    """LangChain에서 사용할 OpenAIEmbeddings 인스턴스를 생성하고 반환합니다."""
    api_key = get_api_key("OPENAI_API_KEY")
    if not api_key:
        logging.error("OPENAI_API_KEY가 .env 파일에 설정되지 않았습니다.")
        return None
    return OpenAIEmbeddings(openai_api_key=api_key)
