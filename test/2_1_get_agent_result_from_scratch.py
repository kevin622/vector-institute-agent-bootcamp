from pathlib import Path
import json
from datetime import datetime

from dotenv import load_dotenv
from langfuse.langchain import CallbackHandler

load_dotenv()
from agents import master_agent

langfuse_handler = CallbackHandler()

TODAY_DATETIME_STR = datetime.now().strftime("%Y%m%d_%H%M%S")
SYNTHESIZED_QUERIES_DIR = Path(__file__).resolve().parent / "synthesized_data"
TEST_DATA_DIR = max(
    SYNTHESIZED_QUERIES_DIR.glob("synthesized_queries_*.json"), key=lambda x: x.stat().st_mtime
)  # synthesized_queries_%Y%m%d_%H%M%S.jsonl 형태의 파일 중 최신 파일 선택
AGENT_RESULT_FILE = (
    Path(__file__).resolve().parent / "agent_results_from_scratch" / f"agent_result_{TODAY_DATETIME_STR}.jsonl"
)

if __name__ == "__main__":
    with open(TEST_DATA_DIR, "r", encoding="utf-8") as f:
        test_data = json.load(f)

    with open(AGENT_RESULT_FILE, "w", encoding="utf-8") as result_file:
        for idx, data in enumerate(test_data["result"]):
            query = data["query"]
            difficulty = data["difficulty"]
            trace = []

            print(f"+++++++++++++++++++++++++++++++++[ Test Data: {idx} ]+++++++++++++++++++++++++++++++++")
            print(f"[QUERY] {query}")
            for chunk in master_agent.stream(
                {"messages": [{"role": "user", "content": query}]},
                config={"callbacks": [langfuse_handler]},
            ):
                for update in chunk.values():
                    for message in update.get("messages", []):
                        message.pretty_print()
                        trace.append(message.model_dump())
            print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
            result_file.write(
                json.dumps(
                    {
                        "query": query,
                        "agent_response": message.content,
                        "difficulty": difficulty,
                        "trace": trace,
                    },
                    ensure_ascii=False,
                )
                + "\n",
            )
