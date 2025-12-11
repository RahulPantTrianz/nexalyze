"""
LangGraph State Management for Conversational Agent
"""
from typing import Annotated, TypedDict, Optional, List, Dict, Any
from langchain_core.messages import AnyMessage, BaseMessage
from langgraph.graph.message import add_messages


def append_list(a: List[str], b: List[str]) -> List[str]:
    """Reducer function to append lists"""
    return a + b


class AgentState(TypedDict):
    """State for the conversational agent"""
    messages: Annotated[List[BaseMessage], add_messages]
    session_id: str
    user_query: Optional[str]
    context: Optional[Dict[str, Any]]
    tools_used: Annotated[List[str], append_list]  # Track which tools were used
    iteration_count: int  # Track number of agent-tool iterations

