"""
[ai-seong-han-juni]
이 파일은 챗봇의 '지식 창고 관리자' 역할을 합니다.
챗봇이 질문에 답하려면 회의록 내용을 잘 알고 있어야겠죠?
이 담당자는 회의록 내용을 잘게 쪼개서 '벡터'라는 특별한 형태로 저장해두고,
질문이 들어오면 그 질문과 가장 비슷한 내용의 지식을 '지식 창고(ChromaDB)'에서 빠르게 찾아주는 일을 합니다.
"""
# -*- coding: utf-8 -*-
import os
import logging

from langchain_community.document_loaders import TextLoader
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 우리가 만든 '플러그'에서 임베딩 모델을 가져옵니다.
from ..llm.llm_clients import get_openai_embeddings
# '규칙집'에서 지식 창고가 저장될 위치를 가져옵니다.
from ..settings import CHROMA_PERSIST_DIR

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_chroma_retriever(collection_name: str):
    """
    지정된 컬렉션 이름으로 ChromaDB 리트리버를 가져옵니다.
    """
    embeddings = get_openai_embeddings()
    if not embeddings:
        logging.error("임베딩 모델 초기화 실패.")
        return None

    vectorstore = Chroma(
        collection_name=collection_name,
        persist_directory=CHROMA_PERSIST_DIR,
        embedding_function=embeddings,
    )
    return vectorstore.as_retriever()

def update_vector_store(file_path: str, collection_name: str):
    """
    파일 내용을 읽어 벡터 저장소를 업데이트합니다.
    """
    if not os.path.exists(file_path):
        logging.error(f"오류: 파일을 찾을 수 없습니다: {file_path}")
        return

    embeddings = get_openai_embeddings()
    if not embeddings:
        logging.error("임베딩 모델 초기화 실패. 벡터 저장소를 업데이트할 수 없습니다.")
        return

    loader = TextLoader(file_path, encoding='utf-8')
    docs = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(docs)

    Chroma.from_documents(
        documents=splits,
        embedding=embeddings,
        collection_name=collection_name,
        persist_directory=CHROMA_PERSIST_DIR,
    )
    logging.info(f"벡터 저장소 업데이트 완료: {file_path} -> '{collection_name}'.")
