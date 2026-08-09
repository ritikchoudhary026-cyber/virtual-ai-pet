"""PetAI Phase 2 backend: exposes the computer's current resource status."""

import psutil
from fastapi import FastAPI

app = FastAPI(title="PetAI Backend")


def choose_mood(cpu: float, memory: float) -> str:
    """Use the same resource thresholds as the desktop pet."""
    if cpu >= 80 or memory >= 90:
        return "alert"
    if cpu >= 30 or memory >= 50:
        return "working"
    return "idle"


@app.get("/status")
def get_status() -> dict[str, float | str]:
    """Return CPU %, memory %, and the resulting PetAI mood."""
    # interval=None is non-blocking and returns a percentage since the previous call.
    cpu = float(psutil.cpu_percent(interval=None))
    memory = float(psutil.virtual_memory().percent)
    return {"cpu": cpu, "memory": memory, "mood": choose_mood(cpu, memory)}
