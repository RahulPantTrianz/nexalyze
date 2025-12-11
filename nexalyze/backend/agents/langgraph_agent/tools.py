"""
Tools for LangGraph Conversational Agent
"""
from typing import List, Dict, Any, Optional
from langchain_core.tools import tool
from pydantic import BaseModel, Field
import logging
from services.data_service import DataService
from services.research_service import ResearchService
from database.connections import neo4j_conn

logger = logging.getLogger(__name__)

# Initialize services
data_service = DataService()
research_service = ResearchService()


class CompanySearchInput(BaseModel):
    """Input for company search tool"""
    query: str = Field(..., description="Search query to find companies (name, industry, description, etc.)")
    limit: int = Field(default=10, description="Maximum number of companies to return")


class CompanyAnalysisInput(BaseModel):
    """Input for company analysis tool"""
    company_name: str = Field(..., description="Name of the company to analyze")
    include_competitors: bool = Field(default=True, description="Whether to include competitor analysis")


class KnowledgeGraphInput(BaseModel):
    """Input for knowledge graph tool"""
    company_name: str = Field(..., description="Name of the company to get knowledge graph for")


class ReportGenerationInput(BaseModel):
    """Input for report generation tool"""
    topic: str = Field(..., description="Topic or company name for the report")
    report_type: str = Field(default="comprehensive", description="Type of report: comprehensive, executive, detailed, market_overview, competitive_analysis")
    format: str = Field(default="pdf", description="Report format: pdf or docx")


@tool("search_companies", args_schema=CompanySearchInput)
async def search_companies_tool(query: str, limit: int = 10) -> str:
    """
    Search for companies in the database by name, industry, description, or other attributes.
    
    Use this tool when the user asks about:
    - Finding companies in a specific industry
    - Searching for companies by name
    - Looking for companies with specific characteristics
    - Getting a list of companies matching criteria
    
    Returns a formatted list of companies with their key information.
    """
    try:
        logger.info(f"Searching companies with query: {query}, limit: {limit}")
        companies = await data_service.search_companies(query, limit)
        
        if not companies:
            return f"No companies found matching '{query}'. Try a different search term."
        
        result = f"Found {len(companies)} companies matching '{query}':\n\n"
        for idx, company in enumerate(companies, 1):
            result += f"{idx}. **{company.get('name', 'Unknown')}**\n"
            result += f"   - Industry: {company.get('industry', 'N/A')}\n"
            result += f"   - Location: {company.get('location', 'N/A')}\n"
            result += f"   - Description: {company.get('description', 'N/A')[:100]}...\n"
            if company.get('yc_batch'):
                result += f"   - YC Batch: {company.get('yc_batch')}\n"
            result += "\n"
        
        return result
    except Exception as e:
        logger.error(f"Company search tool failed: {e}")
        return f"Error searching companies: {str(e)}"


@tool("analyze_company", args_schema=CompanyAnalysisInput)
async def analyze_company_tool(company_name: str, include_competitors: bool = True) -> str:
    """
    Perform comprehensive analysis of a specific company including:
    - Company overview and details
    - Competitive landscape (if requested)
    - Market positioning
    - Key metrics and insights
    
    Use this tool when the user asks about:
    - Analyzing a specific company
    - Getting detailed information about a company
    - Understanding a company's competitive position
    - Company insights and analysis
    """
    try:
        logger.info(f"Analyzing company: {company_name}, include_competitors: {include_competitors}")
        analysis = await research_service.analyze_company(
            company_name,
            include_competitors,
            data_service
        )
        
        if not analysis:
            return f"Could not find or analyze company '{company_name}'. Please check the company name."
        
        result = f"## Analysis of {company_name}\n\n"
        
        if analysis.get('company'):
            company = analysis['company']
            result += f"**Company Overview:**\n"
            result += f"- Industry: {company.get('industry', 'N/A')}\n"
            result += f"- Location: {company.get('location', 'N/A')}\n"
            result += f"- Description: {company.get('description', 'N/A')}\n"
            if company.get('website'):
                result += f"- Website: {company.get('website')}\n"
            result += "\n"
        
        if include_competitors and analysis.get('competitors'):
            competitors = analysis['competitors']
            result += f"**Competitive Landscape ({len(competitors)} competitors found):**\n"
            for idx, comp in enumerate(competitors[:5], 1):  # Top 5
                result += f"{idx}. {comp.get('name', 'Unknown')} - {comp.get('industry', 'N/A')}\n"
            result += "\n"
        
        if analysis.get('insights'):
            result += f"**Key Insights:**\n{analysis['insights']}\n"
        
        return result
    except Exception as e:
        logger.error(f"Company analysis tool failed: {e}")
        return f"Error analyzing company: {str(e)}"


