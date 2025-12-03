from pathlib import Path
import json
from datetime import datetime
import asyncio

from dotenv import load_dotenv
from langfuse.langchain import CallbackHandler
from tqdm import tqdm

load_dotenv()
from agents.evaluator_agent import aevaluate_response


langfuse_handler = CallbackHandler()

# AGENT_RESULT_FILE_NAME은 test/results 디렉토리 내에 `agent_result_YYYYMMDD_HHMMSS.jsonl` 형식의 파일명으로 저장된 파일이어야 합니다.
# 디폴트로 가장 최근 생성된 파일명을 사용하도록 설정했습니다.
AGENT_RESULT_FILE_NAME = sorted(
    [f.name for f in (Path(__file__).resolve().parent / "results").glob("agent_result_*.jsonl")],
    reverse=True,
)[0]
AGENT_RESULT_FILE = Path(__file__).resolve().parent / "results" / AGENT_RESULT_FILE_NAME
EVALUATION_RESULT_FILE = (
    Path(__file__).resolve().parent / "results" / f"evaluation_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
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
    for idx in tqdm(range(0, len(tasks), concurrency), desc="Evaluating agent responses"):
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
