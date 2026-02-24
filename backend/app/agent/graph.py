"""
LangGraph ReAct agent graph.

Pattern: START -> agent_node -> should_continue? -> tool_node (loop) or END
"""

import sys
from pathlib import Path
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from app.agent.state import AgentState
from app.core.config import settings
from app.core.prompts import build_system_prompt

# Ensure the repo root is on sys.path so `skills` is importable.
# The backend runs from backend/, but skills/ lives at the repo root.
_repo_root = str(Path(__file__).resolve().parents[3])
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

from skills import load_all_skills


def _get_llm():
    """Create the LLM based on LLM_PROVIDER setting."""
    provider = settings.LLM_PROVIDER.lower()

    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model="claude-sonnet-4.6",
            api_key=settings.ANTHROPIC_API_KEY,
        )
    else:
        # Default: Google Gemini
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model="gemini-3-flash-preview",
            google_api_key=settings.GOOGLE_API_KEY,
        )


def create_agent_graph(trip_id: str, user_id: str):
    """Create a compiled LangGraph agent ready to invoke.

    Args:
        trip_id: The current trip context.
        user_id: The authenticated user ID.

    Returns:
        A compiled StateGraph that accepts AgentState.
    """
    # Load tools and skill prompts from the skills registry
    tools, skill_prompts = load_all_skills()

    # Build the system prompt with skill-specific instructions
    system_prompt = build_system_prompt(skill_prompts)

    # Create LLM and bind tools
    llm = _get_llm()
    if tools:
        llm_with_tools = llm.bind_tools(tools)
    else:
        llm_with_tools = llm

    # --- Nodes ---

    def agent_node(state: AgentState):
        """Call the LLM with the current messages."""
        messages = state["messages"]

        # Prepend system message if not already present
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=system_prompt)] + messages

        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    def should_continue(state: AgentState):
        """Check if the agent wants to call tools or is done."""
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return END

    # --- Build graph ---

    graph = StateGraph(AgentState)

    graph.add_node("agent", agent_node)

    if tools:
        tool_node = ToolNode(tools)
        graph.add_node("tools", tool_node)
        graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
        graph.add_edge("tools", "agent")
    else:
        # No tools -- agent just responds and we're done
        graph.add_edge("agent", END)

    graph.set_entry_point("agent")

    return graph.compile()
