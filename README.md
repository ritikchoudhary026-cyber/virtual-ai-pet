## ☕ Buy Me a Coffee
If this project helped you learn something new, or you just enjoy using it, consider supporting my late-night coding sessions! Your support helps me maintain the code, add new LLM features, and keep the repository bug-free.

💸 **Support via UPI:** choudharyritik026-1@okicici



#  Virtual AI Pet – Kuchu-Puchu

A desktop AI companion that lives on your screen, monitors system activity, chats with you (offline/online), remembers past conversations, and can use tools. Built with Python, PyQt5, FastAPI, Hugging Face models, LangGraph, ChromaDB, Docker, and CI/CD pipelines.

---

##  Features

###  Visual & Reactive Pet
- Draggable, frameless, always-on-top transparent window
- Animated GIF changes based on CPU/memory usage (idle/working/alert)
- Smooth PyQt5 UI with speech bubble and chat input

###  Intelligent Chat (Dual Mode)
- **Offline:** Local Phi-3-mini (GGUF) via llama-cpp-python
- **Online:** NVIDIA Nemotron 3.5 Lightning via API (fallback to offline in auto mode)
- Mode toggle in UI: `auto`, `offline`, `online`
- Shared memory system works in both modes

###  Memory (RAG)
- Persistent chat history stored in ChromaDB
- Semantic retrieval of past conversations using sentence-transformers embeddings
- Context-aware responses (e.g., remembers your name, schedule, preferences)

###  Tools & Agent (LangGraph)
- Calculator, system stats, weather, terminal file reader
- Agent decides when to use a tool and executes it
- Multi-step reasoning via LangGraph state machine

###  CI/CD & MLOps (Setup Ready)
- GitHub Actions for linting, testing, Docker build & push
- DVC for data/model versioning
- MLflow for experiment tracking (local)
- Scheduled retraining workflow (optional with self-hosted runner)

---

##  Architecture
```
┌─────────────────────┐         ┌──────────────────────────┐
│      Frontend       │  HTTP   │     FastAPI Backend      │
│     (PyQt5 UI)      │────────▶│   /status, /chat         │
└─────────────────────┘         └────────────┬─────────────┘
                                             │
                                             ▼
                               ┌─────────────────────────────┐
                               │      Inference Manager      │
                               │  ┌────────────────────────┐  │
                               │  │ OfflineEngine          │  │  (Phi-3 via llama-cpp)
                               │  ├────────────────────────┤  │
                               │  │ OnlineEngine           │  │  (Nemotron via API)
                               │  └────────────────────────┘  │
                               └────────────┬────────────────┘
                                            │
                                            ▼
                               ┌────────────────────────────┐
                               │     Memory (ChromaDB)      │
                               │   Embeddings (MiniLM)      │
                               └────────────────────────────┘
```

##  Tech Stack

- **Frontend:** PyQt5
- **Backend:** FastAPI, Uvicorn, Pydantic
- **Models:** Phi-3-mini (GGUF), Nemotron 3.5 Lightning (API), Sentence-Transformers (all-MiniLM-L6-v2)
- **Vector DB:** ChromaDB
- **Agent:** LangGraph, custom tools
- **Containerization:** Docker, Docker Compose
- **CI/CD:** GitHub Actions, Docker Hub
- **MLOps:** DVC, MLflow
- **Others:** psutil, requests, httpx, python-dotenv

---

##  Folder Structure

```
virtual-ai-pet/
├── backend/
│   ├── main.py                 # FastAPI app
│   ├── config.py               # Settings from env
│   ├── engines/
│   │   ├── base.py
│   │   ├── offline_engine.py   # Phi-3 GGUF
│   │   └── online_engine.py    # Nemotron API
│   ├── tools.py                # Calculator, system stats, etc.
│   ├── agent.py                # LangGraph agent
│   ├── memory.py               # Chroma helpers
│   ├── models/                 # Downloaded GGUF models
│   │   └── phi-3-mini-4k-instruct.Q4_K_M.gguf
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── pet_ui.py               # Main pet window
│   ├── assets/                 # GIFs (idle, working, alert)
│   ├── requirements.txt
│   └── Dockerfile (optional)
├── docker-compose.yml
├── .github/workflows/
│   ├── ci.yml
│   └── mlops.yml
├── .gitignore
├── .env.example
└── README.md
```

##  Prerequisites

- **Python 3.10+**
- **Git**
- **Docker** (for containerized backend)
- **NVIDIA API key** (free tier available) – for online mode (optional)
- **Hugging Face token** (optional, for faster downloads)

---

##  Setup Instructions

### 1. Clone Repository

```bash
git clone https://github.com/ritikchoudhary026-cyber/virtual-ai-pet.git
cd virtual-ai-pet

## backend-setup
Backend Setup (Local)
bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt

Download the Phi-3-mini GGUF model:

bash
mkdir -p models
cd models
curl -L -O "https://huggingface.co/TheBloke/Phi-3-mini-4k-instruct-GGUF/resolve/main/phi-3-mini-4k-instruct.Q4_K_M.gguf"
cd ..

## Environment Variables
Create .env file inside backend/ (use .env.example as template):

ini
DEFAULT_MODE=auto
PHI_MODEL_PATH=models/phi-3-mini-4k-instruct.Q4_K_M.gguf
NEMOTRON_API_KEY=your_nemotron_api_key_here
NEMOTRON_API_URL=https://integrate.api.nvidia.com/v1/chat/completions
NEMOTRON_MODEL=nvidia/nemotron-3.5-8b-chat
NEMOTRON_TIMEOUT=15
NEMOTRON_MAX_RETRIES=2
CHROMA_DB_PATH=./chroma_db

##Frontend Setup
bash
cd ../frontend
pip install -r requirements.txt

##Running the Project
Backend (Terminal 1)
bash
cd backend
export KMP_DUPLICATE_LIB_OK=TRUE   # for Mac only
uvicorn main:app --host 0.0.0.0 --port 8000

##Frontend (Terminal 2)
bash
cd frontend
python pet_ui.py

##Docker Setup (Backend)
Build and run backend only:

bash
docker compose up --build

##Testing
Chat: Type messages in the pet window. Test offline and online modes.

Memory: Tell pet your name, then ask "What is my name?"

Tools: Ask "What is 15% of 250?" or "Check CPU usage."


# Credits & License
Phi-3-mini model: Microsoft (GGUF by TheBloke)

Nemotron 3.5 Lightning: NVIDIA

All code written by Ritik Choudhary

##This project is for educational purposes. Use it responsibly and adhere to the respective licenses of the models and sources. 

