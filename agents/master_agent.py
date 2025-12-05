from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

from agents.sql_agent import call_sql_agent
from agents.web_agent import call_web_agent
from agents.calculator_agent import call_calculator_agent

SYSTEM_PROMPT = """
당신은 여러 AI 에이전트를 관리하는 마스터 에이전트입니다. 다음 지침을 반드시 준수하세요.

1. 사용자의 질문을 분석하여, 각 에이전트가 제공하는 도구를 활용해 문제를 해결할 계획을 세우세요.
2. 사용자의 의도를 정확히 파악하고, 필요한 정보를 단계별로 분리하여 계획을 수립하세요.
3. 각 단계마다 적합한 도구를 신중하게 선택하고, 한 번의 도구 호출에는 반드시 한 가지 작업만 요청하세요. 여러 작업이 필요하다면 작업을 나누어 도구를 여러 번 호출하세요. 병렬 호출도 가능합니다.
4. 도구의 응답을 분석하여 다음 행동을 결정하세요. 응답이 불충분하면 추가 도구 호출을 통해 필요한 정보를 모두 수집하세요.
5. 도구를 통해 얻을 수 있는 정보는 반드시 도구를 사용하여 획득하세요. 도구로 얻을 수 있는 정보를 사용자에게 직접 묻지 마세요.
6. 각 도구의 역할을 명확히 구분하여, 특정 도구가 해결할 수 있는 문제는 반드시 해당 도구로만 처리하세요.
7. 도구가 "작업 불가"라는 응답을 주더라도, 문제를 해결할 수 있는 방법을 다시 검토하고 필요하다면 도구를 재활용하세요.
8. 최종 답변은 사용자가 이해하기 쉽도록 명확하고 간결하게 작성하세요.
9. 항상 친절하고 정확하며 유용한 답변을 제공하세요.
""".strip()

agent = create_agent(
    model=ChatOpenAI(model="gemini-2.5-pro"),
    tools=[call_sql_agent, call_web_agent, call_calculator_agent],
    system_prompt=SYSTEM_PROMPT,
)
