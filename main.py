from dotenv import load_dotenv

load_dotenv()

from agents import master_agent


if __name__ == "__main__":
    query = "DB에서 예산이 1만 이하인 프로젝트들의 예산 합을 알려줘."
    for chunk in master_agent.stream(
        {"messages": [{"role": "user", "content": query}]},
    ):
        for update in chunk.values():
            for message in update.get("messages", []):
                message.pretty_print()