@tool("get_knowledge_graph", args_schema=KnowledgeGraphInput)
async def get_knowledge_graph_tool(company_name: str) -> str:
    """
    Get knowledge graph data for a company showing relationships, dependencies, competitors, opportunities, and risks.
    
    Use this tool when the user asks about:
    - Company relationships and connections
    - Business ecosystem of a company
    - Dependencies and partnerships
    - Competitive relationships
    """
    try:
        logger.info(f"Getting knowledge graph for: {company_name}")
        graph_data = await data_service.get_knowledge_graph_by_name(company_name)
        
        if not graph_data or not graph_data.get('nodes'):
            return f"Could not generate knowledge graph for '{company_name}'. The company may not be in the database."
        
        result = f"## Knowledge Graph for {company_name}\n\n"
        
        nodes = graph_data.get('nodes', [])
        edges = graph_data.get('edges', [])
        
        result += f"**Graph Statistics:**\n"
        result += f"- Nodes: {len(nodes)}\n"
        result += f"- Relationships: {len(edges)}\n\n"
        
        # Group nodes by type
        node_types = {}
        for node in nodes:
            node_type = node.get('type', 'unknown')
            if node_type not in node_types:
                node_types[node_type] = []
            node_types[node_type].append(node.get('name', 'Unknown'))
        
        for node_type, names in node_types.items():
            result += f"**{node_type.title()}:**\n"
            for name in names[:10]:  # Limit to 10 per type
                result += f"- {name}\n"
            if len(names) > 10:
                result += f"- ... and {len(names) - 10} more\n"
            result += "\n"
        
        return result
    except Exception as e:
        logger.error(f"Knowledge graph tool failed: {e}")
        return f"Error getting knowledge graph: {str(e)}"


@tool("generate_report", args_schema=ReportGenerationInput)
async def generate_report_tool(topic: str, report_type: str = "comprehensive", format: str = "pdf") -> str:
    """
    Generate a comprehensive report for a topic, company, or industry.
    
    Report types:
    - comprehensive: Full detailed report with all sections
    - executive: Brief executive summary for C-suite
    - detailed: Deep analytical report with extensive data
    - market_overview: Market-level insights and trends
    - competitive_analysis: Focus on competitive landscape
    
    Use this tool when the user asks about:
    - Generating a report
    - Creating analysis documents
    - Getting comprehensive insights on a topic
    - Producing executive summaries
    """
    try:
        logger.info(f"Generating {report_type} report for topic: {topic}, format: {format}")
        from services.report_service import EnhancedReportService
        
        report_service = EnhancedReportService()
        result = await report_service.generate_comprehensive_report(
            topic=topic,
            report_type=report_type,
            format=format
        )
        
        if result.get('success'):
            report_path = result.get('report_path', '')
            report_filename = result.get('report_filename', '')
            return f"✅ Report generated successfully!\n\n" \
                   f"- **Topic:** {topic}\n" \
                   f"- **Type:** {report_type}\n" \
                   f"- **Format:** {format}\n" \
                   f"- **Filename:** {report_filename}\n" \
                   f"- **Charts Generated:** {result.get('charts_generated', 0)}\n\n" \
                   f"You can download the report using the filename: {report_filename}"
        else:
            return f"❌ Report generation failed: {result.get('error', 'Unknown error')}"
    except Exception as e:
        logger.error(f"Report generation tool failed: {e}")
        return f"Error generating report: {str(e)}"


@tool("get_company_statistics")
async def get_company_statistics_tool() -> str:
    """
    Get overall statistics about companies in the database.
    
    Use this tool when the user asks about:
    - Total number of companies
    - Database statistics
    - Overall data metrics
    - System status
    """
    try:
        if not neo4j_conn.is_connected():
            return "Database is not connected. Please try again later."
        
        with neo4j_conn.driver.session() as session:
            # Get total company count
            result = session.run("MATCH (c:Company) RETURN count(c) as total")
            record = result.single()
            total_companies = record["total"] if record else 0
            
            # Get industry distribution
            result = session.run("""
                MATCH (c:Company)
                WHERE c.industry IS NOT NULL
                RETURN c.industry as industry, count(c) as count
                ORDER BY count DESC
                LIMIT 10
            """)
            industries = [(record["industry"], record["count"]) for record in result]
            
            # Get location distribution
            result = session.run("""
                MATCH (c:Company)
                WHERE c.location IS NOT NULL
                RETURN c.location as location, count(c) as count
                ORDER BY count DESC
                LIMIT 10
            """)
            locations = [(record["location"], record["count"]) for record in result]
        
        result = f"## Database Statistics\n\n"
        result += f"**Total Companies:** {total_companies:,}\n\n"
        
        if industries:
            result += f"**Top Industries:**\n"
            for industry, count in industries:
                result += f"- {industry}: {count} companies\n"
            result += "\n"
        
        if locations:
            result += f"**Top Locations:**\n"
            for location, count in locations:
                result += f"- {location}: {count} companies\n"
        
        return result
    except Exception as e:
        logger.error(f"Statistics tool failed: {e}")
        return f"Error getting statistics: {str(e)}"


def get_all_tools() -> List:
    """Get all available tools for the agent"""
    return [
        search_companies_tool,
        analyze_company_tool,
        get_knowledge_graph_tool,
        generate_report_tool,
        get_company_statistics_tool
    ]

