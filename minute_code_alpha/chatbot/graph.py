"""
[ai-seong-han-juni]
이 파일은 챗봇 팀의 '팀장' 역할을 합니다.
'개별 연구원(nodes.py)'들에게 어떤 순서로 일을 시킬지 결정하고,
전체 Q&A 과정을 총괄하여 질문에 대한 최종 답변을 만들어내는 역할을 하죠.
질문이 들어오면, 이 팀장은 연구원들을 적절히 지휘해서 가장 정확한 답변을 찾아내도록 합니다.
"""
# -*- coding: utf-8 -*-
import os
import uuid
import logging

from langgraph.graph import StateGraph, END

# 우리가 만든 모듈들을 가져옵니다.
from .nodes import (
    GraphState, # 챗봇의 '정보 보따리'
    route_question, retrieve, grade_documents, generate, 
    grade_generation, decide_next_action
)
from ..config import get_api_key # API 키를 가져오기 위해 '비밀 금고'를 사용합니다.

# --- 1. RAG 그래프 정의 ---
# 챗봇 팀장이 연구원들에게 일을 시키는 '업무 흐름도'를 그립니다.

_app = None # 챗봇 앱이 한 번만 만들어지도록 저장해두는 변수

def get_crag_app():
    """LangGraph 앱을 생성하거나 이미 생성된 앱을 반환합니다."""
    global _app
    if _app is None:
        # '정보 보따리'를 가지고 일할 '업무 흐름도'를 만듭니다.
        workflow = StateGraph(GraphState)
        
        # 각 연구원들을 '업무 흐름도'에 배치합니다.
        workflow.add_node("route_question", route_question)
        workflow.add_node("retrieve", retrieve)
        workflow.add_node("grade_documents", grade_documents)
        workflow.add_node("generate", generate)
        workflow.add_node("grade_generation", grade_generation)
        workflow.add_node("decide_next_action", decide_next_action)

        # 첫 번째 업무는 '질문 분석'입니다.
        workflow.set_entry_point("route_question")
        # 각 업무의 순서를 정해줍니다.
        workflow.add_edge("route_question", "retrieve")
        workflow.add_edge("retrieve", "grade_documents")
        workflow.add_edge("grade_documents", "generate")
        workflow.add_edge("generate", "grade_generation")
        workflow.add_edge("grade_generation", "decide_next_action")
        
        # '다음 행동 결정' 업무 후에, 다시 자료를 찾아야 할지(retrieve) 아니면 끝낼지(END) 결정합니다.
        workflow.add_conditional_edges(
            "decide_next_action",
            # 이 함수가 'retrieve'를 반환하면 retrieve 노드로, 'END'를 반환하면 끝냅니다.
            lambda state: "retrieve" if state.get("final_answer") is None else END,
            {"retrieve": "retrieve", END: END}
        )
        
        # 모든 업무 흐름도를 완성하고 챗봇 앱을 만듭니다.
        _app = workflow.compile()
    return _app

def run_query(question: str, collection_name: str):
    """
    챗봇에게 질문을 하고 답변을 받아옵니다.
    
    Args:
        question (str): 사용자 질문.
        collection_name (str): 검색할 ChromaDB 컬렉션 이름.

    Returns:
        str: 챗봇의 최종 답변.
    """
    # OpenAI API 키가 없으면 오류 메시지를 반환합니다.
    if not get_api_key("OPENAI_API_KEY"):
        return "오류: OPENAI_API_KEY가 .env 파일에 설정되어야 합니다."
    
    try:
        app = get_crag_app() # 챗봇 앱을 가져옵니다.
        config = {"configurable": {"thread_id": str(uuid.uuid4())}} # 챗봇의 대화 기록을 위한 설정
        # 챗봇에게 넘겨줄 초기 정보 보따리
        inputs = {"question": question, "base_collection_name": collection_name, "final_answer": None}
        
        last_output = None
        # 챗봇 앱을 실행하고, 각 단계의 결과를 실시간으로 받습니다.
        for output in app.stream(inputs, config=config):
            last_output = output
        
        if last_output:
            # 마지막 단계의 결과에서 최종 답변을 찾아 반환합니다.
            final_state = list(last_output.values())[0]
            if final_state and final_state.get('final_answer'):
                return final_state['final_answer']

        logging.warning(f"RAG 파이프라인이 최종 답변을 생성하지 못했습니다. Last output: {last_output}")
        return "답변을 생성하지 못했습니다."
            
    except Exception as e:
        logging.error(f"RAG 파이프라인 실행 중 오류 발생: {e}", exc_info=True)
        return f"챗봇 응답 생성 중 오류가 발생했습니다: {e}"
