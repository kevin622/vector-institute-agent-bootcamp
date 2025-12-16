from pathlib import Path
import json
from datetime import datetime

from dotenv import load_dotenv
from langfuse.langchain import CallbackHandler

load_dotenv()
from agents import master_agent

langfuse_handler = CallbackHandler()

TODAY_DATETIME_STR = datetime.now().strftime("%Y%m%d_%H%M%S")
AGENT_RESULT_DIR = Path(__file__).resolve().parent / "agent_results_from_scratch"
TEST_DATA_DIR = max(
    AGENT_RESULT_DIR.glob("agent_result_*.jsonl"), key=lambda x: x.stat().st_mtime
)  # agent_result_%Y%m%d_%H%M%S.jsonl 형태의 파일 중 최신 파일 선택
COMPARE_RESULT_FILE = (
    Path(__file__).resolve().parent / "agent_results_to_compare" / f"agent_result_{TODAY_DATETIME_STR}.jsonl"
)

if __name__ == "__main__":
    test_data = []
    with open(TEST_DATA_DIR, "r", encoding="utf-8") as f:
        for line in f:
            test_data.append(json.loads(line))

    with open(COMPARE_RESULT_FILE, "w", encoding="utf-8") as result_file:
        for idx, data in enumerate(test_data):
            query = data["query"]
            difficulty = data["difficulty"]
            agent_response = data["agent_response"]
            trace = data["trace"]  # 기존에 저장된 trace 불러오기

            new_trace = []
            print(f"+++++++++++++++++++++++++++++++++[ Test Data: {idx} ]+++++++++++++++++++++++++++++++++")
            print(f"[QUERY] {query}")
            for chunk in master_agent.stream(
                {"messages": [{"role": "user", "content": query}]},
                config={"callbacks": [langfuse_handler]},
            ):
                for update in chunk.values():
                    for message in update.get("messages", []):
                        message.pretty_print()
                        new_trace.append(message.model_dump())
            print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
            result_file.write(
                json.dumps(
                    {
                        "query": query,
                        "agent_response": agent_response,
                        "new_agent_response": message.content,
                        "difficulty": difficulty,
                        "trace": trace,
                        "new_trace": new_trace,
                    },
                    ensure_ascii=False,
                )
                + "\n",
            )
