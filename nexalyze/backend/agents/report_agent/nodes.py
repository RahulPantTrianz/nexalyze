"""
Nodes for Report Generation Agent
"""
from typing import Dict, Any
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from agents.report_agent.state import ReportAgentState, ContentTable, ContentTableSection
from services.gemini_service import get_gemini_service
import logging
import json
import re

logger = logging.getLogger(__name__)

gemini_service = get_gemini_service()

CONTENT_TABLE_PROMPT = """You are an expert report content planner. Your task is to create a structured content table for a {report_type} report on the topic: {topic}.

Based on the available data and the report type, create a comprehensive content table with sections that will guide the report generation.

**Report Types:**
- comprehensive: Full detailed report with all sections
- executive: Brief executive summary for C-suite (3-5 sections max)
- detailed: Deep analytical report with extensive data (8-12 sections)
- market_overview: Market-level insights and trends (5-7 sections)
- competitive_analysis: Focus on competitive landscape (6-8 sections)

**Output Format (JSON only):**
{{
    "title": "Report Title",
    "summary": "Brief overview of the report",
    "sections": [
        {{
            "heading": "Section Heading",
            "sources": ["data_source_1", "data_source_2"],
            "focus_elements": ["element1", "element2"],
            "notes": ["note1", "note2"]
        }}
    ]
}}

Return ONLY valid JSON, no additional text."""


async def node_content_table_agent(state: ReportAgentState) -> Dict[str, Any]:
    """
    Node that creates or updates the content table for the report.
    """
    topic = state.get("topic", "")
    report_type = state.get("report_type", "comprehensive")
    current_table = state.get("content_table")
    
    logger.info(f"Content table agent processing for topic: {topic}, type: {report_type}")
    
    # If content table exists, ask for updates
    if current_table:
        # Convert ContentTable to dict for JSON serialization
        if hasattr(current_table, 'model_dump'):
            table_dict = current_table.model_dump()
        elif hasattr(current_table, 'dict'):
            table_dict = current_table.dict()
        else:
            table_dict = {
                "title": getattr(current_table, 'title', f"Report on {topic}"),
                "summary": getattr(current_table, 'summary', None),
                "sections": [
                    {
                        "heading": getattr(s, 'heading', ''),
                        "sources": getattr(s, 'sources', []),
                        "focus_elements": getattr(s, 'focus_elements', []),
                        "notes": getattr(s, 'notes', [])
                    }
                    for s in getattr(current_table, 'sections', [])
                ]
            }
        
        prompt = f"""Review and update the existing content table for a {report_type} report on {topic}.

Current Content Table:
{json.dumps(table_dict, indent=2)}

Provide an updated content table in JSON format (same structure as before)."""
    else:
        prompt = CONTENT_TABLE_PROMPT.format(topic=topic, report_type=report_type)
    
    try:
        response = await gemini_service.generate_content(prompt, temperature=0.3)
        
        # Extract JSON from response
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            content_table_dict = json.loads(json_match.group())
            # Convert sections to ContentTableSection objects
            sections = [
                ContentTableSection(**section) if isinstance(section, dict) else section
                for section in content_table_dict.get('sections', [])
            ]
            content_table = ContentTable(
                title=content_table_dict.get('title', f"Report on {topic}"),
                summary=content_table_dict.get('summary'),
                sections=sections
            )
            
            logger.info(f"Content table created with {len(content_table.sections)} sections")
            
            return {
                "content_table": content_table,
                "status": "drafting",
                "messages": [AIMessage(content=f"Content table created with {len(content_table.sections)} sections. Ready to generate report.")]
            }
        else:
            raise ValueError("Could not extract JSON from response")
            
    except Exception as e:
        logger.error(f"Content table generation failed: {e}")
        return {
            "status": "error",
            "messages": [AIMessage(content=f"Error creating content table: {str(e)}")]
        }


