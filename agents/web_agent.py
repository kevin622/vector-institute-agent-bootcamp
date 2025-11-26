from langchain.agents import create_agent
from langchain.tools import tool
from langchain_openai import ChatOpenAI

from .tools.web_tool import google_search

SYSTEM_PROMPT = """
당신은 웹에 접근할 수 있는 에이전트입니다.
사용자가 요청한 정보를 제공하기 위해 적절한 도구를 사용하세요.
많은 검색 정보 중 필요한 정보를 잘 추출하여 유용하고 정확한 답변을 제공하세요.
""".strip()

agent = create_agent(
    model=ChatOpenAI(model="gemini-2.5-flash"),
    tools=[google_search],
    system_prompt=SYSTEM_PROMPT,
)


@tool
def call_web_agent(input_text: str) -> dict:
    """
    웹(인터넷)을 검색하는 에이전트를 호출하여 응답을 반환.

    Args:
        input_text (str): 사용자 입력 텍스트.
    Returns:
        dict: 에이전트의 응답.
    """
    response = agent.invoke({"messages": [{"role": "user", "content": input_text}]})
    return response["messages"][-1].text
