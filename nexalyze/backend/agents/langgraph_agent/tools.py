"""
Tools for LangGraph Conversational Agent
"""
from typing import List, Dict, Any, Optional
from langchain_core.tools import tool
from pydantic import BaseModel, Field
import logging
from services.data_service import DataService
from services.research_service import ResearchService


logger = logging.getLogger(__name__)

# Initialize services
data_service = DataService()
research_service = ResearchService()


class CompanySearchInput(BaseModel):
    """Input for company search tool"""
    query: str = Field(default="", description="Search query to find companies (name, industry, description, etc.). Can be empty to search all.")
    limit: int = Field(default=10, description="Maximum number of companies to return")
    industry: Optional[str] = Field(default=None, description="Filter by industry (e.g., AI, Healthcare, FinTech)")


class CompanyAnalysisInput(BaseModel):
    """Input for company analysis tool"""
    company_name: str = Field(..., description="Name of the company to analyze")
    include_competitors: bool = Field(default=True, description="Whether to include competitor analysis")





class ReportGenerationInput(BaseModel):
    """Input for report generation tool"""
    topic: str = Field(..., description="Topic or company name for the report")
    report_type: str = Field(default="comprehensive", description="Type of report: comprehensive, executive, detailed, market_overview, competitive_analysis")
    format: str = Field(default="pdf", description="Report format: pdf or docx")


@tool("search_companies", args_schema=CompanySearchInput)
async def search_companies_tool(query: str = "", limit: int = 10, industry: Optional[str] = None) -> str:
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
        # Build filters dict
        filters = {}
        if industry:
            filters['industry'] = industry
        
        logger.info(f"Searching companies with query: {query}, limit: {limit}, industry: {industry}")
        companies = await data_service.search_companies(query, limit, filters if filters else None)
        
        if not companies:
            search_desc = f"'{query}'" if query else "all companies"
            if industry:
                search_desc += f" in {industry}"
            return f"No companies found matching {search_desc}. Try a different search term or industry."
        
        result_header = f"Found {len(companies)} companies"
        if query:
            result_header += f" matching '{query}'"
        if industry:
            result_header += f" in {industry}"
        result = f"{result_header}:\n\n"
        
        for idx, company in enumerate(companies, 1):
            result += f"{idx}. **{company.get('name', 'Unknown')}**\n"
            result += f"   - Industry: {company.get('industry', 'N/A')}\n"
            result += f"   - Location: {company.get('location', 'N/A')}\n"
            desc = company.get('description', 'N/A') or 'N/A'
            result += f"   - Description: {desc[:100]}...\n"
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
        from database.connections import postgres_conn
        if not postgres_conn.is_connected():
            return "Database is not connected. Please try again later."
        
        # Get total company count
        result = postgres_conn.query("SELECT COUNT(*) as total FROM companies")
        total_companies = result[0]["total"] if result else 0
        
        # Get industry distribution
        result = postgres_conn.query("""
            SELECT industry, COUNT(*) as count
            FROM companies
            WHERE industry IS NOT NULL
            GROUP BY industry
            ORDER BY count DESC
            LIMIT 10
        """)
        industries = [(r["industry"], r["count"]) for r in result]
        
        # Get location distribution
        result = postgres_conn.query("""
            SELECT location, COUNT(*) as count
            FROM companies
            WHERE location IS NOT NULL
            GROUP BY location
            ORDER BY count DESC
            LIMIT 10
        """)
        locations = [(r["location"], r["count"]) for r in result]
        
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
        generate_report_tool,
        get_company_statistics_tool
    ]

