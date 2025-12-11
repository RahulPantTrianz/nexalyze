"""
Utility functions for LangGraph agent
"""
import tiktoken
from typing import List
from langchain_core.messages import BaseMessage, ToolMessage, AIMessage
import logging

logger = logging.getLogger(__name__)

# Constants for context management
MAX_TOOL_OUTPUT_CHARS = 3000
MAX_TOOL_OUTPUT_TOKENS = 750
TOKENIZER_SAFETY_MARGIN = 0.85
TOOL_OUTPUT_TRUNCATION_SUFFIX = "\n\n[Output truncated to save context. Full result was shown above.]"


def count_tokens_accurate(text: str, model: str = "gpt-4") -> int:
    """
    Count tokens accurately using tiktoken.
    
    Args:
        text: Text to count tokens for
        model: Model name for tokenizer (default: gpt-4)
    
    Returns:
        Number of tokens
    """
    try:
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(str(text)))
    except Exception as e:
        logger.warning(f"Token counting failed, using estimate: {e}")
        # Fallback: rough estimate (1 token ≈ 4 characters)
        return len(str(text)) // 4


def truncate_tool_output(content: str, max_chars: int = MAX_TOOL_OUTPUT_CHARS) -> str:
    """
    Truncate tool output to prevent massive context accumulation.
    Preserves the beginning (usually most relevant) and adds truncation notice.
    """
    if not content or len(content) <= max_chars:
        return content
    
    truncated = content[:max_chars - len(TOOL_OUTPUT_TRUNCATION_SUFFIX)]
    return truncated + TOOL_OUTPUT_TRUNCATION_SUFFIX


def truncate_tool_messages(messages: List[BaseMessage]) -> List[BaseMessage]:
    """
    Create a copy of messages with truncated tool outputs.
    This reduces context size while preserving message structure.
    """
    truncated_messages = []
    truncated_count = 0
    
    for msg in messages:
        if isinstance(msg, ToolMessage):
            content = getattr(msg, 'content', '')
            if isinstance(content, str) and len(content) > MAX_TOOL_OUTPUT_CHARS:
                truncated_content = truncate_tool_output(content)
                truncated_msg = ToolMessage(
                    content=truncated_content,
                    tool_call_id=msg.tool_call_id,
                    name=getattr(msg, 'name', None),
                    id=getattr(msg, 'id', None),
                )
                truncated_messages.append(truncated_msg)
                truncated_count += 1
            else:
                truncated_messages.append(msg)
        elif isinstance(msg, AIMessage) and hasattr(msg, 'content'):
            content = msg.content
            if isinstance(content, str) and len(content) > MAX_TOOL_OUTPUT_CHARS * 2:
                truncated_content = truncate_tool_output(content, MAX_TOOL_OUTPUT_CHARS * 2)
                truncated_msg = AIMessage(
                    content=truncated_content,
                    tool_calls=getattr(msg, 'tool_calls', []),
                    id=getattr(msg, 'id', None),
                )
                truncated_messages.append(truncated_msg)
                truncated_count += 1
            else:
                truncated_messages.append(msg)
        else:
            truncated_messages.append(msg)
    
    if truncated_count > 0:
        logger.info(f"Truncated {truncated_count} messages with large outputs")
    
    return truncated_messages


def estimate_context_usage(messages: List[BaseMessage], system_prompt: str = "") -> dict:
    """
    Estimate context window usage.
    
    Returns:
        Dictionary with token counts and percentages
    """
    system_tokens = count_tokens_accurate(system_prompt) if system_prompt else 0
    
    # Count tokens in messages
    message_texts = []
    for msg in messages:
        if hasattr(msg, 'content'):
            message_texts.append(str(msg.content))
    
    message_text = "\n".join(message_texts)
    message_tokens = count_tokens_accurate(message_text)
    
    total_input_tokens = system_tokens + message_tokens
    
    # Model context limits (using Gemini 1.5 Flash as default)
    total_context = 1000000  # 1M context for Gemini 1.5 Flash
    output_buffer = 10000  # Reserve for output
    max_input_tokens = int((total_context - output_buffer) * TOKENIZER_SAFETY_MARGIN)
    
    return {
        "system_tokens": system_tokens,
        "message_tokens": message_tokens,
        "total_input_tokens": total_input_tokens,
        "max_input_tokens": max_input_tokens,
        "usage_percentage": (total_input_tokens / max_input_tokens * 100) if max_input_tokens > 0 else 0,
        "total_context": total_context
    }

