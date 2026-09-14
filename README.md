# 🤖 Enterprise AI Agent

An enterprise-focused AI agent built to handle support tickets and internal knowledge queries using **LLMs, RAG, MCP, and LangGraph**.

---

## 🚀 Features

- **Intelligent Routing** — Routes requests dynamically to Ticket, Knowledge, Mixed, or General workflows.
- **Ticket Management** — Search, retrieve, and update support tickets.
- **RAG Engine** — Semantic search over internal knowledge bases using PostgreSQL + pgvector.
- **MCP Integration** — Modular ticket operations exposed through Model Context Protocol (MCP).
- **Human-in-the-Loop** — Sensitive ticket updates require explicit approval before execution.
- **Guardrails** — Input validation, prompt-injection defense, and output sanitization.
- **API Security** — API-key authentication and request rate limiting.
- **Persistent State** — PostgreSQL-backed LangGraph checkpointing for durable agent state.
- **Observability** — End-to-end request IDs and structured logging.
- **Dockerized** — Fully containerized multi-container setup via Docker Compose.

---

## 🏗️ Architecture

```text
User
  ↓
FastAPI
  ↓
Guardrails
  ↓
LangGraph Router
  ├── Ticket ──────→ MCP Tools ──→ PostgreSQL
  ├── Knowledge ───→ RAG ────────→ pgvector
  ├── Mixed ───────→ Ticket + RAG
  └── General ─────→ LLM

Sensitive operations:
Agent ──→ Human Approval ──→ MCP Tool ──→ Database
```

---

## ⚡ Approach

### Initial Approach
The system originated as a simple monolithic LLM with basic direct tool-calling.

### Optimization
To address latency, safety, and operational reliability, the system evolved into an agentic architecture featuring:

* **Explicit intent routing** to avoid unnecessary retrieval and tool calls
* **RAG-based knowledge retrieval** using pgvector for grounded context
* **MCP-standardized tools** for clean separation of tool execution
* **Human-in-the-loop approval gates** for destructive or sensitive database operations
* **Bidirectional guardrails** preventing prompt injection and data leaks
* **Persistent agent checkpoints** allowing multi-turn conversational recovery
* **Structured, request-scoped logging** for tracing execution graphs

---

## 🛠️ Tech Stack

| Domain | Technologies |
|---|---|
| **Backend & Frameworks** | Python, FastAPI, Pydantic |
| **Agent Orchestration** | LangGraph, LangChain |
| **LLM & Tool Protocol** | Groq, Model Context Protocol (MCP) |
| **Data & Retrieval** | PostgreSQL, pgvector, Sentence Transformers |
| **Infrastructure** | Docker, Docker Compose |

---

## 📁 Project Structure

```text
Enterprise-Agent/
├── app/
│   ├── api/             # FastAPI route definitions and dependencies
│   ├── agents/          # LangGraph graph definitions, states, and nodes
│   ├── tools/           # Internal tool definitions
│   ├── mcp/             # MCP server client and tool adapters
│   ├── db/              # Database models, migrations, and session management
│   ├── rag/             # Embeddings, chunking, and vector search logic
│   ├── guardrails/      # Input validation and prompt injection defenses
│   └── utils/           # Structured logging and helper utilities
├── data/
│   ├── sample_data/     # Mock support ticket records
│   └── knowledge/       # Internal documentation and knowledge base docs
├── testFiles/           # Integration and unit tests
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## 🐳 Quickstart

### 1. Clone & Navigate
```bash
git clone https://github.com/Rossie2141/Enterprise-Agent.git
cd Enterprise-Agent
```

### 2. Configure Environment
Create a `.env` file in the root directory:
```env
GROQ_API_KEY=your_groq_api_key
POSTGRES_DB=agent_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
API_KEY=your_secure_api_key
```

### 3. Run Containers
```bash
docker compose up -d --build
```

### 4. Health Check
```bash
curl http://localhost:8000/health
```

---

## 🔮 Roadmap

- [ ] Web dashboard / UI interface
- [ ] Role-Based Access Control (RBAC) for ticket actions
- [ ] Automated CI/CD test and deploy pipelines
- [ ] Agent evaluation harness (latency, hallucination, tool accuracy)
- [ ] OpenTelemetry distributed tracing integration

---

## 👨‍💻 Author

**Shriprasad DJ**  
*Built to explore production-oriented Agentic AI and Enterprise AI systems.*
