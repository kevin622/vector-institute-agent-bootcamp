from pathlib import Path
import json
from datetime import datetime
import asyncio

from dotenv import load_dotenv
from langfuse.langchain import CallbackHandler

load_dotenv()

from agents.evaluator_agent import aevaluate_response


langfuse_handler = CallbackHandler()

AGENT_RESULT_FILE = Path(__file__).resolve().parent / "agent_result_20251202_144937.jsonl"
EVALUATION_RESULT_FILE = (
    Path(__file__).resolve().parent / f"evaluation_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
)


async def aget_evaluation_responses(agent_results, concurrency: int = 5):
    tasks = []
    for data in agent_results:
        title = data["title"]
        query = data["query"]
        expected_answer = data["expected_answer"]
        agent_response = data["agent_response"]

        tasks.append(
            aevaluate_response(
                question=query,
                ground_truth=expected_answer,
                proposed_response=agent_response,
            )
        )
    results = []
    for idx in range(0, len(tasks), concurrency):
        result = await asyncio.gather(*tasks[idx : idx + concurrency])
        results.extend(result)
    return results


if __name__ == "__main__":
    with open(AGENT_RESULT_FILE, "r", encoding="utf-8") as f:
        agent_results = [json.loads(line) for line in f.readlines()]

    evaluation_responses = asyncio.run(aget_evaluation_responses(agent_results))
    with open(EVALUATION_RESULT_FILE, "w", encoding="utf-8") as result_file:
        for data, eval_response in zip(agent_results, evaluation_responses):
            evaluation_record = {
                "title": data["title"],
                "query": data["query"],
                "expected_answer": data["expected_answer"],
                "agent_response": data["agent_response"],
                "evaluator_explanation": eval_response,
            }
            result_file.write(json.dumps(evaluation_record, ensure_ascii=False) + "\n")
