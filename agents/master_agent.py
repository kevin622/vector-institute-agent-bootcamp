from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

from .sql_agent import call_sql_agent
from .web_agent import call_web_agent
from .calculator_agent import call_calculator_agent

SYSTEM_PROMPT = """
당신은 여러 에이전트를 관리하는 마스터 에이전트입니다.
사용자의 질문을 바로 답하지 말고 계획을 세워 각 에이전트가 제공하는 도구를 사용하여 사용자의 요청을 처리하세요.
사용자의 의도를 파악하고, 필요한 정보를 결정하세요.
정보가 필요한 만큼 여러 도구를 호출할 수 있습니다.
도구들은 모두 AI Agent이며, 각 도구의 응답은 사용자가 이해할 수 있는 형식으로 제공됩니다. 만약 도구의 응답이 불충분하다면 추가 도구 호출을 통해 필요한 정보를 모두 수집하세요.
유용하고 정확하고 친절한 답변을 제공하세요.
""".strip()

agent = create_agent(
    model=ChatOpenAI(model="gemini-2.5-pro"),
    tools=[call_sql_agent, call_web_agent, call_calculator_agent],
    system_prompt=SYSTEM_PROMPT,
)
