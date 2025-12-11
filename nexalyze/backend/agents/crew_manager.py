"""
CrewAI Manager with Gemini AI Integration
Uses Google Gemini API with retry and exponential backoff for maximum availability
"""

import os
import asyncio
from crewai import Crew, Agent, Task, LLM
from config.settings import settings
from services.gemini_service import get_gemini_service, GeminiService
import logging

logger = logging.getLogger(__name__)


class CrewManager:
    """
    Manages CrewAI agents powered by Google Gemini AI
    Features retry logic and exponential backoff for reliability
    """
    
    def __init__(self):
        """Initialize CrewManager with Gemini-powered LLM"""
        self.gemini_service = get_gemini_service()
        
        # Configure LLM for CrewAI using Gemini
        # CrewAI supports Gemini directly through litellm
        os.environ["GEMINI_API_KEY"] = settings.gemini_api_key
        
        self.llm = LLM(
            model=f"gemini/{settings.gemini_model}",
            temperature=settings.ai_temperature,
            api_key=settings.gemini_api_key
        )
        
        logger.info(f"Initialized CrewManager with Gemini model: {settings.gemini_model}")
        self.agents = self._create_agents()

    def _create_agents(self):
        """Create specialized AI agents for different tasks"""
        
        data_collector = Agent(
            role='Data Collection Specialist',
            goal='Gather comprehensive startup data from multiple sources including YC, Product Hunt, Crunchbase, and web sources',
            backstory='''Expert data collector with deep knowledge of startup ecosystems. 
            Skilled at finding and aggregating company information from Y Combinator, 
            Crunchbase, Product Hunt, BetaList, and various public databases. 
            Known for thorough research and accurate data extraction.''',
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
        
        researcher = Agent(
            role='Market Research Analyst',
            goal='Conduct deep market research and competitive analysis with actionable insights',
            backstory='''Senior market research analyst with 15+ years analyzing startup 
            ecosystems and technology markets. Specialized in identifying market trends, 
            growth opportunities, and industry dynamics. Provides data-driven insights 
            that inform strategic decisions.''',
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
        
        analyzer = Agent(
            role='Competitive Intelligence Analyst',
            goal='Analyze competitive landscapes, identify market gaps, and provide strategic positioning recommendations',
            backstory='''Expert competitive intelligence analyst who has evaluated 
            thousands of startups and enterprises. Skilled at identifying competitive 
            advantages, market positioning strategies, and untapped opportunities. 
            Known for SWOT analyses and competitive benchmarking.''',
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
        
        reporter = Agent(
            role='Business Intelligence Reporter',
            goal='Generate comprehensive, executive-ready reports with actionable insights',
            backstory='''Award-winning business intelligence reporter who transforms 
            complex data into clear, compelling narratives. Specializes in executive 
            summaries, market reports, and strategic recommendations that drive 
            business decisions.''',
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
        
        conversationalist = Agent(
            role='AI Research Assistant',
            goal='Provide natural, helpful responses to user queries about startups, markets, and competitive intelligence',
            backstory='''Friendly and knowledgeable AI assistant specialized in business 
            intelligence and startup research. Helps users navigate complex data, 
            understand market dynamics, and make informed decisions. Known for 
            accurate, well-structured responses.''',
            verbose=True,
            allow_delegation=True,
            llm=self.llm
        )

        return {
            'data_collector': data_collector,
            'researcher': researcher,
            'analyzer': analyzer,
            'reporter': reporter,
            'conversationalist': conversationalist
        }

    async def execute_research(self, query: str, user_session: str = None):
        """
        Execute comprehensive research workflow
        
        Args:
            query: Research query
            user_session: Optional session identifier
        
        Returns:
            Research results
        """
        try:
            logger.info(f"Starting research for query: {query}")
            
            data_task = Task(
                description=f"""Collect comprehensive startup and company data relevant to: {query}
                
                Include:
                - Company profiles and descriptions
                - Industry and market context
                - Funding history if available
                - Key metrics and milestones
                - Relevant news and updates""",
                agent=self.agents['data_collector'],
                expected_output="Structured data about relevant startups and companies with key metrics"
            )
            
            research_task = Task(
                description=f"""Research market trends and ecosystem for: {query}
                
                Analyze:
                - Market size and growth trends
                - Key industry players
                - Technology trends
                - Customer segments
                - Investment trends""",
                agent=self.agents['researcher'],
                expected_output="Comprehensive market research findings with data-backed insights"
            )
            
            analysis_task = Task(
                description=f"""Analyze competitive landscape for: {query}
                
                Provide:
                - Competitive positioning analysis
                - SWOT analysis
                - Market gap identification
                - Strategic recommendations
                - Risk assessment""",
                agent=self.agents['analyzer'],
                expected_output="Detailed competitive analysis with strategic recommendations"
            )
            
            report_task = Task(
                description=f"""Generate executive report for: {query}
                
                Include:
                - Executive summary
                - Key findings
                - Market opportunity assessment
                - Competitive landscape overview
                - Actionable recommendations
                - Risk factors""",
                agent=self.agents['reporter'],
                expected_output="Executive-ready report with actionable insights"
            )

            crew = Crew(
                agents=list(self.agents.values()),
                tasks=[data_task, research_task, analysis_task, report_task],
                verbose=True
            )

            # Execute crew with retry logic
            result = await self._execute_with_retry(crew)
            
            return {
                "query": query,
                "user_session": user_session,
                "results": str(result),
                "status": "completed",
                "timestamp": self._get_timestamp()
            }
            
        except Exception as e:
            logger.error(f"Crew execution failed: {e}")
            # Try fallback with direct Gemini
            return await self._fallback_research(query, user_session)

    async def _execute_with_retry(self, crew: Crew, max_retries: int = 3):
        """Execute crew with retry logic"""
        last_error = None
        
        for attempt in range(max_retries):
            try:
                result = crew.kickoff()
                return result
            except Exception as e:
                last_error = e
                logger.warning(f"Crew execution attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        raise last_error

    async def _fallback_research(self, query: str, user_session: str = None):
        """Fallback to direct Gemini API if CrewAI fails"""
        try:
            prompt = f"""As a business intelligence expert, provide comprehensive analysis for: {query}

Include:
1. Overview and context
2. Market analysis
3. Competitive landscape
4. Key players and competitors
5. Opportunities and challenges
6. Strategic recommendations

Provide detailed, actionable insights."""

            response = await self.gemini_service.generate_content(prompt, temperature=0.3)
            
            return {
                "query": query,
                "user_session": user_session,
                "results": response,
                "status": "completed_fallback",
                "timestamp": self._get_timestamp()
            }
        except Exception as e:
            logger.error(f"Fallback research failed: {e}")
            return {
                "error": str(e),
                "query": query,
                "status": "failed"
            }

    async def handle_conversation(self, query: str, user_session: str = None):
        """
        Handle conversational queries
        
        Args:
            query: User query
            user_session: Session identifier for context
        
        Returns:
            Conversation response
        """
        try:
            # Use Gemini service directly for faster responses
            response = await self.gemini_service.chat(query, session_id=user_session or "default")
            
            return {
                "response": response,
                "query": query,
                "user_session": user_session,
                "timestamp": self._get_timestamp()
            }
            
        except Exception as e:
            logger.error(f"Conversation handling failed: {e}")
            
            # Fallback to CrewAI conversationalist
            try:
                conversation_task = Task(
                    description=f"Answer user query in a helpful, conversational manner: {query}",
                    agent=self.agents['conversationalist'],
                    expected_output="Natural language response to user query"
                )

                crew = Crew(
                    agents=[self.agents['conversationalist']],
                    tasks=[conversation_task],
                    verbose=True
                )

                result = crew.kickoff()
                return {
                    "response": str(result),
                    "query": query,
                    "user_session": user_session,
                    "timestamp": self._get_timestamp()
                }
            except Exception as fallback_error:
                logger.error(f"Conversation fallback also failed: {fallback_error}")
                return {
                    "error": str(e),
                    "query": query,
                    "response": "I apologize, but I'm having trouble processing your request. Please try again."
                }

    async def analyze_company(self, company_name: str, company_data: dict = None):
        """
        Analyze a specific company
        
        Args:
            company_name: Name of the company
            company_data: Optional existing company data
        
        Returns:
            Company analysis
        """
        return await self.gemini_service.analyze_company(company_name, company_data)

    async def discover_competitors(self, company_name: str, industry: str = None):
        """
        Discover competitors for a company
        
        Args:
            company_name: Name of the company
            industry: Optional industry context
        
        Returns:
            List of competitors
        """
        return await self.gemini_service.discover_competitors(company_name, industry)

    async def generate_swot(self, company_name: str, company_data: dict = None):
        """
        Generate SWOT analysis
        
        Args:
            company_name: Name of the company
            company_data: Optional existing company data
        
        Returns:
            SWOT analysis
        """
        return await self.gemini_service.generate_swot_analysis(company_name, company_data)



    def _get_timestamp(self):
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
