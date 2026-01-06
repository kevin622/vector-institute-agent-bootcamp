from pathlib import Path
import json
from datetime import datetime

from dotenv import load_dotenv
from langfuse.langchain import CallbackHandler

load_dotenv()
from agents import master_agent

langfuse_handler = CallbackHandler()

TODAY_DATETIME_STR = datetime.now().strftime("%Y%m%d_%H%M%S")
# TEST_DATA_DIR = Path(__file__).resolve().parent / "json" / "movie_test.json"
TEST_DATA_DIR = Path(__file__).resolve().parent / "json" / "common_sense_test.json"
AGENT_RESULT_FILE = Path(__file__).resolve().parent / "agent_results" / f"agent_result_{TODAY_DATETIME_STR}.jsonl"
if __name__ == "__main__":
    with open(TEST_DATA_DIR, "r", encoding="utf-8") as f:
        test_data = json.load(f)

    with open(AGENT_RESULT_FILE, "w", encoding="utf-8") as result_file:
        for idx, data in enumerate(test_data):
            question = data["question"]
            difficulty = data["difficulty"]
            answer = data["answer"]

            trace = []
            print(f"+++++++++++++++++++++++++++++++++[ Test Data: {idx} ]+++++++++++++++++++++++++++++++++")
            print(f"[QUESTION] {question}")
            for chunk in master_agent.stream(
                {"messages": [{"role": "user", "content": question}]},
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
                        "question": question,
                        "expected_answer": answer,
                        "agent_response": message.content,
                        "difficulty": difficulty,
                        "trace": trace,
                    },
                    ensure_ascii=False,
                )
                + "\n",
            )
