# 💰 CashPilot

**AI-powered CFO for Indie SaaS Founders — runs 100% on free-tier LLMs.**

CashPilot is an agentic financial platform that transforms raw transaction data into boardroom-ready insights. By orchestrating multiple specialized AI agents, it provides real-time financial monitoring, anomaly detection, and interactive forecasting without the cost of a traditional CFO.

---

## ✨ Key Features

- **🧠 ReAct Analysis Agent**: A dynamic, goal-oriented agent that explores your financial data to find the most critical insights (Revenue trends, burn rate, runway).
- **💬 Interactive CFO Chat**: Ask natural language questions about your business finances (e.g., "What was my highest expense last month?", "Can I afford to hire a developer?").
- **📊 Financial Snapshot**: Real-time dashboard with health scores, revenue/expense charts, and sparklines.
- **🚨 Automated Monitoring**: Nightly and weekly monitoring for spend anomalies and financial health updates.
- **📑 Executive Reporting**: Automatically generates professional Markdown reports with narrative analysis.
- **🆓 Zero-Cost LLM Strategy**: Built-in support for free-tier providers like **Groq (Llama 3.3)** and **Gemini 1.5/2.0**.

---

## 🏗️ Architecture

- **Backend**: FastAPI + LangGraph (Dynamic ReAct graphs for complex analysis)
- **Database**: PostgreSQL (Async SQLAlchemy) + Redis (Caching & Task Management)
- **Frontend**: React 18 + TypeScript + Tailwind CSS + Recharts
- **Agents**: Specialized agents for Ingestion, Analysis, Reporting, and Notifications.

---

## 🚀 Quick Start

### 1. Clone and Configure
```bash
git clone <repo-url>
cd FinAgent-OS
cp .env.example .env
```
Add your free API keys to `.env` (Get them from [Groq Console](https://console.groq.com/keys) and [Google AI Studio](https://aistudio.google.com/apikey)).

### 2. Run with Docker (Recommended)
The entire stack (DB, Redis, Backend, Frontend) can be started with one command:
```bash
docker-compose up --build
```

### 3. Access the Platform
- **Frontend**: [http://localhost:5173](http://localhost:5173)
- **API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

---

## 🛠️ Development Setup

If you prefer running components natively:

### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

---

## 📂 Project Structure

```text
.
├── backend/
│   ├── agents/           # LLM Agent definitions (ReAct & Logic)
│   ├── api/              # FastAPI routes & rate limiting
│   ├── db/               # SQLAlchemy models & migrations
│   ├── graph/            # LangGraph workflow orchestration
│   ├── services/         # Business logic & baseline monitoring
│   └── tools/            # Provider-agnostic LLM router & utilities
├── frontend/
│   ├── src/features/     # Modular features (Chat, Snapshot, Settings)
│   ├── src/components/   # Shared UI components (Radix + Tailwind)
│   └── src/hooks/        # Custom React hooks (WS, Theme, Auth)
├── docker-compose.yml    # Full stack orchestration
└── .env.example          # Template for required API keys
```

---

## 🧠 Engineering Highlights

- **Dynamic Routing**: Uses LangGraph's ReAct pattern to allow agents to "think" and call tools based on data findings.
- **Provider-Agnostic**: A custom LLM router handles failover between Groq, Gemini, and Anthropic.
- **Real-time Updates**: WebSocket integration pushes agent activity and financial alerts directly to the UI.
- **Robust Ingestion**: Supports CSV/JSON with automated category inference and P&L baseline updating.

---

## 📜 License

MIT License. Free to use for your own SaaS or as a base for your financial tools.
