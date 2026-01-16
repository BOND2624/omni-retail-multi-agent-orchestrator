# Omni-Retail Multi-Agent Orchestrator

A hierarchical multi-agent system where a Super Agent (Orchestrator) coordinates four specialized Sub-Agents, each owning its own relational database.

## Architecture

```
User
 │
 ▼
Super Agent (Orchestrator)
 │
 ├── ShopCore Agent  ── DB_ShopCore (SQLite)
 ├── ShipStream Agent ── DB_ShipStream
 ├── PayGuard Agent  ── DB_PayGuard
 └── CareDesk Agent  ── DB_CareDesk
```

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Add your OpenRouter API key to `.env`:
```
OPENROUTER_API_KEY=your_api_key_here
```

3. Run the system:

**Option A: Web UI (Recommended)**
```bash
python server.py
```
Then open your browser to: http://localhost:8000

**Option B: Command Line**
```bash
python main.py
```

## Project Structure

```
omni-retail-multiagent-orchestrator/
 ├── agents/
 │    ├── orchestrator.py
 │    ├── shopcore_agent.py
 │    ├── shipstream_agent.py
 │    ├── payguard_agent.py
 │    └── caredesk_agent.py
 ├── db/
 │    ├── shopcore.db
 │    ├── shipstream.db
 │    ├── payguard.db
 │    └── caredesk.db
 ├── sql/
 │    ├── shopcore.sql
 │    ├── shipstream.sql
 │    ├── payguard.sql
 │    └── caredesk.sql
 ├── static/
 │    └── index.html (Web UI)
 ├── utils/
 │    ├── llm_client.py (OpenRouter integration)
 │    └── logger.py
 ├── logs/
 ├── main.py
 ├── server.py (WebSocket server)
 └── requirements.txt
```

## Features

- **Web UI with WebSocket**: Real-time interactive interface
- **Intelligent Query Parsing**: Automatically identifies required agents
- **Missing Information Detection**: Asks users for OrderID, Email, etc. when needed
- **Dependency Resolution**: Resolves inter-agent dependencies automatically
- **Structured Logging**: All execution steps, SQL queries, and results are logged
- **LangGraph Integration**: State-based orchestration with conditional routing
- **Multi-Database Support**: Each agent owns and queries only its own database
- **OpenRouter Integration**: Fast LLM responses with automatic model fallback

## Web UI

The Web UI provides:
- Real-time query processing
- Live status updates
- Agent execution tracking
- Interactive input prompts
- Beautiful, modern interface

Access at: http://localhost:8000

## Development Flow

The system is built incrementally:
1. Project Scaffolding ✅
2. Database Layer ✅
3. Sub-Agent Layer ✅
4. Orchestrator Logic ✅
5. LangGraph Integration ✅
6. Logging & Observability ✅
7. Demonstration & Validation ✅
8. Web UI with WebSocket ✅
