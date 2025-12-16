import asyncio
from datetime import datetime
import json
from pathlib import Path

from dotenv import load_dotenv
from langfuse.langchain import CallbackHandler
from tqdm import tqdm

load_dotenv()
from agents.evaluator_agent import aevaluate_response

langfuse_handler = CallbackHandler()

TODAY_DATETIME_STR = datetime.now().strftime("%Y%m%d_%H%M%S")
AGENT_RESULT_DIR = Path(__file__).resolve().parent / "agent_results_to_compare"
TEST_DATA_DIR = max(
    AGENT_RESULT_DIR.glob("agent_result_*.jsonl"), key=lambda x: x.stat().st_mtime
)  # agent_result_%Y%m%d_%H%M%S.jsonl 형태의 파일 중 최신 파일 선택

EVALUATION_RESULT_FILE = (
    Path(__file__).resolve().parent / "evaluation_results" / f"evaluation_result_{TODAY_DATETIME_STR}.jsonl"
)


async def aget_evaluation_responses(agent_results, concurrency: int = 5):
    tasks = []
    for data in agent_results:
        query = data["query"]
        expected_answer = data["agent_response"]
        agent_response = data["new_agent_response"]

        tasks.append(
            aevaluate_response(
                question=query,
                ground_truth=expected_answer,
                proposed_response=agent_response,
            )
        )
    results = []
    for idx in tqdm(range(0, len(tasks), concurrency), desc="Evaluating agent responses"):
        result = await asyncio.gather(*tasks[idx : idx + concurrency])
        results.extend(result)
    return results


if __name__ == "__main__":
    with open(TEST_DATA_DIR, "r", encoding="utf-8") as f:
        agent_results = [json.loads(line) for line in f.readlines()]

    evaluation_responses = asyncio.run(aget_evaluation_responses(agent_results))
    with open(EVALUATION_RESULT_FILE, "w", encoding="utf-8") as result_file:
        for data, eval_response in zip(agent_results, evaluation_responses):
            evaluation_record = {
                "query": data["query"],
                "expected_answer": data["agent_response"],
                "agent_response": data["new_agent_response"],
                "evaluator_explanation": eval_response,
            }
            result_file.write(json.dumps(evaluation_record, ensure_ascii=False) + "\n")
