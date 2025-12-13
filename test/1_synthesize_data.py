from datetime import datetime
import json
from pathlib import Path

from langfuse.langchain import CallbackHandler

from agents.data_synthesis_agent import agent, DataSynthesisResponse

TODAY_DATETIME_STR = datetime.now().strftime("%Y%m%d_%H%M%S")
SYNTHESIZED_DATA_PATH = Path(__file__).parent / "synthesized_data" / f"synthesized_queries_{TODAY_DATETIME_STR}.json"
DATA_CNT = 5
langfuse_handler = CallbackHandler()


def synthesize_data(data_cnt: int) -> DataSynthesisResponse:
    """
    Returns:
        DataSynthesisResponse: 생성된 데이터.
    """
    response = agent.invoke(
        {"messages": [{"role": "user", "content": f"지침을 확실하게 준수하여 데이터를 {data_cnt}개 생성해줘."}]},
        config={"callbacks": [langfuse_handler]},
    )
    return response


def main():
    synthesized_data = synthesize_data(DATA_CNT)
    result = synthesized_data["structured_response"].model_dump()
    result["datetime"] = TODAY_DATETIME_STR
    with open(SYNTHESIZED_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    main()
