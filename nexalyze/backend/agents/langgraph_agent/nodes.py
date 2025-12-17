"""
LangGraph Nodes - Agent and tool execution nodes
"""
from typing import Dict, Any
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.prebuilt import ToolNode
from agents.langgraph_agent.state import AgentState
from agents.langgraph_agent.tools import get_all_tools
from agents.langgraph_agent.utils import (
    truncate_tool_messages,
    estimate_context_usage,
    count_tokens_accurate
)

from config.settings import settings
import logging
import asyncio
import re

logger = logging.getLogger(__name__)

# System prompt for the conversational agent
SYSTEM_PROMPT = """You are Nexalyze, an AI-powered assistant specialized in startup research, competitive intelligence, and market analysis.

Your capabilities include:
1. **Company Search**: Find companies by name, industry, location, or description
2. **Company Analysis**: Provide comprehensive analysis of specific companies including competitive landscape
3. **Knowledge Graphs**: Show business relationships, dependencies, competitors, opportunities, and risks
4. **Report Generation**: Create detailed reports (comprehensive, executive, detailed, market overview, competitive analysis)
5. **Statistics**: Provide database statistics and insights

**Guidelines:**
- Be helpful, accurate, and concise
- Use tools when you need specific data or to perform actions
- Provide actionable insights based on data
- Format responses in clear markdown
- If you don't have enough information, use the appropriate tools to gather it
- Always cite sources when providing data

**Tool Usage:**
- Use `search_companies` to find companies matching criteria
- Use `analyze_company` for detailed company analysis
- Use `get_knowledge_graph` to show company relationships
- Use `generate_report` to create comprehensive reports
- Use `get_company_statistics` for database metrics

Remember: You have access to a database of thousands of companies. Use tools to access this data when needed."""


from services.bedrock_service import get_bedrock_service

# Get Bedrock service for LLM
bedrock_service = get_bedrock_service()

