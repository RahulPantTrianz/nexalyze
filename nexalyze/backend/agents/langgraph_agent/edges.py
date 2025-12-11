"""
LangGraph Edges - Routing logic for the conversational agent
"""
from agents.langgraph_agent.state import AgentState
import logging

logger = logging.getLogger(__name__)


def should_continue(state: AgentState) -> str:
    """
    Determine if the agent should continue with tool calls or end.
    
    Returns:
        "continue" if there are tool calls to execute
        "end" if the conversation should end
    """
    messages = state.get("messages", [])
    if not messages:
        return "end"
    
    last_message = messages[-1]
    
    # Check if the last message has tool calls
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        tool_count = len(last_message.tool_calls)
        logger.info(f"Agent requested {tool_count} tool call(s), continuing...")
        return "continue"
    
    # Check iteration count to prevent infinite loops
    iteration_count = state.get("iteration_count", 0)
    if iteration_count >= 10:  # Max 10 iterations
        logger.warning(f"Max iterations ({iteration_count}) reached, ending conversation")
        return "end"
    
    # No tool calls, conversation can end
    logger.info("No tool calls in last message, ending conversation")
    return "end"

