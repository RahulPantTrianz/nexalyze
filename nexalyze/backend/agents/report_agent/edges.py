"""
Edges for Report Generation Agent
"""
from agents.report_agent.state import ReportAgentState
import logging

logger = logging.getLogger(__name__)


def should_generate_report(state: ReportAgentState) -> str:
    """
    Determine if report should be generated or if content table needs updates.
    
    Returns:
        "generate_report" if content table is ready
        "end" if content table creation failed or user cancelled
    """
    content_table = state.get("content_table")
    status = state.get("status", "drafting")
    
    if status == "error":
        return "end"
    
    if content_table and content_table.sections:
        logger.info("Content table ready, proceeding to report generation")
        return "generate_report"
    
    logger.info("Content table not ready, ending workflow")
    return "end"

