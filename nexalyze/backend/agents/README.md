# LangGraph Agents Implementation

This directory contains the LangGraph-based agent implementations for Nexalyze.

## Structure

### Conversational Agent (`langgraph_agent/`)
- **State Management** (`state.py`): Defines the agent state with messages, session tracking, and context
- **Nodes** (`nodes.py`): Agent and tool execution nodes
- **Edges** (`edges.py`): Routing logic for tool calls vs. end conversation
- **Tools** (`tools.py`): Available tools for the agent:
  - `search_companies`: Search companies in the database
  - `analyze_company`: Comprehensive company analysis
  - `get_knowledge_graph`: Get company knowledge graph
  - `generate_report`: Generate comprehensive reports
  - `get_company_statistics`: Get database statistics
- **Utils** (`utils.py`): Context window management, token counting, message truncation
- **Graph** (`graph.py`): Main workflow definition and compilation

### Report Generation Agent (`report_agent/`)
- **State Management** (`state.py`): Report generation state with content table and sections
- **Nodes** (`nodes.py`): 
  - Content table creation
  - Report section generation
  - Background report compilation
- **Edges** (`edges.py`): Routing for report generation workflow
- **Graph** (`graph.py`): Report generation workflow

## Features

### Conversational Agent
- **Tool-based interactions**: Agent can use tools to search, analyze, and generate reports
- **Context management**: Automatic message truncation and token counting
- **State persistence**: Conversation state is maintained across requests
- **Iteration limiting**: Prevents infinite loops (max 10 iterations)

### Report Generation Agent
- **Multi-stage workflow**: Content table → Section generation → Report compilation
- **Flexible report types**: Comprehensive, executive, detailed, market overview, competitive analysis
- **Background processing**: Non-blocking report generation

## API Integration

The agents are integrated into the existing API routes:

- `/api/v1/chat`: Uses LangGraph conversational agent
- `/api/v1/chat/stream`: Streaming version with SSE
- `/api/v1/generate-comprehensive-report`: Uses LangGraph report agent (with fallback)

## Usage

### Conversational Agent
```python
from agents.langgraph_agent import get_conversational_agent_graph
from langchain_core.messages import HumanMessage

graph = get_conversational_agent_graph()
state = {
    "messages": [HumanMessage(content="Find AI companies in San Francisco")],
    "session_id": "session_123",
    "user_query": "Find AI companies in San Francisco",
    "context": {},
    "tools_used": [],
    "iteration_count": 0
}
result = await graph.ainvoke(state, config={"configurable": {"thread_id": "session_123"}})
```

### Report Generation Agent
```python
from agents.report_agent import get_report_agent_graph
from langchain_core.messages import HumanMessage

graph = get_report_agent_graph()
state = {
    "messages": [HumanMessage(content="Generate comprehensive report on AI startups")],
    "session_id": "report_123",
    "topic": "AI startups",
    "report_type": "comprehensive",
    "content_table": None,
    "current_section": None,
    "report_sections": [],
    "status": "drafting"
}
result = await graph.ainvoke(state, config={"configurable": {"thread_id": "report_123"}})
```

## Dependencies

- `langgraph>=0.2.0`: LangGraph framework
- `langchain>=0.2.0`: LangChain core
- `langchain-core>=0.2.0`: LangChain core components
- `tiktoken>=0.5.0`: Token counting for context management

## Notes

- The conversational agent uses a simple tool calling format (`TOOL_CALL: tool_name(args)`) since Gemini's native function calling requires additional setup
- Context window management automatically truncates large tool outputs
- State persistence uses in-memory checkpointer (can be upgraded to Redis/PostgreSQL for production)

