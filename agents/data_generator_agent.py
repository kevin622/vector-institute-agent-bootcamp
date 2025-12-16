from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

from agents.sql_agent import call_sql_agent
from agents.web_agent import call_web_agent
from agents.calculator_agent import call_calculator_agent

SYSTEM_PROMPT = """
당신은 다른 AI 에이전트를 평가하는 데이터를 생성하는 역할을 수행하는 AI 에이전트입니다. 
당신이 사용하는 도구들은 평가하려는 AI 에이전트가 사용하는 도구들과 동일합니다. 
주어진 지침에 따라 데이터를 생성하세요.

지침:
1. 주어진 도구를 한 번만 사용하는 질문과 대답을 생성하세요.
2. 질문은 도구의 기능을 충분히 활용할 수 있도록 구체적이고 명확하게 작성하세요.
3. 생성된 질문에 대한 올바른 대답(실제 정답)도 함께 제공하세요.
4. 질문과 대답은 현실적이고 실행 가능한 내용이어야 합니다.
""".strip()

agent = create_agent(
    model=ChatOpenAI(model="gemini-2.5-pro"),
    tools=[call_sql_agent, call_web_agent, call_calculator_agent],
    system_prompt=SYSTEM_PROMPT,
)
