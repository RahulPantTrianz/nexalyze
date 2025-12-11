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
from services.gemini_service import get_gemini_service
from config.settings import settings
import logging
import asyncio
import re

logger = logging.getLogger(__name__)

# Get Gemini service for LLM
gemini_service = get_gemini_service()

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
    
    # Estimate context usage
    context_stats = estimate_context_usage(messages, SYSTEM_PROMPT)
    logger.info(f"Context usage: {context_stats['total_input_tokens']:,} / {context_stats['max_input_tokens']:,} tokens "
                f"({context_stats['usage_percentage']:.1f}%)")
    
    # Prepare messages for LLM
    current_messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        *messages
    ]
    
    # Get all available tools
    tools = get_all_tools()
    logger.info(f"Agent has access to {len(tools)} tools: {[tool.name for tool in tools]}")
    
    # Prepare prompt with tool descriptions
    tools_description = "\n\nAvailable tools:\n"
    for tool in tools:
        tools_description += f"- {tool.name}: {tool.description}\n"
    
    # Build conversation history for Gemini
    conversation_text = ""
    for msg in messages[-10:]:  # Last 10 messages for context
        if hasattr(msg, 'type'):
            if msg.type == 'human':
                conversation_text += f"User: {msg.content}\n\n"
            elif msg.type == 'ai':
                conversation_text += f"Assistant: {msg.content}\n\n"
            elif msg.type == 'tool':
                conversation_text += f"Tool Result ({getattr(msg, 'name', 'tool')}): {msg.content[:500]}...\n\n"
    
    # Create enhanced prompt with tools
    enhanced_prompt = f"""{SYSTEM_PROMPT}

{tools_description}

Conversation History:
{conversation_text}

Current User Query: {messages[-1].content if messages else 'No query'}

Instructions:
1. If you need to use a tool, respond with: TOOL_CALL: tool_name(arg1="value1", arg2="value2")
2. You can call multiple tools by separating with newlines
3. If no tool is needed, provide a direct answer
4. Format tool calls exactly as shown above

Response:"""
    
    # Use Gemini service for LLM
    try:
        response_text = await gemini_service.chat(
            message=enhanced_prompt,
            session_id=session_id
        )
        
        # Parse response for tool calls
        tool_calls = []
        content = response_text
        
        # Check if response contains tool calls
        import re
        tool_call_pattern = r'TOOL_CALL:\s*(\w+)\s*\(([^)]+)\)'
        matches = re.findall(tool_call_pattern, response_text)
        
        if matches:
            # Extract tool calls
            for tool_name, args_str in matches:
                # Parse arguments (simple key=value parsing)
                args = {}
                arg_matches = re.findall(r'(\w+)="([^"]+)"', args_str)
                for key, value in arg_matches:
                    args[key] = value
                
                tool_calls.append({
                    'name': tool_name,
                    'args': args,
                    'id': f"{tool_name}_{len(tool_calls)}"
                })
            
            # Remove tool call markers from content
            content = re.sub(tool_call_pattern, '', response_text).strip()
        
        # Create AI message
        ai_message = AIMessage(content=content)
        if tool_calls:
            # Store tool calls in a way LangGraph can use
            ai_message.tool_calls = tool_calls
            logger.info(f"Agent requested {len(tool_calls)} tool call(s)")
        
        # Increment iteration count
        new_iteration_count = iteration_count + 1
        
        return {
            "messages": [ai_message],
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

