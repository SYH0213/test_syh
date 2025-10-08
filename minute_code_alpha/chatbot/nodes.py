"""
[ai-seong-han-juni]
이 파일은 챗봇 팀의 '개별 연구원' 역할을 하는 함수들을 모아놓은 곳입니다.
각 연구원은 질문을 분석하고, 자료를 찾고, 답변을 만들고, 답변이 정확한지 확인하는 등
챗봇이 질문에 답하기 위한 한 가지 일에만 집중합니다.
이 연구원들은 '챗봇 명령서(prompts.py)'와 '지식 창고 관리자(vector_store.py)'의 도움을 받습니다.
"""
# -*- coding: utf-8 -*-
import logging
import json
from typing import List, Any
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain.schema import Document

# 우리가 만든 모듈들을 가져옵니다.
from .prompts import (
    ROUTER_SYSTEM_PROMPT, ROUTER_PROMPT_TEMPLATE,
    CHATBOT_GRADER_SYSTEM_PROMPT, CHATBOT_GRADE_PROMPT_TEMPLATE,
    CHATBOT_RAG_SYSTEM_PROMPT, CHATBOT_RAG_PROMPT_TEMPLATE,
    GENERATION_VALIDATOR_SYSTEM_PROMPT, GENERATION_VALIDATOR_PROMPT_TEMPLATE,
    DECIDER_SYSTEM_PROMPT, DECIDER_PROMPT_TEMPLATE
)
from .vector_store import get_chroma_retriever
from ..llm.llm_clients import get_chat_openai_llm # LangChain용 ChatOpenAI LLM 가져오기

# --- 1. Pydantic 모델 (JSON 출력 형식 정의) ---
# AI가 답변을 줄 때 어떤 형식으로 줄지 미리 정해놓는 '설계도'입니다.
class RouteQuery(BaseModel):
    target_db: str = Field(description="'summary_db' 또는 'full_db'")
    confidence: float
    rationale: str

class GradeDocuments(BaseModel):
    relevant: str = Field(description="'yes' 또는 'no'")
    reason: str

class GenerationValidation(BaseModel):
    grounded: bool
    missing_evidence: List[str]
    suggested_fix: str

class FinalDecision(BaseModel):
    final_decision: str = Field(description="'accept' 또는 'reject'")
    reason: str
    next_action: str

# --- 2. 그래프 상태 (GraphState) ---
# 챗봇이 질문에 답하는 과정에서 필요한 모든 정보들을 담아두는 '정보 보따리'입니다.
class GraphState(TypedDict):
    question: str # 사용자의 질문
    generation: str # AI가 생성한 답변
    documents: List[Document] # 검색된 문서들
    base_collection_name: str # ChromaDB 컬렉션 이름
    datasource: str # 검색할 데이터베이스 (요약본 또는 원문)
    retries: int # 재시도 횟수
    final_answer: str # 최종 답변
    validation_result: Any # 답변 검증 결과

# --- 3. LLM 체인 및 파서 설정 ---
# AI에게 명령을 내리고 답변을 받아오는 '통역사'와, AI의 답변을 우리가 이해하기 쉽게 바꿔주는 '번역기'를 설정합니다.
json_parser_router = JsonOutputParser(pydantic_object=RouteQuery)
json_parser_grader = JsonOutputParser(pydantic_object=GradeDocuments)
json_parser_validator = JsonOutputParser(pydantic_object=GenerationValidation)
json_parser_decider = JsonOutputParser(pydantic_object=FinalDecision)

# --- 4. 그래프 노드 함수 (개별 연구원들의 작업) ---
# 각 함수는 '정보 보따리'를 받아서 필요한 작업을 하고, 업데이트된 '정보 보따리'를 돌려줍니다.

def route_question(state: GraphState):
    """질문을 분석하여 어떤 데이터베이스에서 정보를 찾을지 결정합니다."""
    print("---\n---[1] ANALYZE QUESTION---")
    llm = get_chat_openai_llm()
    if not llm: return {"final_answer": "LLM 초기화 실패"}

    prompt = ChatPromptTemplate.from_messages([
        ("system", ROUTER_SYSTEM_PROMPT),
        ("human", ROUTER_PROMPT_TEMPLATE)
    ])
    chain = prompt | llm | json_parser_router
    result = chain.invoke({"question": state["question"]})
    
    print(f"---DECISION: ROUTE TO {result['target_db']} (Confidence: {result['confidence']})---")
    return {"datasource": result['target_db'], "retries": 0}

