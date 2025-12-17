"""
AWS Bedrock Service for LLM inference using Claude Sonnet 4.5
"""
import os
import logging
import json
import re
from typing import Optional, Dict, Any, List
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError, ProfileNotFound
from langchain_aws import ChatBedrockConverse
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from config.settings import settings

logger = logging.getLogger(__name__)


class BedrockService:
    """Service for interacting with AWS Bedrock Claude models"""
    
    def __init__(
        self,
        model_id: str = None,
        aws_profile: str = None,
        region_name: str = None,
        temperature: float = None,
        max_tokens: int = None
    ):
        """
        Initialize Bedrock service with Claude Sonnet 4.5
        
        Args:
            model_id: Bedrock model ID
            aws_profile: AWS profile name to use
            region_name: AWS region
            temperature: Model temperature (0-1)
            max_tokens: Maximum tokens to generate
        """
        self.model_id = model_id or settings.bedrock_model_id
        self.aws_profile = aws_profile or settings.aws_profile
        self.region_name = region_name or settings.aws_region
        self.temperature = temperature if temperature is not None else settings.ai_temperature
        self.max_tokens = max_tokens if max_tokens is not None else settings.ai_max_tokens
        
        # Chat session storage
        self.chat_sessions: Dict[str, List[Any]] = {}
        
        # Initialize boto3 session
        self._init_session()
        
        # Create Bedrock client
        config = Config(
            region_name=self.region_name,
            retries={'max_attempts': 3, 'mode': 'adaptive'}
        )
        
        try:
            self.bedrock_client = self.session.client(
                service_name='bedrock-runtime',
                config=config
            )
            logger.info(f"Bedrock client initialized for region: {self.region_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Bedrock client: {e}")
            raise
        
        # Initialize ChatBedrockConverse
        self._init_chat_model()

    def _init_session(self):
        """Initialize AWS session"""
        # Try using access keys from settings first
        if settings.aws_access_key_id and settings.aws_secret_access_key:
            try:
                self.session = boto3.Session(
                    aws_access_key_id=settings.aws_access_key_id,
                    aws_secret_access_key=settings.aws_secret_access_key,
                    region_name=self.region_name
                )
                logger.info("Initialized AWS session with provided access keys")
                return
            except Exception as e:
                logger.warning(f"Failed to use provided access keys: {e}")

        # Fallback to profile
        try:
            self.session = boto3.Session(profile_name=self.aws_profile)
            logger.info(f"Initialized AWS session with profile: {self.aws_profile}")
        except ProfileNotFound:
            logger.warning(f"Profile '{self.aws_profile}' not found, falling back to default credentials.")
            self.session = boto3.Session()
        except Exception as e:
            logger.warning(f"Failed to use profile '{self.aws_profile}', using default credentials: {e}")
            self.session = boto3.Session()
    
    def _init_chat_model(self):
        """Initialize or reinitialize the chat model"""
        try:
            self.chat_model = ChatBedrockConverse(
                client=self.bedrock_client,
                model=self.model_id,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            logger.info(f"ChatBedrockConverse initialized with model: {self.model_id}")
        except Exception as e:
            logger.error(f"Failed to initialize ChatBedrockConverse: {e}")
            raise
    
    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generate text using Claude via Bedrock
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Override default temperature
            max_tokens: Override default max tokens
            
        Returns:
            Generated text
        """
        try:
            # Create a temporary model/client if params are overridden
            if temperature is not None or max_tokens is not None:
                chat_model = ChatBedrockConverse(
                    client=self.bedrock_client,
                    model=self.model_id,
                    temperature=temperature if temperature is not None else self.temperature,
                    max_tokens=max_tokens if max_tokens is not None else self.max_tokens,
                )
            else:
                chat_model = self.chat_model
            
            # Build messages
            messages = []
            if system_prompt:
                messages.append(SystemMessage(content=system_prompt))
            messages.append(HumanMessage(content=prompt))
            
            # Invoke model
            logger.debug(f"Generating text with Bedrock (prompt length: {len(prompt)})")
            response = await chat_model.ainvoke(messages)
            
            # Extract content
            if hasattr(response, 'content'):
                result = response.content
            else:
                result = str(response)
            
            return result
            
        except Exception as e:
            logger.error(f"Bedrock text generation failed: {e}")
            raise
    
    async def generate_with_retry(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_retries: int = 3,
        **kwargs
    ) -> str:
        """
        Generate text with automatic retry on failure
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            max_retries: Maximum retry attempts
            **kwargs: Additional arguments for generate_text
            
        Returns:
            Generated text
        """
        import asyncio
        
        last_error = None
        for attempt in range(max_retries):
            try:
                return await self.generate_text(prompt, system_prompt, **kwargs)
            except Exception as e:
                last_error = e
                logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        logger.error(f"All {max_retries} attempts failed")
        raise last_error

    # =========================================================================
    # High-level Analysis Methods (replacing GeminiService functionality)
    # =========================================================================

    async def analyze_company(self, company_name: str, company_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Perform comprehensive company analysis
        """
        context = ""
        if company_data:
            context = f"""
Company Data:
- Industry: {company_data.get('industry', 'Unknown')}
- Description: {company_data.get('description', 'No description')}
- Location: {company_data.get('location', 'Unknown')}
- Founded: {company_data.get('founded_year', 'Unknown')}
- Stage: {company_data.get('stage', 'Unknown')}
"""
        
        prompt = f"""Analyze the company "{company_name}" and provide comprehensive insights.

{context}

Provide analysis in the following JSON format:
{{
    "overview": "2-3 sentence company overview",
    "industry_analysis": "Industry position and trends",
    "competitive_advantages": ["advantage 1", "advantage 2", "advantage 3"],
    "challenges": ["challenge 1", "challenge 2", "challenge 3"],
    "growth_opportunities": ["opportunity 1", "opportunity 2", "opportunity 3"],
    "market_position": "Current market position assessment",
    "strategic_recommendations": ["recommendation 1", "recommendation 2", "recommendation 3"]
}}

Return ONLY valid JSON, no additional text."""

        try:
            response = await self.generate_with_retry(prompt, temperature=0.3)
            
            # Extract JSON
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            logger.warning(f"Failed to parse company analysis JSON: {e}")
        
        return {
            "overview": "Analysis unavailable",
            "industry_analysis": "Please retry for detailed analysis",
            "competitive_advantages": [],
            "challenges": [],
            "growth_opportunities": [],
            "market_position": "Analysis pending",
            "strategic_recommendations": []
        }

    async def discover_competitors(self, company_name: str, industry: str = None) -> List[str]:
        """
        Discover competitors using AI analysis
        """
        prompt = f"""Identify the top 8-10 direct competitors of "{company_name}"{f' in the {industry} industry' if industry else ''}.

Focus on:
1. Companies with similar products/services
2. Same target market
3. Similar business model
4. Direct competitive threats

Return ONLY a JSON array of competitor company names, nothing else:
["Competitor 1", "Competitor 2", "Competitor 3", ...]"""

        try:
            response = await self.generate_with_retry(prompt, temperature=0.3)
            
            # Extract JSON array
            json_match = re.search(r'\[[\s\S]*\]', response)
            if json_match:
                competitors = json.loads(json_match.group())
                return competitors[:10]
        except Exception as e:
            logger.warning(f"Failed to parse competitors JSON: {e}")
        
        return []

    async def generate_swot_analysis(self, company_name: str, company_data: Dict[str, Any] = None) -> Dict[str, List[str]]:
        """
        Generate SWOT analysis for a company
        """
        context = ""
        if company_data:
            context = f"""
Industry: {company_data.get('industry', 'Unknown')}
Stage: {company_data.get('stage', 'Unknown')}
Description: {company_data.get('description', '')}
"""
        
        prompt = f"""Generate a comprehensive SWOT analysis for "{company_name}".
{context}

Return JSON:
{{
    "strengths": ["strength 1", "strength 2", "strength 3", "strength 4"],
    "weaknesses": ["weakness 1", "weakness 2", "weakness 3", "weakness 4"],
    "opportunities": ["opportunity 1", "opportunity 2", "opportunity 3", "opportunity 4"],
    "threats": ["threat 1", "threat 2", "threat 3", "threat 4"]
}}

Each item should be specific and actionable. Return ONLY valid JSON."""

        try:
            response = await self.generate_with_retry(prompt, temperature=0.3)
            
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            logger.warning(f"Failed to parse SWOT JSON: {e}")
        
        return {
            "strengths": ["Analysis Unavailable"],
            "weaknesses": [],
            "opportunities": [],
            "threats": []
        }

    async def chat(self, message: str, session_id: str = "default") -> str:
        """
        Chat interface with conversation memory
        """
        system_context = """You are Nexalyze AI, an expert business intelligence assistant specializing in:
- Startup and company analysis
- Competitive intelligence
- Market research
- Funding and investment analysis
- Industry trends and insights

Provide accurate, data-driven insights. Be concise but comprehensive.
If you don't have specific data, say so and provide general guidance."""

        # Retrieve history
        history = self.chat_sessions.get(session_id, [])
        
        # Build messages including history
        messages = []
        messages.append(SystemMessage(content=system_context))
        for msg in history:
            messages.append(msg)
        
        messages.append(HumanMessage(content=message))
        
        try:
            # Use chat model directly to maintain state if we were using it that way, 
            # but here we are managing state manually.
            logger.debug(f"Chatting with session {session_id}, history length: {len(history)}")
            
            response = await self.chat_model.ainvoke(messages)
            
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Update history
            history.append(HumanMessage(content=message))
            history.append(AIMessage(content=content))
            
            # Limit history to last 10 turns (20 messages) to prevent context overflow
            if len(history) > 20:
                history = history[-20:]
            
            self.chat_sessions[session_id] = history
            return content
            
        except Exception as e:
            logger.error(f"Chat failed: {e}")
            return "I apologize, but I'm having trouble processing your request right now. Please try again."

    def clear_chat_session(self, session_id: str):
        """Clear a chat session's history"""
        if session_id in self.chat_sessions:
            del self.chat_sessions[session_id]
            logger.info(f"Cleared chat session: {session_id}")
    
    def get_chat_model(self) -> ChatBedrockConverse:
        """Get the ChatBedrockConverse instance for use with LangChain/LangGraph"""
        return self.chat_model
    
    def create_chat_model_with_params(
        self,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> ChatBedrockConverse:
        """Create a new ChatBedrockConverse instance with custom parameters"""
        return ChatBedrockConverse(
            client=self.bedrock_client,
            model=self.model_id,
            temperature=temperature if temperature is not None else self.temperature,
            max_tokens=max_tokens if max_tokens is not None else self.max_tokens,
        )


# Global instance
_bedrock_service: Optional[BedrockService] = None


def get_bedrock_service() -> BedrockService:
    """
    Get or create the global Bedrock service instance
    """
    global _bedrock_service
    
    if _bedrock_service is None:
        _bedrock_service = BedrockService()
    
    return _bedrock_service

# Async wrapper functions for easy use (Backward compatibility with Gemini wrappers)

async def generate_ai_response(prompt: str, temperature: float = 0.3) -> str:
    """Quick helper to generate AI response"""
    service = get_bedrock_service()
    return await service.generate_text(prompt, temperature=temperature)


async def analyze_company_with_ai(company_name: str, company_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """Quick helper to analyze a company"""
    service = get_bedrock_service()
    return await service.analyze_company(company_name, company_data)


async def discover_competitors_with_ai(company_name: str, industry: str = None) -> List[str]:
    """Quick helper to discover competitors"""
    service = get_bedrock_service()
    return await service.discover_competitors(company_name, industry)
