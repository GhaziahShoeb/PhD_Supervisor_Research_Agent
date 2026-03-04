# Academic Research Coordinator Agent

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-green)](https://fastapi.tiangolo.com/)
[![LangChain](https://img.shields.io/badge/LangChain-Latest-orange)](https://www.langchain.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An intelligent multi-agent system for comprehensive academic research. Autonomously discovers professors, validates research credentials, and identifies graduate programs aligned with specific research interests and academic backgrounds.

## 📋 Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Technology Stack](#technology-stack)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [API Documentation](#api-documentation)
- [Configuration](#configuration)
- [Project Structure](#project-structure)
- [Output Specifications](#output-specifications)
- [Development](#development)

## ✨ Features

- **Multi-Agent Orchestration**: Hierarchical agent structure with specialized subagents for targeted research
- **Real-Time Streaming**: Server-Sent Events (SSE) for live monitoring of agent execution
- **University Shortlisting**: Identifies top-tier institutions based on IT, AI, and QS rankings
- **Professor Discovery**: Locates faculty researching stateful agents and quantum machine learning
- **Credential Validation**: Verifies active funding, publications, and PhD admission status
- **Graduate Program Discovery**: Finds suitable Master's programs aligned with research interests
- **Structured Report Generation**: Automatic compilation into professional markdown tables
- **Session Management**: UUID-based thread handling for concurrent user requests
- **Deterministic Inference**: Temperature=0 LLM settings for consistent, reproducible results
- **Async-First Design**: Non-blocking I/O throughout the service pipeline

## 🏗️ Architecture

### Design Patterns

```
┌─────────────────────────────────────────────────────────┐
│        Academic Research Lead (Orchestrator)            │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  University-Shortlister                          │  │
│  │  (Identifies top-tier universities)              │  │
│  └──────────────────────────────────────────────────┘  │
│                        │                                │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Professor-Discovery                             │  │
│  │  (Locates faculty members)                       │  │
│  └──────────────────────────────────────────────────┘  │
│                        │                                │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Professor-Validator                             │  │
│  │  (Verifies credentials & funding)                │  │
│  └──────────────────────────────────────────────────┘  │
│                        │                                │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Master's Program Searcher                       │  │
│  │  (Discovers graduate programs)                   │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Key Concepts

- **Hierarchical Multi-Agent System**: Central orchestrator coordinates specialized subagents
- **State Machine Graph**: LangGraph manages deterministic workflows
- **Event Streaming**: Real-time progress tracking via SSE
- **Tool Integration**: Modular tool system for extensibility
- **Async Processing**: Non-blocking I/O for scalable performance

## 🛠️ Technology Stack

### Core Frameworks

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Agent Orchestration** | LangChain, LangGraph, DeepAgents | Multi-agent coordination and workflow |
| **LLM** | Google Gemini 2.5 Pro | Primary language model (temperature=0) |
| **Web Framework** | FastAPI, Uvicorn | RESTful API and ASGI server |
| **Search** | Tavily Search API | Real-time web search capability |
| **Storage** | Google Cloud Storage | Persistent backend for outputs |
| **Data Validation** | Pydantic | Type-safe request/response models |

### Libraries & Dependencies

```
langchain-core            # Core LangChain abstractions
langchain-openai          # OpenAI integration
langchain-google-genai    # Gemini integration
langchain-community       # Extended tools and integrations
langgraph                 # State machine orchestration
deepagents                # Multi-agent framework
fastapi                   # Web framework
uvicorn                   # ASGI server
pydantic                  # Data validation
tavily-python             # Web search client
beautifulsoup4            # HTML parsing
scipy                     # Scientific computing
```

## 📦 Installation

### Prerequisites

- Python 3.10 or higher
- pip or conda package manager
- API Keys:
  - Google Gemini API
  - Tavily Search API
  - (Optional) OpenAI API for fallback LLM

### Setup Steps

1. **Clone the repository**:
```bash
git clone https://github.com/GhaziahShoeb/PhD_Supervisor_Research_Agent
cd professor_research
```

2. **Create virtual environment**:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r agent/requirements.txt
```

4. **Configure environment variables**:
```bash
cp agent/.env.example agent/.env
```

Edit `agent/.env` with your API keys:
```env
GEMINI_API_KEY=your-gemini-api-key
TAVILY_API_KEY=your-tavily-api-key
OPENAI_API_KEY=your-openai-api-key  # Optional
```

## 🚀 Quick Start

### Start the API Server

```bash
cd agent
python main.py
```

Server runs on `http://localhost:8000`


### Make Your First Research Request

```bash
curl -X POST http://localhost:8000/research/stream \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "researcher_001",
    "concatenated_query": "Find professors researching stateful LLM agents and quantum machine learning in leading European universities"
  }'
```

### Response Format

The API streams Server-Sent Events with the following event types:

```json
// Connection established
{"type": "connection", "status": "connected", "thread_id": "uuid"}

// Agent activation
{"type": "agent_active", "agent": "university-shortlister"}

// Agent reasoning
{"type": "thought", "agent": "professor-discovery", "content": "..."}

// Tool invocation
{"type": "tool_call", "agent": "agent-name", "tool": "internet_search", "args": {...}}

// Tool result
{"type": "tool_result", "agent": "agent-name", "tool": "internet_search", "content": "..."}

// Final report
{"type": "final", "content": "... markdown table ..."}
```

## 📡 API Documentation

### Endpoint: POST /research/stream

Initiates academic research workflow with streaming results.

**Request Model**:
```python
{
  "user_id": str (optional, default: "default_user"),
  "concatenated_query": str (required)
}
```

**Response**: Server-Sent Events stream

**Example Request**:
```bash
curl -X POST http://localhost:8000/research/stream \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "concatenated_query": "Find AI research professors in UK universities with active grant funding"
  }' \
  --stream
```

## ⚙️ Configuration

### Agent Settings (agent/agent.py)

```python
# Model configuration
model_gemini = ChatGoogleGenerativeAI(
    model="gemini-2.5-pro",
    temperature=0,              # Deterministic inference
    max_retries=5,
    timeout=600
)

# Subagent definitions
subagents = [
    {
        "name": "university-shortlister",
        "description": "...",
        "system_prompt": "...",
        "tools": [internet_search, write_file],
        "model": model_gemini
    },
    # ... additional subagents
]
```

### API Settings (agent/main.py)

```python
# Server configuration
app = FastAPI(title="Professor Research API")

# CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 📁 Project Structure

```
professor_research/
├── README.md                 # Project documentation
├── agent/
│   ├── agent.py             # Core agent and subagent definitions
│   ├── main.py              # FastAPI application and endpoints
│   ├── requirements.txt      # Python dependencies
│   ├── langgraph.json        # LangGraph configuration
│   ├── .env                  # Environment variables (not in VC)
│   ├── .gitignore            # Git ignore rules
│   ├── notebook.ipynb        # Jupyter notebook for experimentation
│   └── utils/
│       ├── tools.py          # Tool definitions (search, file I/O)
│       ├── backends.py       # Storage backend factory
│       ├── subagents.py      # Subagent utilities
│       └── utils.py          # General utilities
└── research_frontend/        # Frontend application (if applicable)
```

## 📊 Output Specifications

### Academic Report

**File**: `/results/academic_report.md`

```markdown
| University Name | Professor Name | Designation | Email | Research Area | Active Grants | Recent Publication | PhD Openings |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| University of ... | Prof. Name | ... | ... | ... | Yes/No | 2024 | Yes/No |
```

### Master's Programs Report

**File**: `/results/Masters_Programs_Report.md`

```markdown
| University Name | Program Name | Duration | Key Research Areas | Tuition Fees | Intake Dates |
| :--- | :--- | :--- | :--- | :--- | :--- |
| ... | ... | ... | ... | ... | ... |
```

## 🔧 Development

### Running Tests (if available)

```bash
pytest tests/ -v
```

### Code Style

Code follows PEP 8 standards with type hints. Format code using:

```bash
black agent/
isort agent/
```

### Logging

Configure logging levels in environment:

```bash
export LOG_LEVEL=DEBUG
python agent/main.py
```

## 📝 Key Features in Detail

### Real-Time Event Streaming

Monitor agent execution in real-time:
- Agent activation notifications
- Reasoning process (thoughts)
- Tool invocations and results
- Final report generation

### Deterministic Research

Temperature=0 LLM configuration ensures:
- Reproducible results for identical queries
- Consistent formatting across sessions
- Predictable agent behavior

### Scalable Architecture

- Asynchronous request handling
- UUID-based session management
- Concurrent subagent execution
- Non-blocking I/O throughout

### Extensibility

Add custom tools and subagents:

```python
# Add new tool
@tool
async def custom_tool(query: str) -> str:
    """Tool description"""
    return "result"

# Register in subagent configuration
subagents.append({
    "name": "custom-agent",
    "tools": [custom_tool],
    # ... other config
})
```

## 🐛 Troubleshooting

### Issue: API Key Errors

**Solution**: Verify environment variables are properly set:
```bash
echo $GEMINI_API_KEY
echo $TAVILY_API_KEY
```

### Issue: Search Query Validation Fails

**Solution**: Queries must include search keywords, not just `site:` filters. Ensure:
```
✓ "professors of AI research in MIT"
✗ "site:mit.edu"
```

### Issue: Timeout Errors

**Solution**: Increase timeout in agent configuration:
```python
ChatGoogleGenerativeAI(timeout=900)  # 15 minutes
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📮 Contact

For questions or feedback, please open an issue on GitHub.

---

**Built with** ❤️ **using LangChain, LangGraph, and FastAPI**
