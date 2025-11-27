from dotenv import load_dotenv
from langfuse.langchain import CallbackHandler

load_dotenv()

from agents import master_agent

langfuse_handler = CallbackHandler()

if __name__ == "__main__":
    query = "DB에서 예산이 1만 이하인 프로젝트들의 예산 합을 알려줘."
    for chunk in master_agent.stream(
        {"messages": [{"role": "user", "content": query}]},
        config={"callbacks": [langfuse_handler]},
    ):
        for update in chunk.values():
            for message in update.get("messages", []):
                message.pretty_print()