async def node_generate_report_sections(state: ReportAgentState) -> Dict[str, Any]:
    """
    Node that generates report sections based on the content table.
    Uses actual data from DataService and ResearchService for data-driven insights.
    """
    content_table = state.get("content_table")
    topic = state.get("topic", "")
    report_type = state.get("report_type", "comprehensive")
    report_sections = state.get("report_sections", [])
    
    if not content_table or not content_table.sections:
        logger.warning("No content table or sections available")
        return {
            "status": "error",
            "messages": [AIMessage(content="No content table available. Please create one first.")]
        }
    
    logger.info(f"Generating report sections for {len(content_table.sections)} sections")
    
    # Get actual data for context
    from services.data_service import DataService
    from services.research_service import ResearchService
    
    data_service = DataService()
    research_service = ResearchService()
    
    # Fetch companies related to topic
    companies = await data_service.search_companies(topic, 20)
    
    # Process each section with data-driven content
    for section in content_table.sections:
        try:
            logger.info(f"Processing section: {section.heading}")
            
            # Prepare data context based on section heading
            data_context = ""
            if "executive" in section.heading.lower() or "summary" in section.heading.lower():
                data_context = f"""
DATA CONTEXT:
- Companies analyzed: {len(companies)}
- Top companies: {', '.join([c.get('name', 'Unknown') for c in companies[:5]])}
- Industries: {', '.join(list(set(c.get('industry', 'Unknown') for c in companies))[:5])}
"""
            elif "market" in section.heading.lower():
                industries = {}
                locations = {}
                for company in companies:
                    industry = company.get('industry', 'Unknown')
                    industries[industry] = industries.get(industry, 0) + 1
                    location = company.get('location', 'Unknown')
                    locations[location] = locations.get(location, 0) + 1
                
                data_context = f"""
DATA CONTEXT:
- Total companies: {len(companies)}
- Industry segments: {len(industries)}
- Top industries: {', '.join(sorted(industries.items(), key=lambda x: x[1], reverse=True)[:3])}
- Geographic distribution: {', '.join(sorted(locations.items(), key=lambda x: x[1], reverse=True)[:3])}
"""
            elif "company" in section.heading.lower() or "competitive" in section.heading.lower():
                top_companies = sorted(companies, key=lambda x: len(x.get('name', '')), reverse=True)[:10]
                data_context = f"""
DATA CONTEXT:
- Top companies: {', '.join([c.get('name', 'Unknown') for c in top_companies])}
- Company details available for analysis
"""
            else:
                data_context = f"""
DATA CONTEXT:
- Topic: {topic}
- Companies analyzed: {len(companies)}
- Report type: {report_type}
"""
            
            # Generate section content with data context
            section_prompt = f"""Generate comprehensive, data-driven content for the following report section:

**Section Heading:** {section.heading}
**Focus Elements:** {', '.join(section.focus_elements) if section.focus_elements else 'General analysis'}
**Notes:** {', '.join(section.notes) if section.notes else 'None'}
**Topic:** {topic}
**Report Type:** {report_type}
{data_context}

**Requirements:**
1. Use the data context provided above to include specific numbers, metrics, and insights
2. Format content in clean HTML with proper headings (h2, h3), paragraphs, lists, and tables
3. Include specific examples from the data when relevant
4. Make it professional, well-structured, and suitable for a {report_type} report
5. Use metrics, percentages, and concrete data points
6. Keep content focused and concise but comprehensive

**Output Format:**
Return the content wrapped in <section> tags with proper HTML structure. Example:
<section>
    <h2>{section.heading}</h2>
    <p>Introduction paragraph...</p>
    <h3>Subsection</h3>
    <ul>
        <li>Key point 1</li>
        <li>Key point 2</li>
    </ul>
    ...
</section>

Generate the content now:"""

            section_content = await gemini_service.generate_content(section_prompt, temperature=0.3)
            
            # Extract HTML content
            html_match = re.search(r'<section>(.*?)</section>', section_content, re.DOTALL)
            if html_match:
                html_content = html_match.group(1).strip()
            else:
                # Try to find any HTML content
                if '<h2>' in section_content or '<h3>' in section_content:
                    html_content = section_content
                else:
                    # Fallback: wrap in proper HTML structure
                    html_content = f"<div><h2>{section.heading}</h2><p>{section_content}</p></div>"
            
            report_sections.append({
                "heading": section.heading,
                "content": html_content,
                "sources": section.sources,
                "focus_elements": section.focus_elements
            })
            
        except Exception as e:
            logger.error(f"Error generating section {section.heading}: {e}")
            import traceback
            traceback.print_exc()
            report_sections.append({
                "heading": section.heading,
                "content": f"<div><h2>{section.heading}</h2><p>Error generating this section: {str(e)}</p></div>",
                "sources": section.sources
            })
    
    logger.info(f"Generated {len(report_sections)} report sections")
    
    return {
        "report_sections": report_sections,
        "status": "completed",
        "messages": [AIMessage(content=f"Report generation completed with {len(report_sections)} sections.")]
    }


async def node_background_report_generation(state: ReportAgentState) -> Dict[str, Any]:
    """
    Node that marks report generation as complete.
    The actual compilation happens in the report service after sections are generated.
    """
    topic = state.get("topic", "")
    report_type = state.get("report_type", "comprehensive")
    report_sections = state.get("report_sections", [])
    
    logger.info(f"Report sections ready for compilation: {topic} ({len(report_sections)} sections)")
    
    # The actual PDF/DOCX compilation will happen in the report service
    # This node just marks the workflow as complete
    return {
        "status": "completed",
        "messages": [AIMessage(content=f"Report sections generated successfully. Ready for compilation into final document.")]
    }

