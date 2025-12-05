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
def calculate_math_expression(expression: str) -> float:
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


@tool
def sort_values_based_on_key(values: list, key: str) -> list:
    """
    주어진 키를 기준으로 값들을 정렬하여 반환.

    Args:
        values (list): 정렬할 값들의 리스트(딕셔너리 형태).
        key (str): 정렬 기준이 되는 키.
    Returns:
        list: 정렬된 값들의 리스트.
    """
    try:
        sorted_values = sorted(values, key=lambda x: x.get(key, 0))
        return sorted_values
    except Exception as e:
        return f"정렬 중 오류 발생: {e}"


@tool
def get_length_of_object(obj: list | dict | str) -> int:
    """
    주어진 객체의 길이를 반환.

    Args:
        obj (list | dict | str): 길이를 구할 객체.
    Returns:
        int: 객체의 길이.
    """
    try:
        length = len(obj)
        return length
    except Exception as e:
        return f"길이 계산 중 오류 발생: {e}"
