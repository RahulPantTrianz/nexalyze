"""
AWS Bedrock Service for LLM inference using Claude Sonnet 4.5
"""
import os
import logging
from typing import Optional, Dict, Any, List
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError, ProfileNotFound
from langchain_aws import ChatBedrockConverse
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

logger = logging.getLogger(__name__)


class BedrockService:
    """Service for interacting with AWS Bedrock Claude models"""
    
    def __init__(
        self,
        model_id: str = "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
        aws_profile: str = "amplify",
        region_name: str = "us-east-1",
        temperature: float = 0.7,
        max_tokens: int = 4096
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
        self.model_id = model_id
        self.aws_profile = aws_profile
        self.region_name = region_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # Initialize boto3 session with profile
        try:
            self.session = boto3.Session(profile_name=aws_profile)
            logger.info(f"Initialized AWS session with profile: {aws_profile}")
        except ProfileNotFound:
            logger.warning(f"Profile '{aws_profile}' not found, falling back to default credentials.")
            self.session = boto3.Session()
        except Exception as e:
            logger.warning(f"Failed to use profile '{aws_profile}', using default credentials: {e}")
            self.session = boto3.Session()
        
        # Create Bedrock client
        config = Config(
            region_name=region_name,
            retries={'max_attempts': 3, 'mode': 'adaptive'}
        )
        
        self.bedrock_client = self.session.client(
            service_name='bedrock-runtime',
            config=config
        )
        
        logger.info(f"Bedrock client initialized for region: {region_name}")
        
        # Initialize ChatBedrockConverse
        self._init_chat_model()
    
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
            # Update model parameters if overridden
            if temperature is not None or max_tokens is not None:
                self.chat_model = ChatBedrockConverse(
                    client=self.bedrock_client,
                    model=self.model_id,
                    temperature=temperature if temperature is not None else self.temperature,
                    max_tokens=max_tokens if max_tokens is not None else self.max_tokens,
                )
            
            # Build messages
            messages = []
            if system_prompt:
                messages.append(SystemMessage(content=system_prompt))
            messages.append(HumanMessage(content=prompt))
            
            # Invoke model
            logger.info(f"Generating text with Claude Sonnet 4.5 (prompt length: {len(prompt)})")
            response = await self.chat_model.ainvoke(messages)
            
            # Extract content
            if hasattr(response, 'content'):
                result = response.content
            else:
                result = str(response)
            
            logger.info(f"Generated {len(result)} characters")
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
    
    def get_chat_model(self) -> ChatBedrockConverse:
        """
        Get the ChatBedrockConverse instance for use with LangChain/LangGraph
        
        Returns:
            ChatBedrockConverse instance
        """
        return self.chat_model
    
    def create_chat_model_with_params(
        self,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> ChatBedrockConverse:
        """
        Create a new ChatBedrockConverse instance with custom parameters
        
        Args:
            temperature: Model temperature
            max_tokens: Maximum tokens
            
        Returns:
            New ChatBedrockConverse instance
        """
        return ChatBedrockConverse(
            client=self.bedrock_client,
            model=self.model_id,
            temperature=temperature if temperature is not None else self.temperature,
            max_tokens=max_tokens if max_tokens is not None else self.max_tokens,
        )


# Global instance
_bedrock_service: Optional[BedrockService] = None


def get_bedrock_service(
    model_id: str = "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
    aws_profile: str = "amplify",
    region_name: str = "us-east-1"
) -> BedrockService:
    """
    Get or create the global Bedrock service instance
    
    Args:
        model_id: Bedrock model ID
        aws_profile: AWS profile name
        region_name: AWS region
        
    Returns:
        BedrockService instance
    """
    global _bedrock_service
    
    if _bedrock_service is None:
        _bedrock_service = BedrockService(
            model_id=model_id,
            aws_profile=aws_profile,
            region_name=region_name
        )
    
    return _bedrock_service
