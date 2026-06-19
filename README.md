# AKSHAT V2: Autonomous Software Engineering Platform

AKSHAT is a local-first autonomous software engineering company powered by multi-agent workflows. It operates as an engineering organization rather than a conversational chatbot, translating user requirements into planned, coded, tested, and deployed software applications automatically.

---

## 🚀 Core Features

- **Multi-Agent Orchestration**: Enlists specialized agents (Project Manager, Architect, Developer, Tester, Deployer, Reviewer, Memory, **Debug**, **Refactor**, **Documentation**, **Dependency**, **Browser**, and **Vision**) to build software sequentially or concurrently.
- **Relational Project History**: Stores registration details, project metadata, event timelines, and agent logs in a local relational database structure.
- **Secure JWT Authentication**: Protects dashboard views and background REST/WebSocket routes using crypt password hashing and standard token encoding.
- **Interactive Replay Timeline**: Step-by-step playback controls allow users to trace how prompts were analyzed, files generated, and builds verified.
- **Offline-First & Fast Fallbacks**: Detects Ollama connection timeouts and caches them, gracefully falling back to cloud APIs (such as Groq or OpenAI) to keep prompts responsive.
- **Intelligent Prompt Router**: Uses a model-based classification brain to determine if a prompt is a simple greeting or an engineering task.
- **Governance & Recovery Engine**: Incorporates a strict multi-gate validation engine that halts execution if the generated code fails quality, security, or ethical benchmarks, while state snapshots allow for seamless recovery.

---

## 🛠️ Technology Stack

### Backend
- **Framework**: FastAPI (Python)
- **Workflow State**: LangGraph
- **Database**: PostgreSQL / SQLite (SQLAlchemy ORM)
- **Token Security**: bcrypt (Password Hashing) & Custom JWT

### Frontend
- **Framework**: React (TypeScript, Vite)
- **State Store**: Zustand
- **Graphics & Avatar**: React Three Fiber & Three.js (Ready Player Me GLTF model)
- **Styling**: TailwindCSS & shadcn/ui

---

## 📂 Project Directory Structure

```text
AKSHAT_software_engineer/
├── backend/
│   ├── alembic.ini        # Database migrations configuration
│   ├── app/
│   │   ├── api/           # Versioned REST API routes
│   │   ├── models/        # SQLAlchemy database models
│   │   ├── schemas/       # Pydantic validation models
│   │   ├── utils/         # Logging, retry, and helpers
│   │   ├── config.py      # Pydantic settings config
│   │   ├── exceptions.py  # Custom application exceptions
│   │   ├── middleware.py  # FastAPI middleware (logging, errors, tracking)
│   │   └── main.py        # FastAPI server entrypoint
│   ├── migrations/        # Alembic schema migrations
│   ├── tests/             # Pytest suite
│   └── ...
├── frontend/              # React dashboard SPA code
│   └── src/
│       ├── components/    # Isolated UI panels (AgentFeed, metrics, explorer)
│       ├── pages/         # Dashboard, Projects list, and Replay Timeline
│       ├── services/      # HTTP and WebSocket clients
│       └── stores/        # Zustand project store
├── workspace/             # Dedicated workspace directory (Local user files)
│   ├── projects/          # Autonomously built software project outputs
│   └── memory/            # SQLite memories database (akshat_memory.sqlite3)
└── .env                   # Environment secrets and config
```

---

## ⚙️ Installation & Running Locally

### 1. Prerequisites
Ensure you have Python 3.12+ and Node.js installed.

### 2. Configure Environment
Copy the example environment file and fill in your secrets:
```bash
cp .env.example .env
# Edit .env with your LLM API keys and JWT secret
```

### 3. Backend Setup
Install the python requirements:
```bash
pip install -r requirements.txt
```

Initialize your database with Alembic:
```bash
cd backend
alembic revision --autogenerate -m "Initial schema"
alembic upgrade head
cd ..
```

Run the backend server:
```bash
cd backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 3000
```
The server will start at `http://127.0.0.1:3000/`.

### 4. Frontend Setup
Navigate to the `frontend` folder, install dependencies, and build the distribution:
```bash
cd frontend
npm install
npm run build
```
The FastAPI backend will automatically serve the compiled React build at the root index route.
