from langchain.agents import create_agent
from langchain.tools import tool
from langchain_openai import ChatOpenAI

from .tools.calculator_tool import calculate_expression, get_current_datetime

agent = create_agent(
    model=ChatOpenAI(model="gemini-2.5-flash"),
    tools=[calculate_expression, get_current_datetime],
    system_prompt=(
        "당신은 수학적 계산이나 날짜와 시간을 등을 제공할 수 있는 계산 에이전트입니다."
        "사용자가 요청한 수학 표현식을 정확하게 계산하거나 현재 날짜와 시간을 제공하세요."
        "유용하고 정확한 답변을 제공하세요."
    ),
)


@tool
def call_calculator_agent(input_text: str) -> dict:
    """
    날짜와 수학 등을 계산하는 에이전트를 호출하여 응답을 반환.

    Args:
        input_text (str): 사용자 입력 텍스트.
    Returns:
        dict: 에이전트의 응답.
    """
    response = agent.invoke({"messages": [{"role": "user", "content": input_text}]})
    return response["messages"][-1].text
