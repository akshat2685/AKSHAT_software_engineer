# AKSHAT V2: Autonomous Software Engineering Platform

AKSHAT is a local-first autonomous software engineering company powered by multi-agent workflows. It operates as an engineering organization rather than a conversational chatbot, translating user requirements into planned, coded, tested, and deployed software applications automatically.

---

## 🚀 Core Features

- **Multi-Agent Orchestration**: Enlists specialized agents (Project Manager, Architect, Developer, Tester, Deployer, Reviewer, and Memory) to build software sequentially.
- **Relational Project History**: Stores registration details, project metadata, event timelines, and agent logs in a local relational database structure.
- **Secure JWT Authentication**: Protects dashboard views and background REST/WebSocket routes using crypt password hashing and standard token encoding.
- **Interactive Replay Timeline**: Step-by-step playback controls allow users to trace how prompts were analyzed, files generated, and builds verified.
- **Offline-First & Fast Fallbacks**: Detects Ollama connection timeouts and caches them, gracefully falling back to cloud APIs (such as Groq or OpenAI) to keep prompts responsive.
- **Intelligent Prompt Router**: Uses a model-based classification brain to determine if a prompt is a simple greeting or an engineering task.

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
│   ├── agents/            # Worker agents (PM, Dev, Tester, Deploy, Review, etc.)
│   ├── api/               # REST API endpoints & JWT authentication routes
│   ├── database/          # Connection manager and SQLAlchemy models
│   ├── graph/             # LangGraph state machine orchestrator
│   └── services/          # LLM router and Ollama/Cloud providers
├── frontend/              # React dashboard SPA code
│   ├── src/
│   │   ├── components/    # Isolated UI panels (AgentFeed, metrics, explorer)
│   │   ├── pages/         # Dashboard, Projects list, and Replay Timeline
│   │   ├── services/      # HTTP and WebSocket clients
│   │   └── stores/        # Zustand project store
├── workspace/             # Dedicated workspace directory (Local user files)
│   ├── projects/          # Autonomously built software project outputs
│   └── memory/            # SQLite memories database (akshat_memory.sqlite3)
└── src/
    └── akshat_fastapi.py  # Application startup server entrypoint
```

---

## ⚙️ Installation & Running Locally

### 1. Prerequisites
Ensure you have Python 3.12+ and Node.js installed.

### 2. Configure Environment
Set up your local model and API credentials in your terminal:
```bash
# Set Cloud API key (Groq, OpenAI, etc.)
export CLOUD_API_KEY="your_api_key_here"

# Configure local Ollama model if available
export OLLAMA_MODEL="free01/gemma4:e4b"
```

### 3. Backend Setup
Install the python requirements:
```bash
pip install -r requirements.txt
```

Run the backend server:
```bash
python src/akshat_fastapi.py
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
