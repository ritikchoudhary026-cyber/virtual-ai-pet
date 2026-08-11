import psutil
import json
import requests
import subprocess
import os

def calculator(expression: str) -> str:
    """Calculate a math expression safely."""
    # Convert "15% of 200" to "(15/100)*200"
    import re
    expression = expression.replace('?', '').replace('=', '').replace("'", "").replace('"', "").strip()
    expression = re.sub(r'(\d+(?:\.\d+)?)%\s*of\s*(\d+(?:\.\d+)?)', r'(\1/100)*\2', expression.lower())
    
    allowed = set("0123456789+-*/().% ")
    if not all(c in allowed for c in expression):
        return "Error: Invalid characters in expression."
    try:
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"Error: {e}"

def system_stats() -> str:
    """Return CPU and memory usage."""
    cpu = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory().percent
    return json.dumps({"cpu": cpu, "memory": mem})

def weather(city: str = "London") -> str:
    """Get current weather for a city using wttr.in."""
    try:
        url = f"https://wttr.in/{city}?format=%C+%t"
        resp = requests.get(url, timeout=5)
        return resp.text.strip()
    except:
        return "Weather service unavailable."



# Register tools with their schemas (for LLM to understand)
TOOLS = {
    "calculator": {
        "function": calculator,
        "description": "Perform mathematical calculations. Input: expression string (e.g., '2+2', '15% of 200').",
        "parameters": "expression"
    },
    "system_stats": {
        "function": system_stats,
        "description": "Get current CPU and memory usage. No parameters needed.",
        "parameters": ""
    },
    "weather": {
        "function": weather,
        "description": "Get current weather for a city. Input: city name.",
        "parameters": "city"
    }
}
