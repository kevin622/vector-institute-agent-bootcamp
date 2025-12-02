from pydantic import BaseModel
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langfuse.langchain import CallbackHandler

langfuse_handler = CallbackHandler()


SYSTEM_PROMPT = """
당신은 AI 모델의 답변을 평가하는 역할입니다. 질문과 실제 정답, AI 모델의 답변을 바탕으로 평가해야 합니다.
AI 모델의 답변이 질문에 대한 실제 정답과 얼마나 일치하는지 평가하세요.
""".strip()

EVALUATOR_TEMPLATE = """\
# 질문

{question}

# 실제 정답

{ground_truth}

# AI 모델의 답변

{proposed_response}

""".strip()


class EvaluatorResponse(BaseModel):
    """evaluator agent의 응답 포맷 정의"""

    explanation: str
    is_answer_correct: bool


agent = create_agent(
    model=ChatOpenAI(model="gemini-2.5-flash"),
    system_prompt=SYSTEM_PROMPT,
    response_format=EvaluatorResponse,
)


async def aevaluate_response(question: str, ground_truth: str, proposed_response: str) -> str:
    """
    Args:
        question (str): 사용자 질문.
        ground_truth (str): 실제 정답.
        proposed_response (str): AI 모델의 답변.
    Returns:
        str: 평가 결과.
    """
    prompt = EVALUATOR_TEMPLATE.format(
        question=question,
        ground_truth=ground_truth,
        proposed_response=proposed_response,
    )
    response = await agent.ainvoke(
        {"messages": [{"role": "user", "content": prompt}]},
        config={"callbacks": [langfuse_handler]},
    )
    return response["structured_response"].model_dump()
    # return response["messages"][-1].text
    
