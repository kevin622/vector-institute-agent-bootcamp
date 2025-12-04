from dotenv import load_dotenv
from langfuse.langchain import CallbackHandler
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
import streamlit as st

load_dotenv()

from agents import master_agent

langfuse_handler = CallbackHandler()


class AgentMessage:
    def __init__(self, streamed_messages: list):
        self.streamed_messages = streamed_messages
        self.type = "agent"  # default type


st.set_page_config(
    page_title="Team KT in Vector Institute Agent",
    page_icon="🤖",
    layout="wide",
)

if st.session_state.get("initialized") is None:
    st.session_state["initialized"] = True
    st.session_state["agent_chat_history"] = []
    st.session_state["all_messages"] = []

st.title("Team KT in Vector Institute Agent")

for message in st.session_state["agent_chat_history"]:
    if message.type == "agent":
        with st.chat_message("ai"):
            for streamed_message in message.streamed_messages:
                if streamed_message.content:
                    st.markdown(streamed_message.content)
                elif streamed_message.tool_calls:
                    for tool_call in streamed_message.tool_calls:
                        st.write(f"`{tool_call['name']}`")
                        st.json(tool_call["args"])
    else:
        with st.chat_message("user"):
            st.markdown(message.content)

query = st.chat_input()

if query:
    with st.chat_message("user"):
        st.markdown(query)
    st.session_state["agent_chat_history"].append(HumanMessage(content=query))
    st.session_state["all_messages"].append(HumanMessage(content=query))
    with st.chat_message("ai"):
        streamed_messages = []
        for chunk in master_agent.stream(
            {"messages": st.session_state["all_messages"]},
            config={"callbacks": [langfuse_handler]},
        ):
            for update in chunk.values():
                for message in update.get("messages", []):
                    if message.content:
                        if message.type == "ai":
                            st.markdown(message.content)
                        else:  # tool messages
                            st.caption(message.content)
                    if hasattr(message, "tool_calls"):
                        for tool_call in message.tool_calls:
                            st.write(f"`{tool_call['name']}`")
                            st.json(tool_call["args"])
                    streamed_messages.append(message)
                    st.session_state["all_messages"].append(message)
        st.session_state["agent_chat_history"].append(AgentMessage(streamed_messages))
