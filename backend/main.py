"""FastAPI backend for the Kuchu-Puchu virtual desktop pet.

Provides /chat (with mode selection), /status, /get_mode, and /set_mode endpoints.
Supports offline (Phi-3 GGUF) and online (Nemotron 3.5 via OpenRouter) inference.
"""

import logging
import traceback

import psutil
from fastapi import FastAPI
from pydantic import BaseModel

from config import settings
from engines import InferenceManager
from memory import retrieve_context, store_conversation
from agent import create_agent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Kuchu-Puchu Pet API")

# ---------- Initialize inference engines ----------
inference = InferenceManager()

# ---------- Global mode (can be changed at runtime via /set_mode) ----------
current_mode: str = settings.DEFAULT_MODE

# ---------- Create agent with the inference manager ----------
agent = create_agent(inference, mode=current_mode)


# ---------- Request/Response models ----------

class ChatRequest(BaseModel):
    message: str
    mode: str = ""  # Empty string means "use server default"


class ModeRequest(BaseModel):
    mode: str


# ---------- Status endpoint ----------

@app.get("/status")
def get_status():
    """Return system resource usage and pet mood."""
    cpu = psutil.cpu_percent()
    mem = psutil.virtual_memory().percent

    # macOS aggressively caches memory; use higher thresholds
    if cpu < 40 and mem < 85:
        mood = "idle"
    elif cpu < 80 and mem < 95:
        mood = "working"
    else:
        mood = "alert"

    return {"cpu": cpu, "memory": mem, "mood": mood}


# ---------- Mode management endpoints ----------

@app.get("/get_mode")
def get_mode():
    """Return the current inference mode."""
    online_available = inference.online is not None
    return {
        "mode": current_mode,
        "online_available": online_available,
    }


@app.post("/set_mode")
def set_mode(req: ModeRequest):
    """Change the global inference mode at runtime."""
    global current_mode, agent

    if req.mode not in ("offline", "online", "auto"):
        return {
            "error": f"Invalid mode: {req.mode}. Use 'offline', 'online', or 'auto'."
        }

    if req.mode == "online" and inference.online is None:
        return {"error": "Online mode unavailable (no API key configured)."}

    current_mode = req.mode
    # Rebuild the agent with the new mode
    agent = create_agent(inference, mode=current_mode)
    logger.info("Mode changed to: %s", current_mode)
    return {"mode": current_mode}


# ---------- Chat endpoint ----------

@app.post("/chat")
def chat(req: ChatRequest):
    """Process a chat message through the LangGraph agent.

    The mode can be overridden per-request, or defaults to the server's current mode.
    """
    global agent, current_mode

    # Determine which mode to use for this request
    request_mode = req.mode if req.mode else current_mode

    # If the request mode differs from the agent's compiled mode, rebuild
    if request_mode != current_mode:
        agent = create_agent(inference, mode=request_mode)
        current_mode = request_mode

    # Retrieve relevant past conversations from Chroma
    retrieved_docs = retrieve_context(req.message, n_results=2)

    # Build initial message list from retrieved memory
    messages = []
    if retrieved_docs:
        for doc in reversed(retrieved_docs):
            parts = doc.split("\nPet: ")
            if len(parts) == 2:
                u_msg = parts[0].replace("User: ", "").strip()
                p_msg = parts[1].strip()
                messages.append(f"User: {u_msg}")
                messages.append(f"Pet: {p_msg}")

    messages.append(f"User: {req.message}")

    # Run the LangGraph agent
    state = {"messages": messages, "next": "chat"}
    try:
        final_state = agent.invoke(state, {"recursion_limit": 6})

        # Extract the last assistant message
        assistant_msgs = [
            msg for msg in final_state["messages"] if msg.startswith("Pet: ")]
        if assistant_msgs:
            reply = assistant_msgs[-1].replace("Pet: ", "")
        else:
            reply = "I got confused!"
    except Exception:
        traceback.print_exc()
        reply = "My brain got stuck in a loop! Try asking differently."

    # Clean up model artifacts from the reply
    reply = reply.replace("<|assistant|>", "").replace("<|end|>", "").strip()

    # Store the conversation in Chroma memory
    store_conversation(req.message, reply)

    return {
        "response": reply,
        "mode_used": current_mode,
    }
