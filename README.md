## ☕ Buy Me a Coffee
If this project helped you learn something new, or you just enjoy using it, consider supporting my late-night coding sessions! Your support helps me maintain the code, add new LLM features, and keep the repository bug-free.

💸 **Support via UPI:** choudharyritik026-1@okicici

# kuchu-Puchu PetAI

A small, transparent, draggable desktop pet. Its animation changes as CPU and memory usage change. Everything runs locally and uses no paid service.

## Project layout

```
PetAI/
├── pet_ui.py                 # Phase 1 standalone UI
├── backend/
│   ├── main.py               # Phase 2 FastAPI service
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── pet_ui.py             # Phase 2 UI
│   └── requirements.txt
├── assets/                   # Add your GIF animations here
├── docker-compose.yml
└── README.md
```

## Prerequisites

- Python 3.10 or newer: install it from https://www.python.org/downloads/
- Docker Desktop (only for Phase 2's backend): install it from https://www.docker.com/products/docker-desktop/
- Three GIFs in `assets/`: `idle.gif`, `working.gif`, and `alert.gif`. You can temporarily copy the same GIF three times.

On Windows, open PowerShell in the `PetAI` folder. In the commands below, use `python` if that works on your installation; otherwise replace it with `py`.

## Phase 1: local resource monitoring in one script

Create and activate a virtual environment (do this once):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install PyQt5 psutil pynput
```

Run the Phase 1 pet:

```powershell
python pet_ui.py
```

The pet checks your computer every two seconds. It is **working** for five seconds after keyboard, mouse, trackpad, or scrolling activity, then becomes **idle**. It becomes **alert** when CPU reaches 80% or memory reaches 90%. Drag it with the left mouse button. Stop it with `Ctrl+C` in the terminal.

## Phase 2: FastAPI backend in Docker, UI on your computer

Start Docker Desktop first. From the project root, build and start the backend:

```powershell
docker compose up --build
```

Leave that terminal open. The API is available at http://localhost:8000/status and its interactive documentation is at http://localhost:8000/docs.

In a second PowerShell window, enter the project folder, activate the same virtual environment, install the frontend dependencies, and run the UI:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r frontend\requirements.txt
python frontend\pet_ui.py
```

The frontend calls the backend every two seconds. If the backend is unavailable, it keeps showing the last successful animation; if it has never connected, it displays a small disconnected message.

Stop the UI with `Ctrl+C`. Stop the Docker backend with `Ctrl+C` in its terminal, then run this if you want to remove the stopped container:

```powershell
docker compose down
```

## Running the backend without Docker (optional)

If Docker Desktop is not available, install backend dependencies and start Uvicorn locally:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```
![Idle character](E4AEC8A5-B848-46CC-BB71-5A034E554B40_5-removebg-preview.png)



















![working character](BFE8A160-ECA1-4A22-B12F-5416503F8EC2_5-removebg-preview.png)




























![alert character](B1B25D83-7E97-46B1-8ED9-7CB7D573E7C8_3-removebg-preview.png)