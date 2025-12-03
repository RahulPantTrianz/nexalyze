import os
import boto3
from crewai import Crew, Agent, Task, LLM
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

class CrewManager:
    def __init__(self):
        # Configure AWS Bedrock session with profile
        session = boto3.Session(
            profile_name=settings.aws_profile,
            region_name=settings.aws_region
        )
        
        # Get credentials from the session
        credentials = session.get_credentials()
        
        # Set AWS credentials as environment variables for litellm/CrewAI
        os.environ["AWS_ACCESS_KEY_ID"] = credentials.access_key
        os.environ["AWS_SECRET_ACCESS_KEY"] = credentials.secret_key
        if credentials.token:
            os.environ["AWS_SESSION_TOKEN"] = credentials.token
        os.environ["AWS_REGION_NAME"] = settings.aws_region
        
        # Use CrewAI's LLM class with bedrock provider format
        # This properly integrates with litellm for Bedrock inference
        self.llm = LLM(
            model=f"bedrock/{settings.bedrock_model_id}",
            temperature=0.3
        )
        
        logger.info(f"Initialized LLM with model: bedrock/{settings.bedrock_model_id}")
        self.agents = self._create_agents()

    def _create_agents(self):
        data_collector = Agent(
            role='Data Collection Specialist',
            goal='Gather comprehensive startup data from multiple sources',
            backstory='Expert at finding and aggregating startup information from Y Combinator, Crunchbase, and other sources',
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
        researcher = Agent(
            role='Market Research Analyst',
            goal='Conduct deep market research and competitive analysis',
            backstory='Specialized in startup ecosystem analysis and market trend identification',
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
        analyzer = Agent(
            role='Competitive Intelligence Analyst',
            goal='Analyze competitive landscapes and identify market gaps',
            backstory='Expert at identifying competitive advantages and market opportunities',
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
        reporter = Agent(
            role='Business Intelligence Reporter',
            goal='Generate comprehensive reports and actionable insights',
            backstory='Skilled at synthesizing complex data into clear, actionable business reports',
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
        conversationalist = Agent(
            role='AI Assistant',
            goal='Provide natural language interface for user queries',
            backstory='Friendly AI assistant that helps users navigate startup intelligence data',
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
        try:
            data_task = Task(description=f"Collect startup data relevant to: {query}", agent=self.agents['data_collector'], expected_output="Structured data about relevant startups")
            research_task = Task(description=f"Research market trends and ecosystem for: {query}", agent=self.agents['researcher'], expected_output="Market research findings and trends")
            analysis_task = Task(description=f"Analyze competitive landscape for: {query}", agent=self.agents['analyzer'], expected_output="Competitive analysis and market gaps")
            report_task = Task(description=f"Generate comprehensive report for: {query}", agent=self.agents['reporter'], expected_output="Executive summary with actionable insights")

            crew = Crew(
                agents=list(self.agents.values()),
                tasks=[data_task, research_task, analysis_task, report_task],
                verbose=True
            )

            result = crew.kickoff()
            return {"query": query, "user_session": user_session, "results": str(result), "timestamp": "2025-10-09T23:00:00Z"}
        except Exception as e:
            logger.error(f"Crew execution failed: {e}")
            return {"error": str(e), "query": query}

    async def handle_conversation(self, query: str, user_session: str = None):
        try:
            conversation_task = Task(description=f"Answer user query in conversational manner: {query}", agent=self.agents['conversationalist'], expected_output="Natural language response to user query")

            crew = Crew(
                agents=[self.agents['conversationalist']],
                tasks=[conversation_task],
                verbose=True
            )

            result = crew.kickoff()
            return {"response": str(result), "query": query, "user_session": user_session}
        except Exception as e:
            logger.error(f"Conversation handling failed: {e}")
            return {"error": str(e), "query": query}