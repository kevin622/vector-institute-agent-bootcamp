from langchain.tools import tool


@tool
def plan_recorder(plan: str):
    """
    작업을 시작하기 전, 구체적인 실행 계획을 기록하는 도구입니다.
    반드시 가장 먼저 이 도구를 호출하여 계획을 세우세요.
    """
    return "계획이 기록되었습니다. 이제 다음 단계를 진행하세요."
