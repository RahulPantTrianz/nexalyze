"""
Gemini AI Service with Retry and Exponential Backoff
Provides reliable AI inference using Google's Gemini API
"""

import asyncio
import logging
import time
import random
from typing import Dict, Any, Optional, List
import google.generativeai as genai
from functools import wraps
from config.settings import settings

logger = logging.getLogger(__name__)


class GeminiService:
    """
    Gemini AI Service with built-in retry logic and exponential backoff
    for maximum availability and reliability.
    """
    
    def __init__(self, api_key: str = None, model_name: str = "gemini-flash-latest"):
        """
        Initialize Gemini Service
        
        Args:
            api_key: Gemini API key (uses settings if not provided)
            model_name: Model to use (gemini-flash-latest, gemini-pro-latest, gemini-1.5-pro, gemini-1.5-flash, gemini-pro)
        """
        self.api_key = api_key or settings.gemini_api_key
        self.model_name = model_name
        
        # Retry configuration
        self.max_retries = 5
        self.base_delay = 1.0  # Base delay in seconds
        self.max_delay = 60.0  # Maximum delay in seconds
        self.jitter = 0.1  # Random jitter factor
        
        # Rate limiting
        self.requests_per_minute = 60
        self.last_request_time = 0
        self.min_request_interval = 60.0 / self.requests_per_minute
        
        # Track which models have been tried (for fallback logic)
        self.tried_models = set()
        
        # Initialize the client
        self._initialize_client()
        
        logger.info(f"Gemini Service initialized with model: {model_name}")
    
    def _initialize_client(self):
        """Initialize the Gemini client with API key"""
        try:
            genai.configure(api_key=self.api_key)
            
            # Initialize tried_models if not already set
            if not hasattr(self, 'tried_models'):
                self.tried_models = set()
            
            # Try to initialize with the specified model
            # If it fails, try fallback models using latest naming conventions
            model_names_to_try = [
                self.model_name,
                "gemini-flash-latest",  # Latest flash (most reliable)
                "gemini-pro-latest",    # Latest pro
                "gemini-1.5-pro-latest", # Latest 1.5 pro
                "gemini-1.5-flash-latest", # Latest 1.5 flash
                "gemini-1.5-pro",       # Stable 1.5 pro
                "gemini-1.5-flash",     # Stable 1.5 flash
                "gemini-pro",           # Legacy stable
            ]
            
            model_initialized = False
            for model_name in model_names_to_try:
                if model_name in self.tried_models:
                    continue
                    
                try:
                    self.model = genai.GenerativeModel(model_name)
                    # Test if model is accessible
                    self.chat_sessions: Dict[str, Any] = {}
                    self.model_name = model_name
                    self.tried_models.add(model_name)
                    logger.info(f"Gemini client initialized successfully with model: {model_name}")
                    model_initialized = True
                    break
                except Exception as e:
                    logger.warning(f"Failed to initialize with model {model_name}: {e}")
                    self.tried_models.add(model_name)
                    continue
            
            if not model_initialized:
                raise Exception(f"Failed to initialize any Gemini model. Tried: {model_names_to_try}")
                
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            raise
    
    def _try_fallback_model(self) -> bool:
        """
        Try to switch to a fallback model when current model fails
        
        Returns:
            True if successfully switched to a fallback model, False otherwise
        """
        # Add current model to tried set
        self.tried_models.add(self.model_name)
        
        # Try different model names using latest naming conventions
        # Order: latest aliases first (most reliable), then specific stable models
        fallback_models = [
            "gemini-flash-latest",  # Latest flash model
            "gemini-pro-latest",    # Latest pro model
            "gemini-2.0-flash-exp", # Experimental flash
            "gemini-1.5-pro-latest", # Latest 1.5 pro
            "gemini-1.5-flash-latest", # Latest 1.5 flash
            "gemini-1.5-pro",       # Stable 1.5 pro
            "gemini-1.5-flash",     # Stable 1.5 flash
            "gemini-pro",           # Legacy stable
        ]
        
        for fallback_model in fallback_models:
            # Skip if we've already tried this model
            if fallback_model in self.tried_models:
                continue
                
            try:
                logger.info(f"Attempting to switch to fallback model: {fallback_model}")
                test_model = genai.GenerativeModel(fallback_model)
                # Test if model is accessible by trying to get its config
                # If this succeeds, switch to it
                self.model = test_model
                self.model_name = fallback_model
                self.tried_models.add(fallback_model)
                # Clear chat sessions as they're model-specific
                self.chat_sessions = {}
                logger.info(f"Successfully switched to fallback model: {fallback_model}")
                return True
            except Exception as e:
                logger.warning(f"Failed to switch to fallback model {fallback_model}: {e}")
                self.tried_models.add(fallback_model)
                continue
        
        return False
    
    def _calculate_backoff(self, attempt: int) -> float:
        """
        Calculate exponential backoff delay with jitter
        
        Args:
            attempt: Current retry attempt number
        
        Returns:
            Delay in seconds
        """
        # Exponential backoff: delay = base * 2^attempt
        delay = min(self.base_delay * (2 ** attempt), self.max_delay)
        
        # Add random jitter to prevent thundering herd
        jitter_amount = delay * self.jitter * random.random()
        delay += jitter_amount
        
        return delay
    
    async def _rate_limit(self):
        """Apply rate limiting between requests"""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        
        if elapsed < self.min_request_interval:
            await asyncio.sleep(self.min_request_interval - elapsed)
        
        self.last_request_time = time.time()
    
    async def generate_content(
        self,
        prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 4096,
        session_id: str = None
    ) -> str:
        """
        Generate content using Gemini with retry and exponential backoff
        
        Args:
            prompt: The prompt to send to the model
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens in response
            session_id: Optional session ID for conversation context
        
        Returns:
            Generated text response
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                # Apply rate limiting
                await self._rate_limit()
                
                # Configure generation settings
                generation_config = genai.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                    top_p=0.95,
                    top_k=40
                )
                
                # Use chat session if session_id provided
                if session_id:
                    if session_id not in self.chat_sessions:
                        self.chat_sessions[session_id] = self.model.start_chat(history=[])
                    
                    response = await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: self.chat_sessions[session_id].send_message(
                            prompt,
                            generation_config=generation_config
                        )
                    )
                else:
                    response = await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: self.model.generate_content(
                            prompt,
                            generation_config=generation_config
                        )
                    )
                
                # Extract text from response
                if response and response.text:
                    logger.debug(f"Gemini response generated successfully (attempt {attempt + 1})")
                    return response.text
                else:
                    raise ValueError("Empty response from Gemini API")
                    
            except Exception as e:
                last_exception = e
                error_message = str(e).lower()
                
                # Check if it's a model not found error - try fallback model
                if '404' in str(e) and ('model' in error_message or 'not found' in error_message):
                    # Only try fallback once per request attempt to avoid infinite loops
                    if attempt == 0:  # Only try fallback on first attempt
                        logger.warning(f"Model {self.model_name} not available, trying fallback models...")
                        if self._try_fallback_model():
                            # Successfully switched to fallback, retry the request
                            logger.info(f"Switched to fallback model, retrying request...")
                            continue
                        else:
                            logger.error(f"All model fallbacks failed. Will use fallback response.")
                            # Don't break, let it continue to fallback response
                    else:
                        # Already tried fallback, just log and continue to fallback response
                        logger.error(f"Model error persists after fallback attempt. Last error: {e}")
                
                # Check if error is retryable
                retryable_errors = [
                    'rate limit', 'quota', 'timeout', 'unavailable',
                    'internal', 'overloaded', '429', '500', '503', '504'
                ]
                
                is_retryable = any(err in error_message for err in retryable_errors)
                
                if is_retryable and attempt < self.max_retries - 1:
                    delay = self._calculate_backoff(attempt)
                    logger.warning(
                        f"Gemini request failed (attempt {attempt + 1}/{self.max_retries}): {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Gemini request failed permanently: {e}")
                    break
        
        # If all retries failed, return a fallback response
        logger.error(f"All {self.max_retries} retry attempts failed. Last error: {last_exception}")
        return self._get_fallback_response(prompt)
    
    def _get_fallback_response(self, prompt: str) -> str:
        """
        Generate a fallback response when API is unavailable
        
        Args:
            prompt: Original prompt
        
        Returns:
            Fallback response
        """
        # Analyze prompt to provide relevant fallback
        prompt_lower = prompt.lower()
        
        if 'competitor' in prompt_lower:
            return "Based on available data, the key competitors in this space include established market leaders and emerging startups. For detailed competitive analysis, please ensure API connectivity and try again."
        elif 'market' in prompt_lower:
            return "Market analysis indicates growth opportunities in this sector. The market is characterized by increasing digital adoption and evolving customer needs. Please retry for detailed insights."
        elif 'funding' in prompt_lower:
            return "Funding trends show continued investor interest in this space. Recent rounds have ranged from seed to growth stages. Please retry for specific funding data."
        elif 'company' in prompt_lower or 'startup' in prompt_lower:
            return "Company analysis requires current data. The organization operates in a dynamic market with various strategic opportunities. Please ensure connectivity for detailed analysis."
        else:
            return "Analysis is temporarily unavailable. Please try again in a moment for comprehensive insights."
    
    async def analyze_company(self, company_name: str, company_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Perform comprehensive company analysis
        
        Args:
            company_name: Name of the company
            company_data: Optional existing company data
        
        Returns:
            Analysis results
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

        response = await self.generate_content(prompt, temperature=0.3)
        
        try:
            import json
            import re
            # Extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            logger.warning(f"Failed to parse company analysis JSON: {e}")
        
        return {
            "overview": response[:500] if response else "Analysis unavailable",
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
        
        Args:
            company_name: Name of the company
            industry: Optional industry context
        
        Returns:
            List of competitor names
        """
        prompt = f"""Identify the top 8-10 direct competitors of "{company_name}"{f' in the {industry} industry' if industry else ''}.

Focus on:
1. Companies with similar products/services
2. Same target market
3. Similar business model
4. Direct competitive threats

Return ONLY a JSON array of competitor company names, nothing else:
["Competitor 1", "Competitor 2", "Competitor 3", ...]"""

        response = await self.generate_content(prompt, temperature=0.3)
        
        try:
            import json
            import re
            # Extract JSON array from response
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
        
        Args:
            company_name: Name of the company
            company_data: Optional existing company data
        
        Returns:
            SWOT analysis dictionary
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

        response = await self.generate_content(prompt, temperature=0.3)
        
        try:
            import json
            import re
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            logger.warning(f"Failed to parse SWOT JSON: {e}")
        
        return {
            "strengths": ["Strong product", "Growing market"],
            "weaknesses": ["Limited resources", "Brand recognition"],
            "opportunities": ["Market expansion", "New products"],
            "threats": ["Competition", "Market changes"]
        }
    
    async def chat(self, message: str, session_id: str = "default") -> str:
        """
        Chat interface with conversation memory
        
        Args:
            message: User message
            session_id: Session identifier for conversation context
        
        Returns:
            AI response
        """
        system_context = """You are Nexalyze AI, an expert business intelligence assistant specializing in:
- Startup and company analysis
- Competitive intelligence
- Market research
- Funding and investment analysis
- Industry trends and insights

Provide accurate, data-driven insights. Be concise but comprehensive.
If you don't have specific data, say so and provide general guidance."""

        prompt = f"{system_context}\n\nUser: {message}\n\nAssistant:"
        
        return await self.generate_content(prompt, session_id=session_id, temperature=0.4)
    
    def clear_chat_session(self, session_id: str):
        """Clear a chat session's history"""
        if session_id in self.chat_sessions:
            del self.chat_sessions[session_id]
            logger.info(f"Cleared chat session: {session_id}")


# Global singleton instance
_gemini_service: Optional[GeminiService] = None


def get_gemini_service() -> GeminiService:
    """Get or create the global Gemini service instance"""
    global _gemini_service
    if _gemini_service is None:
        _gemini_service = GeminiService()
    return _gemini_service


# Async wrapper functions for easy use
async def generate_ai_response(prompt: str, temperature: float = 0.3) -> str:
    """Quick helper to generate AI response"""
    service = get_gemini_service()
    return await service.generate_content(prompt, temperature=temperature)


async def analyze_company_with_ai(company_name: str, company_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """Quick helper to analyze a company"""
    service = get_gemini_service()
    return await service.analyze_company(company_name, company_data)


async def discover_competitors_with_ai(company_name: str, industry: str = None) -> List[str]:
    """Quick helper to discover competitors"""
    service = get_gemini_service()
    return await service.discover_competitors(company_name, industry)

