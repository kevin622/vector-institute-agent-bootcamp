from langchain.agents import create_agent
from langchain.tools import tool
from langchain_openai import ChatOpenAI

from tools.db_tool import (
    get_tables_from_db,
    get_column_info_from_table,
    get_top_n_data_from_table,
    filter_data_by_gte_or_lte,
    filter_data_by_inclusion,
    filter_data_by_like,
    join_tables_on_column,
    get_unique_values_of_columns,
)
from tools.util_tool import plan_recorder

# Pre-defined values
TABLES_NAMES = ", ".join(get_tables_from_db())
## prompt
SYSTEM_PROMPT = f"""
당신은 KT의 IPTV 영화 관련 데이터를 가진 데이터베이스에 접근할 수 있는 에이전트입니다.
이 데이터베이스에는 작품 제목, 감독, 출연 배우, 장르, 출시 연도, 평론 등 다양한 정보가 포함되어 있습니다.
단, 데이터가 과거의 데이터이며 최신 영화나 일부 정보가 누락될 수 있음을 유의하세요.
사용자가 요청한 정보를 제공하기 위해 적절한 도구를 사용하고 계획을 상세히 세워 응답하세요. 꼭 계획을 세워야 합니다.
본 에이전트를 호출하는 마스터 에이전트는 DB의 정보를 잘못 알고 있을 수 있습니다. 
테이블의 구조나 컬럼 정보는 자주 변경될 수 있으므로, 먼저 테이블의 컬럼 정보를 확인한 후 데이터를 조회하세요.
도구들을 이용해 답할 수 없는 경우에는 그 이유를 설명하고, 대신 할 수 있는 것들을 응답하세요.
유용하고 정확한 답변을 제공하세요.

DB에 존재하는 테이블들: {TABLES_NAMES}
""".strip()

## tools
TOOLS = [
    plan_recorder,
    get_column_info_from_table,
    get_top_n_data_from_table,
    filter_data_by_gte_or_lte,
    filter_data_by_inclusion,
    filter_data_by_like,
    join_tables_on_column,
    get_unique_values_of_columns,
]
TOOLS_DESCRIPTION = "\n\n".join([f"- {tool.name}\n: {tool.description}" for tool in TOOLS])
## agent
AGENT_DESCRIPTION = f"""
KT의 IPTV 영화 관련 데이터를 가진 데이터베이스에 접근할 수 있는 SQL 에이전트를 호출하여 응답을 반환.
이 데이터베이스에는 작품 제목, 감독, 출연 배우, 장르, 출시 연도, 평론 등 다양한 정보가 포함되어 있습니다.
이 데이터베이스에 있는 정보는 확실한 정보로써, 다른 출처의 정보보다 우선시 됩니다.
단, 데이터가 과거의 데이터이며 최신 영화나 일부 정보가 누락될 수 있음을 유의하세요.
테이블의 이름, 구조나 컬럼 정보는 자주 변경될 수 있으므로, 먼저 테이블과 컬럼 정보를 확인한 후 데이터를 조회하세요.
본 에이전트를 호출하는 마스터 에이전트는 DB의 정보를 잘못 알고 있을 수 있습니다. 
사용자가 요청한 정보를 제공하기 위해 적절한 도구를 사용하세요.
도구들을 이용해 답할 수 없는 경우에는 그 이유를 설명하고, 대신 할 수 있는 것들을 응답하세요.
유용하고 정확한 답변을 제공하세요.
사용 가능한 도구는 다음과 같습니다:
{TOOLS_DESCRIPTION}

DB에 존재하는 테이블들: {TABLES_NAMES}

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
