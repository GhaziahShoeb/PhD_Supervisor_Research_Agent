# Academic Research Coordinator Agent

An advanced multi-agent orchestration system designed to identify academic researchers, validate credentials, and discover graduate programs aligned with specific research interests and academic backgrounds.

## Overview

The Academic Research Coordinator Agent leverages a modular, hierarchical multi-agent architecture to conduct comprehensive academic research. The system autonomously discovers professors, validates their research credentials, and identifies suitable academic programs through specialized subagents coordinated by a central orchestrator.

## Architecture

### Design Patterns

- **Multi-Agent Orchestration**: Hierarchical agent structure with a central lead agent coordinating specialized subagents
- **Deep Agent Framework**: Leverages DeepAgents for complex task decomposition and agent coordination
- **State Machine Graph**: Implements LangGraph for deterministic state transitions and message flow
- **Event Streaming**: Real-time server-sent events for monitoring agent execution progress
- **Asynchronous Processing**: Non-blocking I/O operations throughout the service pipeline

### Agent Structure

**Orchestrator Agent**: `academic-research-lead`
- Coordinates all subagents
- Compiles findings into structured reports
- Maintains message state and context

**Specialized Subagents**:
1. **University-Shortlister**: Identifies top-tier universities based on IT, AI, and QS rankings
2. **Professor-Discovery**: Locates faculty members researching stateful agents and quantum machine learning
3. **Professor-Validator**: Verifies active research funding and PhD admission status
4. **Master's Program Searcher**: Discovers suitable graduate programs based on research interests

## Technology Stack

### Core Frameworks & Libraries

- **LangChain**: Unified interface for LLM interactions and tool management
  - `langchain-core`: Core abstractions and message types
  - `langchain-openai`: OpenAI model integration
  - `langchain-google-genai`: Google Generative AI (Gemini) integration
  - `langchain-community`: Extended tool and integration ecosystem

- **LangGraph**: State machine and agentic workflow orchestration
  - Deterministic control flow
  - Message state management
  - Multi-node execution with configurable streaming

- **DeepAgents**: Advanced multi-agent orchestration framework
  - Hierarchical agent coordination
  - Subagent specialization and management
  - Complex task decomposition

### Web Framework & APIs

- **FastAPI**: Modern async Python web framework for RESTful API design
- **Uvicorn**: ASGI server for production-grade HTTP service deployment
- **Pydantic**: Data validation and type-safe request/response models
- **CORS Middleware**: Cross-origin resource sharing support for frontend integration

### Language Models

- **Google Gemini 2.5 Pro**: Primary LLM with temperature=0 for deterministic inference
- **OpenAI Integration**: Alternative LLM support for fallback and comparison capabilities

### Data Sources & Tools

- **Tavily Search**: Web search capability with async client support
  - Configurable search modes (general, news, finance)
  - Raw content extraction
  - Query validation with keyword enforcement

### Storage & Output

- **Google Cloud Storage (GCS)**: Persistent backend for research outputs
- **Markdown Reporting**: Structured table-format reports for findings
- **JSON Serialization**: Structured data interchange and logging

### Development & Infrastructure

- **Python 3.x**: Primary development language
- **dotenv**: Environment variable management for API keys and configuration
- **asyncio**: Concurrent task execution and event loop management
- **UUID**: Thread identification and request tracking
- **Logging**: Structured logging with configured formatters and handlers

## Key Features

### Real-Time Event Streaming

The API streams agent execution events in Server-Sent Events (SSE) format, enabling real-time frontend updates:
- **connection**: Stream initialization with thread ID
- **agent_active**: Current executing agent notification
- **thought**: Agent reasoning and planning
- **tool_call**: Tool invocation with arguments
- **tool_result**: Tool execution results
- **final**: Completed research report

### Deterministic Inference

LLM temperature set to 0 ensures consistent, reproducible research findings across identical queries.

### Structured Output Generation

Automatic compilation of research findings into professional markdown tables with the following fields:
- University Name
- Professor Name
- Designation
- Email Address
- Research Area
- Active Grants
- Recent Publications
- PhD Opening Status

### Session Management

UUID-based thread management for request tracking, concurrent user handling, and stateful conversation continuity.

### Error Handling & Resilience

- Defensive patching for LangChain compatibility
- Comprehensive exception handling in stream generators
- Query validation to prevent malformed search operations
- Fallback mechanisms for async/sync client operations

## Installation

### Prerequisites

- Python 3.10+
- Google Cloud credentials (for GCS backend)
- Gemini API key
- Tavily API key (for web search)
- OpenAI API key (optional, for fallback LLM)

### Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables:
```bash
export GEMINI_API_KEY="your-gemini-api-key"
export TAVILY_API_KEY="your-tavily-api-key"
export OPENAI_API_KEY="your-openai-api-key"  # Optional
```

3. Launch the API server:
```bash
python main.py
```

The server starts on `http://localhost:8000`

## API Endpoints

### POST /research/stream

Initiates an academic research workflow with streaming results.

**Request Model**:
```
{
  "user_id": "optional-identifier",
  "concatenated_query": "research query string"
}
```

**Response**: Server-Sent Events stream with real-time agent execution data

**Example**:
```bash
curl -X POST http://localhost:8000/research/stream \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user123", "concatenated_query": "Find professors researching stateful LLM agents in European universities"}'
```

## Configuration

### Agent Configuration

Agent parameters are defined in `agent.py`:
- Model selection and temperature settings
- Subagent descriptions and system prompts
- Tool availability per agent
- Backend factory selection

### API Configuration

Server parameters can be modified in `main.py`:
- Host and port binding
- CORS policy settings
- Logging levels and formats
- Middleware configuration

## File Structure

```
agent/
├── agent.py              # Core agent and subagent definitions
├── main.py              # FastAPI application and streaming endpoints
├── requirements.txt     # Project dependencies
├── langgraph.json       # LangGraph configuration
├── .env                 # Environment variables (not in version control)
└── utils/
    ├── tools.py         # Tool definitions (search, file I/O)
    ├── backends.py      # Storage backend factory
    ├── subagents.py     # Subagent utility functions
    └── utils.py         # General utility functions
```

## Output Specifications

### Academic Report Format

Generated in `/results/academic_report.md`:
```markdown
| University Name | Professor Name | Designation | Email | Research Area | Active Grants | Recent Publication | PhD Openings |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
```

### Master's Programs Report Format

Generated in `/results/Masters_Programs_Report.md`:
```markdown
| University Name | Program Name | Duration | Key Research Areas | Tuition Fees | Intake Dates |
| :--- | :--- | :--- | :--- | :--- | :--- |
```

## Performance Considerations

- Asynchronous operations prevent blocking during long-running searches
- Streaming response model enables progressive result delivery
- Query validation reduces unnecessary search operations
- State management through configurable threads supports concurrent requests

## Technical Implementation Details

### Message Flow

1. User submits concatenated query via REST API
2. Lead agent decomposes query into subagent tasks
3. Subagents execute parallel research operations
4. Tool results aggregated into agent state
5. Lead agent compiles findings into structured reports
6. Results streamed back to client via SSE

### Tool Integration

All specialized tools implement LangChain's `@tool` decorator for automatic integration into agent systems. Tools support:
- Async execution to prevent event loop blocking
- Structured input validation
- Error handling and logging
- Context-aware result formatting

### Logging & Observability

Comprehensive logging across all components:
- API request/response tracking
- Agent execution monitoring
- Tool invocation logging
- Error stack traces with context
