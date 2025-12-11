"""
State Management for Report Generation Agent
"""
from typing import Annotated, TypedDict, Optional, List, Dict, Any
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel


def append_dict_list(a: List[Dict[str, Any]], b: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Reducer function to append lists of dictionaries"""
    return a + b


class ContentTableSection(BaseModel):
    """Represents a section in the content table"""
    heading: str
    sources: List[str]
    focus_elements: Optional[List[str]] = []
    notes: Optional[List[str]] = []


class ContentTable(BaseModel):
    """Content table structure for report"""
    sections: List[ContentTableSection]
    title: str
    summary: Optional[str] = None


class ReportAgentState(TypedDict):
    """State for the report generation agent"""
    messages: Annotated[List[BaseMessage], add_messages]
    session_id: str
    topic: str
    report_type: str
    content_table: Optional[ContentTable]
    current_section: Optional[ContentTableSection]
    report_sections: Annotated[List[Dict[str, Any]], append_dict_list]  # Generated HTML sections
    status: str  # "drafting", "generating", "completed", "error"

