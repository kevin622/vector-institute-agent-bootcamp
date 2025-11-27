from langchain.agents import create_agent
from langchain.tools import tool
from langchain_openai import ChatOpenAI

from tools.db_tool import (
    get_tables_from_db,
    get_column_info_from_table,
    filter_data_by_numeric_condition,
)

# Pre-defined values
## prompt
SYSTEM_PROMPT = """
    당신은 회사 데이터베이스에 접근할 수 있는 에이전트입니다.
    사용자가 요청한 정보를 제공하기 위해 적절한 도구를 사용하세요.
    도구들을 이용해 답할 수 없는 경우에는 그 이유를 설명하고, 대신 할 수 있는 것들을 응답하세요.
    유용하고 정확한 답변을 제공하세요.
""".strip()
## tools
TOOLS = [
    get_tables_from_db,
    get_column_info_from_table,
    filter_data_by_numeric_condition,
]
TOOLS_DESCRIPTION = "\n".join([f"- {tool.name}: {tool.description}" for tool in TOOLS])
## agent
AGENT_DESCRIPTION = f"""
회사 데이터베이스에 접근할 수 있는 SQL 에이전트를 호출하여 응답을 반환.
사용자가 요청한 정보를 제공하기 위해 적절한 도구를 사용하세요.
도구들을 이용해 답할 수 없는 경우에는 그 이유를 설명하고, 대신 할 수 있는 것들을 응답하세요.
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
def call_sql_agent(input_text: str) -> dict:
    """
    Args:
        input_text (str): 사용자 입력 텍스트.
    Returns:
        dict: 에이전트의 응답.
    """
    response = agent.invoke({"messages": [{"role": "user", "content": input_text}]})
    return response["messages"][-1].text