async def agent_node(state: AgentState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Main agent node that processes user queries and decides on tool usage.
    """
    messages = state.get("messages", [])
    session_id = state.get("session_id", "default")
    iteration_count = state.get("iteration_count", 0)
    
    logger.info(f"Agent node processing for session {session_id}, iteration {iteration_count}")
    
    # Truncate large tool outputs before processing
    messages = truncate_tool_messages(messages)
    
    # Count tool messages for context management
    tool_message_count = sum(1 for m in messages if hasattr(m, 'type') and getattr(m, 'type', None) == 'tool')
    human_message_count = sum(1 for m in messages if hasattr(m, 'type') and getattr(m, 'type', None) == 'human')
    
    logger.info(f"Message counts - Human: {human_message_count}, Tool: {tool_message_count}, Total: {len(messages)}")
    
    # Prepare system message
    system_message = SystemMessage(content=SYSTEM_PROMPT)
    
    # Get tools and bind them to the model
    tools = get_all_tools()
    llm = bedrock_service.get_chat_model()
    llm_with_tools = llm.bind_tools(tools)
    
    # Prepare messages for LLM (prepend system message)
    # Filter out system messages from history to avoid duplication if one exists
    history_messages = [m for m in messages if not isinstance(m, SystemMessage)]
    # Ensure the first message is the system message
    final_messages = [system_message] + history_messages
    
    try:
        # Invoke LLM
        response = await llm_with_tools.ainvoke(final_messages)
        
        # Increment iteration count
        new_iteration_count = iteration_count + 1
        
        return {
            "messages": [response],
            "iteration_count": new_iteration_count
        }
        
    except Exception as e:
        logger.error(f"Agent node failed: {e}")
        import traceback
        traceback.print_exc()
        error_message = AIMessage(
            content=f"I encountered an error processing your request: {str(e)}. Please try rephrasing your question."
        )
        return {
            "messages": [error_message],
            "iteration_count": iteration_count + 1
        }



async def tools_node(state: AgentState) -> Dict[str, Any]:
    """
    Tool execution node that runs tools requested by the agent.
    """
    messages = state.get("messages", [])
    last_message = messages[-1] if messages else None
    
    if not last_message or not hasattr(last_message, 'tool_calls') or not last_message.tool_calls:
        logger.warning("Tools node called but no tool calls found")
        return {"messages": []}
    
    logger.info(f"Executing {len(last_message.tool_calls)} tool call(s)")
    
    # Get all tools
    tools = get_all_tools()
    tool_map = {tool.name: tool for tool in tools}
    
    # Execute tools
    tool_messages = []
    tool_calls = last_message.tool_calls if hasattr(last_message, 'tool_calls') else []
    
    if not tool_calls:
        # Try to extract from content if tool_calls attribute doesn't exist
        import re
        content = str(last_message.content) if hasattr(last_message, 'content') else ""
        tool_call_pattern = r'TOOL_CALL:\s*(\w+)\s*\(([^)]+)\)'
        matches = re.findall(tool_call_pattern, content)
        
        if matches:
            for tool_name, args_str in matches:
                args = {}
                arg_matches = re.findall(r'(\w+)="([^"]+)"', args_str)
                for key, value in arg_matches:
                    args[key] = value
                
                tool_calls.append({
                    'name': tool_name,
                    'args': args,
                    'id': f"{tool_name}_{len(tool_calls)}"
                })
    
    for tool_call in tool_calls:
        tool_name = tool_call.get('name') if isinstance(tool_call, dict) else getattr(tool_call, 'name', None)
        tool_args = tool_call.get('args', {}) if isinstance(tool_call, dict) else {}
        
        if not tool_name:
            continue
            
        if tool_name in tool_map:
            try:
                logger.info(f"Executing tool: {tool_name} with args: {tool_args}")
                tool = tool_map[tool_name]
                
                # Execute the tool - handle different tool types
                # LangChain tools may have .func, .run, or .invoke methods
                if hasattr(tool, 'func') and tool.func is not None:
                    # Direct function access
                    if asyncio.iscoroutinefunction(tool.func):
                        result = await tool.func(**tool_args)
                    else:
                        result = tool.func(**tool_args)
                elif hasattr(tool, 'ainvoke'):
                    # Async invoke for structured tools
                    result = await tool.ainvoke(tool_args)
                elif hasattr(tool, 'invoke'):
                    # Sync invoke for structured tools
                    result = tool.invoke(tool_args)
                elif hasattr(tool, 'arun'):
                    # Async run for legacy tools
                    result = await tool.arun(**tool_args)
                elif hasattr(tool, 'run'):
                    # Sync run for legacy tools
                    result = tool.run(**tool_args)
                else:
                    # Last resort: try calling the tool directly
                    if asyncio.iscoroutinefunction(tool):
                        result = await tool(**tool_args)
                    else:
                        result = tool(**tool_args)
                
                # Create tool message
                from langchain_core.messages import ToolMessage
                tool_message = ToolMessage(
                    content=str(result),
                    tool_call_id=tool_call.get('id', f"{tool_name}_{len(tool_messages)}"),
                    name=tool_name
                )
                tool_messages.append(tool_message)
                logger.info(f"Tool {tool_name} executed successfully")
                
            except Exception as e:
                logger.error(f"Tool {tool_name} execution failed: {e}")
                import traceback
                traceback.print_exc()
                from langchain_core.messages import ToolMessage
                error_message = ToolMessage(
                    content=f"Error executing {tool_name}: {str(e)}",
                    tool_call_id=tool_call.get('id', f"{tool_name}_{len(tool_messages)}"),
                    name=tool_name
                )
                tool_messages.append(error_message)
        else:
            logger.warning(f"Tool {tool_name} not found in available tools")
            from langchain_core.messages import ToolMessage
            error_message = ToolMessage(
                content=f"Tool {tool_name} is not available. Available tools: {list(tool_map.keys())}",
                tool_call_id=tool_call.get('id', f"{tool_name}_{len(tool_messages)}"),
                name=tool_name
            )
            tool_messages.append(error_message)
    
    return {"messages": tool_messages}

