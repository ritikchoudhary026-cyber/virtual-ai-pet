import psutil
import json
import requests


def calculator(expression: str) -> str:
    """Calculate any math expression safely."""
    import re
    import math

    expr = expression.lower()
    # Strip non-math question prefixes
    expr = re.sub(r'^(what\s+is|calculate|compute|solve|how\s+much\s+is|value\s+of|result\s+of)\s+', '', expr).strip()
    expr = expr.replace('?', '').replace('=', '').replace("'", "").replace('"', "").strip()

    # Convert verbal words to operators
    expr = re.sub(r'(\d+(?:\.\d+)?)%\s*of\s*(\d+(?:\.\d+)?)', r'(\1/100)*\2', expr)
    expr = re.sub(r'(\d+(?:\.\d+)?)\s*percent\s*of\s*(\d+(?:\.\d+)?)', r'(\1/100)*\2', expr)
    expr = expr.replace(' multiplied by ', '*').replace(' times ', '*').replace(' into ', '*').replace(' x ', '*')
    expr = expr.replace(' divided by ', '/').replace(' plus ', '+').replace(' minus ', '-')
    expr = expr.replace('^', '**')

    # Allow math functions like sqrt
    allowed_names = {"sqrt": math.sqrt, "abs": abs, "pow": pow, "round": round}

    allowed_chars = set("0123456789+-*/().%^ ")
    # Filter expression to clean characters
    clean_expr = "".join(c for c in expr if c in allowed_chars or c.isalpha())

    try:
        result = eval(clean_expr, {"__builtins__": None}, allowed_names)
        # Format whole numbers neatly
        if isinstance(result, float) and result.is_integer():
            return str(int(result))
        return str(result)
    except Exception as e:
        return f"Error evaluating calculation: {e}"


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
    except BaseException:
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
