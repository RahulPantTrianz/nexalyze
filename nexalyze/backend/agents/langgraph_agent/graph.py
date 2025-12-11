"""
LangGraph Graph - Main workflow definition
"""
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from agents.langgraph_agent.state import AgentState
from agents.langgraph_agent.nodes import agent_node, tools_node
from agents.langgraph_agent.edges import should_continue
import logging

logger = logging.getLogger(__name__)

# Create checkpointer for state persistence
checkpointer = MemorySaver()


def create_conversational_agent_graph():
    """
    Create and compile the conversational agent graph.
    
    Returns:
        Compiled LangGraph workflow
    """
    logger.info("Creating conversational agent graph...")
    
    # Create the workflow
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tools_node)
    
    # Set entry point
    workflow.set_entry_point("agent")
    
    # Add conditional edge from agent
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "continue": "tools",
            "end": END,
        },
    )
    
    # Add edge from tools back to agent
    workflow.add_edge("tools", "agent")
    
    # Compile the graph with checkpointer
    compiled_graph = workflow.compile(checkpointer=checkpointer)
    
    logger.info("Conversational agent graph compiled successfully")
    return compiled_graph


# Create singleton instance
_conversational_graph = None


def get_conversational_agent_graph():
    """Get or create the conversational agent graph (singleton)"""
    global _conversational_graph
    if _conversational_graph is None:
        _conversational_graph = create_conversational_agent_graph()
    return _conversational_graph

