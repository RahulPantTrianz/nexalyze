"""
LangGraph Graph for Report Generation Agent
"""
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver
from agents.report_agent.state import ReportAgentState
from agents.report_agent.nodes import node_content_table_agent, node_generate_report_sections, node_background_report_generation
from agents.report_agent.edges import should_generate_report
import logging

logger = logging.getLogger(__name__)

# Create checkpointer for state persistence
checkpointer = MemorySaver()


def create_report_agent_graph():
    """
    Create and compile the report generation agent graph.
    
    Returns:
        Compiled LangGraph workflow
    """
    logger.info("Creating report generation agent graph...")
    
    # Create the workflow
    workflow = StateGraph(ReportAgentState)
    
    # Add nodes
    workflow.add_node("content_table_agent", node_content_table_agent)
    workflow.add_node("generate_sections", node_generate_report_sections)
    workflow.add_node("background_generation", node_background_report_generation)
    
    # Set entry point
    workflow.add_edge(START, "content_table_agent")
    
    # Add conditional edge from content table agent
    workflow.add_conditional_edges(
        "content_table_agent",
        should_generate_report,
        {
            "generate_report": "generate_sections",
            "end": END
        }
    )
    
    # Add edge from generate_sections to background_generation
    workflow.add_edge("generate_sections", "background_generation")
    
    # Add edge from background_generation to END
    workflow.add_edge("background_generation", END)
    
    # Compile the graph
    compiled_graph = workflow.compile(checkpointer=checkpointer)
    
    logger.info("Report generation agent graph compiled successfully")
    return compiled_graph


# Create singleton instance
_report_graph = None


def get_report_agent_graph():
    """Get or create the report generation agent graph (singleton)"""
    global _report_graph
    if _report_graph is None:
        _report_graph = create_report_agent_graph()
    return _report_graph

