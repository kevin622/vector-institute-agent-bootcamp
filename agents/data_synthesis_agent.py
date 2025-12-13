from typing import Literal, Optional

from pydantic import BaseModel
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langfuse.langchain import CallbackHandler

from agents.master_agent import TOOLS as MASTER_AGENT_TOOLS

langfuse_handler = CallbackHandler()

DATA_CNT = 3  # 생성할 데이터 개수

SYSTEM_PROMPT = f"""
당신은 AI 에이전트를 평가하기 위한 질의 데이터를 생성하는 AI 에이전트입니다. 주어진 지침에 따라 데이터를 생성하세요.

1. 평가 대상인 AI 에이전트가 사용하는 도구들(tools)이 제공됩니다. 이 도구들을 활용헤야 답할 수 있는 질의를 만들 것입니다.
2. 최소 한 개의 도구를 선택하여, 해당 도구들을 사용한 시나리오에 대한 데이터를 생성하세요. **절대로 실제로 도구를 호출하지 마세요.**
3. 도구를 한 개만 사용하는 시나리오와 여러 개의 도구를 조합하여 사용하는 시나리오를 모두 포함하세요.
4. 현재 알 수 없는 정보들을 절대로 데이터에 포함하지 마세요. **도구를 사용해야 확인할 수 있는 정보가 질의에 포함되어서는 절대 안 됩니다.** 
   당신은 도구를 호출하지 않기 때문에, 도구를 사용해야만 알 수 있는 정보는 절대로 포함할 수 없습니다.
5. 도구를 한 개만 사용하는 시나리오는 'simple', 여러 개의 도구를 조합하여 사용하는 시나리오는 'complex'로 구분하세요.
6. 각 데이터는 다음과 같은 구조를 가져야 합니다:
    - query: 사용자가 AI 에이전트에게 묻는 질문.
    - difficulty: 'simple' 또는 'complex'로, 도구 사용의 복잡성을 나타냄. 도구를 한 개만 사용하면 'simple', 여러 개를 사용하면 'complex'.
7. complex 질의를 만들 때 다양한 도구 조합을 활용하세요. 꼭 비슷한 도구들을 반복해서 사용할 필요는 없습니다.
8. 사용자가 따로 명시하지 않았을 경우 총 {DATA_CNT}개의 데이터를 생성하세요. 사용자가 명시했을 경우 그 개수만큼 데이터를 생성하세요.
9. 각 질문은 완전히 독립적이어야 하며, 이전 질문이나 대화 내용을 참조해서는 안 됩니다. 다른 질문에서 사용된 시나리오나 정보를 재사용하지 마세요.
10. 여러 도구 중 특정 도구를 통해 확인할 수 있는 정보가 있다면 당신은 그 정보를 절대로 알 수 없습니다. 따라서 그런 정보는 절대로 질문에 포함되어서는 안 됩니다.
    예를 들어 A 도구로 확인할 수 있는 정보가 있다면, B, C 도구만을 사용하여 답할 수 있는 질의를 만든다고 해도 그 정보는 절대로 질문에 포함되어서는 안 됩니다.
11. 생성된 질의들은 이후에 여러 번 사용될 수 있으니, 일반적이고 반복 가능한 시나리오를 기반으로 만들어야 합니다. 상황이나 시간에 따라 변하지 않는, 보편적인 질문을 생성하세요.
""".strip()


class SingleToolCall(BaseModel):
    """trace 내 단일 tool call 포맷 정의"""

    name: str
    args: dict
    type: str = "tool_call"


class SingleTrace(BaseModel):
    """trace 내 단일 메시지 포맷 정의"""

    type: Literal["system", "user", "ai", "tool"]
    content: str
    tool_calls: Optional[list[SingleToolCall]] = None


class SingleDataSynthesis(BaseModel):
    """단일 생성 데이터 포맷 정의"""

    query: str
    difficulty: Literal["simple", "complex"]


class DataSynthesisResponse(BaseModel):
    """data synthesis agent의 응답 포맷 정의"""

    result: list[SingleDataSynthesis]


agent = create_agent(
    model=ChatOpenAI(model="gemini-2.5-pro"),
    tools=MASTER_AGENT_TOOLS,
    system_prompt=SYSTEM_PROMPT,
    response_format=DataSynthesisResponse,
)
