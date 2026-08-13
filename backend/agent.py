"""LangGraph-based agent with tool calling support for both offline and online engines."""

import re
import logging
from datetime import datetime
from typing import TypedDict, List, Tuple, Optional

from langgraph.graph import StateGraph, END
from tools import TOOLS

logger = logging.getLogger(__name__)

# System prompt shared by both engines
TOOL_DESCRIPTIONS = "\n".join(
    f"- {name}: {info['description']} (Parameters: {info['parameters']})"
    for name, info in TOOLS.items()
)


def get_system_prompt() -> str:
    current_date = datetime.now().strftime("%A, %B %d, %Y")
    return f"""You are Kuchu-Puchu, a friendly and highly capable desktop AI assistant. Today is {current_date}.
You have access to the following tools:
{TOOL_DESCRIPTIONS}

When you need to use a tool, respond EXACTLY in this format:
[TOOL: tool_name] [ARGS: arguments]
For example:
[TOOL: calculator] [ARGS: 2+2]
[TOOL: weather] [ARGS: London]
[TOOL: system_stats] [ARGS: none]

If you don't need a tool, just reply directly to the user.
CRITICAL RULES FOR REPLYING:
1. You are a fully capable AI (Nemotron). You can write code, analyze data, and help with complex tasks.
2. Be friendly and conversational, but always provide detailed and professional answers when asked technical questions or coding tasks.
3. Provide the direct answer immediately without any internal notes, reasoning, or parenthetical explanations (e.g. NEVER write "(Note: ...)").
4. ONLY call a tool if you absolutely need it. Use web_search for real-time information, news, or unknown facts.
5. If you receive a [SYSTEM NOTIFICATION] with a tool result, you MUST NOT output another tool call. You MUST output the final answer immediately based on the data.
6. NEVER confuse your name (Kuchu-Puchu) with the user's name.
7. NO EMOJIS ALLOWED in your responses.
"""


class AgentState(TypedDict):
    messages: List[str]
    next: str
    tool_call: Optional[Tuple[str, str]]


def clean_reply(text: str) -> str:
    """Strip hallucinated notes, tool fragments, and truncate to one sentence."""
    # Strip leaked reasoning traces from models like Nemotron 3.5 Lightning
    if "thinking process" in text.lower():
        # Try to find the actual output at the end of the reasoning trace
        output_match = re.search(
            r'(?:Output|Final Output|Response):\s*(.*)',
            text,
            flags=re.IGNORECASE | re.DOTALL)
        if output_match:
            text = output_match.group(1).strip()
        else:
            # If we can't find an Output marker, take the last non-empty line
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            if lines:
                text = lines[-1]

    text = re.sub(r'\(Note:.*?\)', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\[TOOL:.*?\]', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\[ARGS:.*?\]', '', text, flags=re.IGNORECASE)
    text = text.strip()
    return text if text else "I got a little confused!"


def _messages_to_standard(raw_messages: List[str]) -> List[dict]:
    """Convert internal 'User: ...' / 'Pet: ...' strings to OpenAI-style dicts.

    Keeps only the last 6 messages to avoid exceeding context limits.
    """
    standard = [{"role": "system", "content": get_system_prompt()}]
    for msg in raw_messages[-6:]:
        if msg.startswith("User: "):
            standard.append(
                {"role": "user", "content": msg.replace("User: ", "", 1)})
        elif msg.startswith("Pet: "):
            standard.append(
                {"role": "assistant", "content": msg.replace("Pet: ", "", 1)})
        elif msg.startswith("Tool result"):
            # Inject tool results as a system notification inside a user
            # message
            standard.append({
                "role": "user",
                "content": f"[SYSTEM NOTIFICATION]: {msg}. Please provide the final short answer based on this result.",
            })
        else:
            standard.append({"role": "user", "content": msg})
    return standard