def retrieve(state: GraphState):
    """결정된 데이터베이스에서 질문과 관련된 문서를 검색합니다."""
    print("---\n---[2] RETRIEVE---")
    collection_suffix = "_summary" if state["datasource"] == "summary_db" else "_full"
    final_collection_name = f"{state['base_collection_name']}{collection_suffix}"
    
    print(f"---RETRIEVING FROM: {final_collection_name}---")
    retriever = get_chroma_retriever(final_collection_name)
    if not retriever: return {"final_answer": "리트리버 초기화 실패"}
    documents = retriever.invoke(state["question"])
    return {"documents": documents}

def grade_documents(state: GraphState):
    """검색된 문서들이 질문에 답변하기에 충분히 관련 있는지 평가합니다."""
    print("---\n---[3] GRADE DOCUMENTS---")
    llm = get_chat_openai_llm()
    if not llm: return {"final_answer": "LLM 초기화 실패"}

    prompt = ChatPromptTemplate.from_messages([
        ("system", CHATBOT_GRADER_SYSTEM_PROMPT),
        ("human", CHATBOT_GRADE_PROMPT_TEMPLATE)
    ])
    chain = prompt | llm | json_parser_grader
    
    filtered_docs = []
    for d in state["documents"]:
        result = chain.invoke({"question": state["question"], "document": d.page_content})
        if result['relevant'] == "yes":
            print(f"---GRADE: DOCUMENT RELEVANT ({result['reason']})---")
            d.metadata['relevance_reason'] = result['reason'] # 메타데이터에 근거 추가
            filtered_docs.append(d)
    return {"documents": filtered_docs}

def generate(state: GraphState):
    """관련성 있는 문서들을 바탕으로 질문에 대한 답변을 생성합니다."""
    print("---\n---[4] GENERATE---")
    llm = get_chat_openai_llm()
    if not llm: return {"final_answer": "LLM 초기화 실패"}

    prompt = ChatPromptTemplate.from_messages([
        ("system", CHATBOT_RAG_SYSTEM_PROMPT),
        ("human", CHATBOT_RAG_PROMPT_TEMPLATE)
    ])
    chain = prompt | llm | StrOutputParser()
    
    # 답변 생성 시, 문서에 인덱스 부여 (D1, D2...) - 근거 문서 표시용
    context_with_indices = []
    for i, doc in enumerate(state["documents"]):
        context_with_indices.append(f"[D{i+1}]\n{doc.page_content}")
    
    generation = chain.invoke({"context": "\n\n".join(context_with_indices), "question": state["question"]})
    return {"generation": generation}

def grade_generation(state: GraphState):
    """생성된 답변이 제공된 문서 컨텍스트에 의해 충분히 뒷받침되는지 검증합니다."""
    print("---\n---[5] VALIDATE GENERATION---")
    llm = get_chat_openai_llm()
    if not llm: return {"final_answer": "LLM 초기화 실패"}

    prompt = ChatPromptTemplate.from_messages([
        ("system", GENERATION_VALIDATOR_SYSTEM_PROMPT),
        ("human", GENERATION_VALIDATOR_PROMPT_TEMPLATE)
    ])
    chain = prompt | llm | json_parser_validator
    
    context_with_indices = []
    for i, doc in enumerate(state["documents"]):
        context_with_indices.append(f"[D{i+1}]\n{doc.page_content}")

    validation_result = chain.invoke({
        "question": state["question"],
        "answer": state["generation"],
        "context": "\n\n".join(context_with_indices)
    })
    return {"validation_result": validation_result}

def decide_next_action(state: GraphState):
    """검증 결과를 바탕으로 최종 응답을 수락할지, 아니면 다음 행동을 결정할지 판단합니다."""
    print("---\n---[6] DECIDE NEXT ACTION---")
    validation_res = state.get("validation_result", {})
    
    if validation_res.get("grounded"):
        print("---DECISION: ACCEPT ANSWER---")
        return {"final_answer": state["generation"]}
    else:
        print(f"---DECISION: REJECT ANSWER (Reason: {validation_res.get('missing_evidence')})---")
        # 재시도 횟수가 1회 미만이고, 요약본에서 검색했다면 원문에서 다시 검색하도록 지시합니다.
        if state["retries"] < 1 and state["datasource"] == "summary_db":
            print("---RETRY: SWITCHING TO full_db---")
            return {"datasource": "full_db", "retries": state["retries"] + 1, "final_answer": None}
        else:
            # 더 이상 재시도할 수 없으면, 검증 실패 메시지와 함께 답변을 반환합니다.
            final_answer = f"[답변 검증 실패] {validation_res.get('suggested_fix', '근거를 찾을 수 없습니다.')}\n\n{state['generation']}"
            return {"final_answer": final_answer}
