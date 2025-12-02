from pathlib import Path
import json
from datetime import datetime

from dotenv import load_dotenv
from langfuse.langchain import CallbackHandler

load_dotenv()

from agents import master_agent

langfuse_handler = CallbackHandler()
TEST_DATA_DIR = (Path(__file__).resolve().parent / "test" / "test_10.json")
AGENT_RESULT_FILE = Path(__file__).resolve().parent / "test" / f"agent_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"

if __name__ == "__main__":
    with open(TEST_DATA_DIR, "r", encoding="utf-8") as f:
        test_data = json.load(f)

    with open(AGENT_RESULT_FILE, "w", encoding="utf-8") as result_file:
        for data in test_data["data"]:
            title = data["title"]
            paragraph = data["paragraphs"][0]
            for qa in paragraph["qas"]:
                query = qa["question"]
                answer = qa["answers"][0]["text"]

                print(f"+++++++++++++++++++++++++++++++++[ {title} ]+++++++++++++++++++++++++++++++++")
                print(f"[QUERY] {query}")
                print(f"[EXPECTED ANSWER] {answer}")
                for chunk in master_agent.stream(
                    {"messages": [{"role": "user", "content": query}]},
                    config={"callbacks": [langfuse_handler]},
                ):
                    for update in chunk.values():
                        for message in update.get("messages", []):
                            message.pretty_print()
                print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
                result_file.write(
                    json.dumps(
                        {
                            "title": title,
                            "query": query,
                            "expected_answer": answer,
                            "agent_response": message.content,
                        },
                        ensure_ascii=False,
                    )
                    + "\n",
                )