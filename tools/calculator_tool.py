from datetime import datetime

from langchain.tools import tool


@tool
def get_current_datetime() -> str:
    """
    현재 날짜와 시간을 'YYYY-MM-DD HH:MM:SS' 형식의 문자열로 반환.

    Returns:
        str: 현재 날짜와 시간.
    """
    now = datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S")


@tool
def calculate_expression(expression: str) -> float:
    """
    주어진 수학 표현식을 계산하여 결과를 반환.

    Args:
        expression (str): 계산할 수학 표현식.
    Returns:
        float: 계산 결과.
    """
    try:
        result = 0
        for s in expression:
            if s not in "0123456789+-*/(). ":
                return "유효하지 않은 문자 포함"
        result = eval(expression)
        return result
    except Exception as e:
        return f"계산 중 오류 발생: {e}"