from langchain.agents import create_agent
from langchain.tools import tool
from langchain_openai import ChatOpenAI

from .tools.db_tool import (
    get_tables_from_db,
    get_column_info_from_table,
    filter_data_by_numeric_condition,
)

agent = create_agent(
    model=ChatOpenAI(model="gemini-2.5-flash"),
    tools=[
        get_tables_from_db,
        get_column_info_from_table,
        filter_data_by_numeric_condition,
    ],
    system_prompt=(
        "당신은 회사 데이터베이스에 접근할 수 있는 에이전트입니다."
        "사용자가 요청한 정보를 제공하기 위해 적절한 도구를 사용하세요."
        "유용하고 정확한 답변을 제공하세요."
    ),
)


@tool
def call_sql_agent(input_text: str) -> dict:
    """
    회사의 데이터베이스에 접근할 수 있는 SQL 에이전트를 호출하여 응답을 반환.

    Args:
        input_text (str): 사용자 입력 텍스트.
    Returns:
        dict: 에이전트의 응답.
    """
    response = agent.invoke({"messages": [{"role": "user", "content": input_text}]})
    return response["messages"][-1].text
