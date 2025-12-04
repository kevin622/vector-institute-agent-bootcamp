from langchain.agents import create_agent
from langchain.tools import tool
from langchain_openai import ChatOpenAI

from tools.calculator_tool import calculate_expression, get_current_datetime

# Pre-defined values
## prompt
SYSTEM_PROMPT = """
당신은 수학적 계산이나 날짜와 시간을 등을 제공할 수 있는 계산 에이전트입니다.
사용자가 요청한 수학 표현식을 정확하게 계산하거나 현재 날짜와 시간을 제공하세요.
유용하고 정확한 답변을 제공하세요.
""".strip()
## tools
TOOLS = [
    calculate_expression,
    get_current_datetime,
]
TOOLS_DESCRIPTION = "\n".join([f"- {tool.name}: {tool.description}" for tool in TOOLS])
## agent
AGENT_DESCRIPTION = f"""
날짜와 수학(덧셈, 뺄셈, 나눗셈, 곱셈 등의 사칙연산) 등을 계산하는 에이전트를 호출하여 응답을 반환.
시점/시간/날짜 관련 정보를 활용해야 하는 경우에는 반드시 본 에이전트가 사용되어야 합니다.
사용자가 요청한 수학 표현식을 정확하게 계산하거나 현재 날짜와 시간을 제공하세요.
유용하고 정확한 답변을 제공하세요.
사용 가능한 도구는 다음과 같습니다:
{TOOLS_DESCRIPTION}

Args:
    input_text (str): 사용자 입력 텍스트.
Returns:
    dict: 에이전트의 응답.
""".strip()

# 에이전트 인스턴스
agent = create_agent(
    model=ChatOpenAI(model="gemini-2.5-flash"),
    tools=TOOLS,
    system_prompt=SYSTEM_PROMPT,
)


@tool(description=AGENT_DESCRIPTION)
def call_calculator_agent(input_text: str) -> dict:
    """
    Args:
        input_text (str): 사용자 입력 텍스트.
    Returns:
        dict: 에이전트의 응답.
    """
    response = agent.invoke({"messages": [{"role": "user", "content": input_text}]})
    return response["messages"][-1].text
