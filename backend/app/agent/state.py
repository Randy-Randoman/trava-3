"""
Agent state definition for the LangGraph ReAct agent.
"""

from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    trip_id: str
    user_id: str