def create_agent(inference_manager, mode: str = "auto"):
    """Build and compile a LangGraph agent that uses the given InferenceManager.

    Args:
        inference_manager: An InferenceManager instance from engines/.
        mode: The inference mode to use ("offline", "online", or "auto").
    """

    def chat_node(state: AgentState) -> dict:
        """Generate a response from the LLM, detect tool calls, and route."""
        standard_messages = _messages_to_standard(state["messages"])

        # Call the appropriate engine via InferenceManager
        reply, mode_used = inference_manager.get_response(
            standard_messages,
            mode=mode,
            temperature=0.3,
        )
        logger.info("LLM Reply [%s]: %s", mode_used, reply)

        # Strip non-ASCII characters (emoji removal)
        reply = reply.encode("ascii", "ignore").decode("ascii").strip()

        # Detect tool call patterns in the reply
        tool_match = re.search(
            r'\[TOOL:\s*(\w+)\](?:\s*\[ARGS:\s*(.*?)\])?', reply)
        new_msgs = state["messages"][:]

        if tool_match:
            text_before = reply[:tool_match.start()].strip()
            if text_before:
                # Model wrote text before the tool call - return just the text
                final_text = clean_reply(text_before)
                new_msgs.append(f"Pet: {final_text}")
                logger.info(
                    "Ignored appended tool, returning text: %s",
                    final_text)
                return {"messages": new_msgs, "next": END}

            tool_name = tool_match.group(1)
            args_str = tool_match.group(
                2).strip() if tool_match.group(2) else ""

            # Anti-loop: don't call the same tool twice in a row
            if state["messages"] and state["messages"][-1].startswith(
                    f"Tool result ({tool_name})"):
                cleaned_reply = reply.replace(tool_match.group(0), "").strip()
                if not cleaned_reply:
                    cleaned_reply = state["messages"][-1].split(":", 1)[
                        1].strip()
                final_text = clean_reply(cleaned_reply)
                new_msgs.append(f"Pet: {final_text}")
                logger.info("Loop detected! Forcing answer: %s", final_text)
                return {"messages": new_msgs, "next": END}

            if args_str.lower() == "none" or not args_str:
                args = ""
            else:
                args = args_str
            new_msgs.append(f"Pet: {reply}")
            logger.info("Routing to tool: %s with args: %s", tool_name, args)
            return {
                "messages": new_msgs,
                "tool_call": (
                    tool_name,
                    args),
                "next": "tools"}

        # Smart universal math tool fallback for any calculation query
        if not tool_match and state["messages"]:
            last_msg = state["messages"][-1]
            if last_msg.startswith("User: "):
                user_text = last_msg.replace("User: ", "", 1).strip()
                math_keywords = ['calculate', 'compute', 'solve', 'what is', 'how much is', 'value of', 'result of']
                has_math_kw = any(kw in user_text.lower() for kw in math_keywords)
                has_math_op = re.search(r'\d+\s*(?:%|percent|\+|\-|\*|\/|x|plus|minus|times|into|divided)\s*(?:of)?\s*\d+', user_text, re.I)
                has_digits_op = any(op in user_text for op in ['+', '*', '/', '%']) and re.search(r'\d+', user_text)

                if (has_math_kw or has_math_op or has_digits_op) and not any("Tool result (calculator)" in m for m in state["messages"]):
                    logger.info("Universal math fallback triggering calculator for: %s", user_text)
                    return {
                        "messages": new_msgs,
                        "tool_call": ("calculator", user_text),
                        "next": "tools"
                    }

        # No tool call - return clean text
        final_text = clean_reply(reply)
        new_msgs.append(f"Pet: {final_text}")
        return {"messages": new_msgs, "next": END}

    def tool_node(state: AgentState) -> dict:
        """Execute the requested tool and return its result."""
        tool_name, args = state.get("tool_call", (None, None))
        if tool_name and tool_name in TOOLS:
            func = TOOLS[tool_name]["function"]
            try:
                if tool_name == "calculator":
                    result = func(args)
                elif tool_name == "system_stats":
                    result = func()
                elif tool_name == "weather":
                    result = func(args if args else "London")
                elif tool_name == "web_search":
                    result = func(args)
                else:
                    result = "Tool not implemented"
            except Exception as exc:
                result = f"Tool error: {exc}"

            tool_result_msg = f"Tool result ({tool_name}): {result}"
            logger.info("Tool Result: %s", tool_result_msg)
            new_msgs = state["messages"][:]
            new_msgs.append(tool_result_msg)
            return {"messages": new_msgs, "next": "chat"}

        new_msgs = state["messages"][:]
        new_msgs.append("Tool result: Invalid tool call.")
        return {"messages": new_msgs, "next": "chat"}

    # Build the LangGraph state machine
    workflow = StateGraph(AgentState)
    workflow.add_node("chat", chat_node)
    workflow.add_node("tools", tool_node)
    workflow.set_entry_point("chat")

    def router(state: AgentState):
        return state["next"]

    workflow.add_conditional_edges(
        "chat", router, {
            "tools": "tools", END: END})
    workflow.add_edge("tools", "chat")

    return workflow.compile()
