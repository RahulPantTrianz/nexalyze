import os
import asyncio
from crewai import Crew, Agent, Task, LLM
from config.settings import settings
from services.bedrock_service import get_bedrock_service
import logging

logger = logging.getLogger(__name__)


class CrewManager:
    """
    Manages CrewAI agents powered by AWS Bedrock (Claude)
    """
    
    def __init__(self):
        """Initialize CrewManager with Bedrock LLM"""
        self.bedrock_service = get_bedrock_service()
        
        # Configure LLM for CrewAI using Bedrock via LiteLLM
        # We use the same model ID as the service
        model_id = self.bedrock_service.model_id
        # LiteLLM expects "bedrock/<model_id>"
        # If the model ID already starts with the provider prefix, adjust accordingly.
        # But usually standard Bedrock IDs don't have "bedrock/" prefix.
        
        self.llm = LLM(
            model=f"bedrock/{model_id}",
            temperature=0.7,
        )
        
        logger.info(f"Initialized CrewManager with Bedrock model: {model_id}")
        self.agents = self._create_agents()

    def _create_agents(self):
        """Create specialized AI agents for different tasks"""
        
        data_collector = Agent(
            role='Data Collection Specialist',
            goal='Gather comprehensive startup data from multiple sources',
            backstory='''Expert data collector with deep knowledge of startup ecosystems. 
            Skilled at finding and aggregating company information suitable for investment analysis.''',
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
        
        researcher = Agent(
            role='Market Research Analyst',
            goal='Conduct deep market research and competitive analysis',
            backstory='''Senior market research analyst with 15+ years analyzing startup 
            ecosystems and technology markets.''',
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
        
        analyzer = Agent(
            role='Competitive Intelligence Analyst',
            goal='Analyze competitive landscapes and identify market gaps',
            backstory='''Expert competitive intelligence analyst who has evaluated 
            thousands of startups and enterprises.''',
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
        
        reporter = Agent(
            role='Business Intelligence Reporter',
            goal='Generate comprehensive, executive-ready reports',
            backstory='''Award-winning business intelligence reporter who transforms 
            complex data into clear, compelling narratives.''',
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
        
        conversationalist = Agent(
            role='AI Research Assistant',
            goal='Provide natural responses to user queries',
            backstory='''Friendly and knowledgeable AI assistant specialized in business 
            intelligence and startup research.''',
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
        """Execute comprehensive research workflow"""
        try:
            logger.info(f"Starting research for query: {query}")
            
            data_task = Task(
                description=f"Collect comprehensive startup and company data for: {query}",
                agent=self.agents['data_collector'],
                expected_output="Structured data about relevant companies"
            )
            
            research_task = Task(
                description=f"Research market trends for: {query}",
                agent=self.agents['researcher'],
                expected_output="Market research findings"
            )
            
            report_task = Task(
                description=f"Generate executive report for: {query}",
                agent=self.agents['reporter'],
                expected_output="Executive summary report"
            )

            crew = Crew(
                agents=list(self.agents.values())[:3], # Use subset for speed
                tasks=[data_task, research_task, report_task],
                verbose=True
            )

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
            return await self._fallback_research(query, user_session)

    async def _execute_with_retry(self, crew: Crew, max_retries: int = 3):
        """Execute crew with retry logic"""
        last_error = None
        for attempt in range(max_retries):
            try:
                # synchronous kickoff wrapped in thread if needed, but crewai recent versions support async?
                # kickoff() is sync. kickoff_async() exists?
                # We'll stick to kickoff() but it blocks loop. Ideally run in executor.
                result = await asyncio.to_thread(crew.kickoff)
                return result
            except Exception as e:
                last_error = e
                logger.warning(f"Crew execution attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
        raise last_error

    async def _fallback_research(self, query: str, user_session: str = None):
        """Fallback to direct Bedrock API"""
        try:
            prompt = f"Analyze: {query}. Provide market overview."
            response = await self.bedrock_service.generate_text(prompt, temperature=0.7)
            return {
                "results": response,
                "status": "completed_fallback",
                "timestamp": self._get_timestamp()
            }
        except Exception as e:
            logger.error(f"Fallback research failed: {e}")
            return {"error": str(e)}

    async def handle_conversation(self, query: str, user_session: str = None):
        """Handle conversational queries via Bedrock"""
        try:
            response = await self.bedrock_service.generate_text(query, temperature=0.7)
            return {
                "response": response,
                "user_session": user_session,
                "timestamp": self._get_timestamp()
            }
        except Exception as e:
            logger.error(f"Conversation failed: {e}")
            return {"error": str(e), "response": "Sorry, I can't process that right now."}

    # Helper methods mapped to ResearchService logic could go here, 
    # but for now we just remove Gemini dependency.

    def _get_timestamp(self):
        from datetime import datetime
        return datetime.now().isoformat()
