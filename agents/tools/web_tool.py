import os

from serpapi import GoogleSearch
from langchain.tools import tool


SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")


@tool
def google_search(
    query: str,
    location="South Korea",
    hl="ko",
    gl="kr",
) -> dict:
    """
    구글 검색을 수행하고 결과를 반환.

    Args:
        query (str): 검색 쿼리.
        location (str): 검색 위치 (기본값: "South Korea").
        hl (str): 언어 설정 (기본값: "ko").
        gl (str): 국가 설정 (기본값: "kr").
    Returns:
        dict: 검색 결과.
    """
    params = {
        "q": query,
        "location": location,
        "hl": hl,
        "gl": gl,
        "engine": "google_light",
        "google_domain": "google.com",
        "api_key": SERPAPI_API_KEY,
    }

    search_result = GoogleSearch(params).get_dict()
    result = {}
    if "answer_box" in search_result:
        result["answer_box"] = search_result["answer_box"]
    if "organic_results" in search_result:
        result["organic_results"] = search_result["organic_results"]
    return result
