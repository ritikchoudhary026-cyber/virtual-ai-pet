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


def web_search(query: str) -> str:
    """Search DuckDuckGo for the query and return summarized text snippets."""
    try:
        from ddgs import DDGS
        results = list(DDGS().text(query, max_results=3))
        if not results:
            return "No web search results found."
        
        snippets = []
        for r in results:
            snippets.append(f"- {r.get('title', '')}: {r.get('body', '')}")
        return "\n".join(snippets)
    except Exception as e:
        return f"Web search failed: {e}"


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
    },
    "web_search": {
        "function": web_search,
        "description": "Search the internet for current news, facts, or real-time information. Input: search query.",
        "parameters": "query"
    }
}
