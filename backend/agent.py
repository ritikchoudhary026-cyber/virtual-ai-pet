import re
from typing import TypedDict, List, Tuple, Optional
from langgraph.graph import StateGraph, END
import json
from tools import TOOLS

class AgentState(TypedDict):
    messages: List[str]
    next: str
    tool_call: Optional[Tuple[str, str]]

def create_agent(llm):
    # System prompt telling the LLM how to use tools
    tool_descriptions = "\n".join([
        f"- {name}: {info['description']} (Parameters: {info['parameters']})"
        for name, info in TOOLS.items()
    ])
    
    system_prompt = f"""You are Kuchu-Puchu, a friendly and cute desktop pet assistant. You have access to the following tools:
{tool_descriptions}

When you need to use a tool, respond EXACTLY in this format:
[TOOL: tool_name] [ARGS: arguments]
For example:
[TOOL: calculator] [ARGS: 2+2]
[TOOL: weather] [ARGS: London]
[TOOL: system_stats] [ARGS: none]

If you don't need a tool, just reply directly to the user.
CRITICAL RULES FOR REPLYING:
1. Reply with exactly ONE short, natural sentence.
2. Provide the direct answer immediately without any internal notes, reasoning, or parenthetical explanations (e.g. NEVER write "(Note: ...)").
3. For math and calculations, ALWAYS use digits and numbers (e.g. write "6" or "100.0", NEVER "Six" or "One hundred").
4. ONLY call a tool if you absolutely need it to calculate math or get facts. DO NOT call any tools for greetings (e.g. "hello") or personal questions (e.g. "what is my name").
5. If you receive a [SYSTEM NOTIFICATION] with a tool result, you MUST NOT output another tool call. You MUST output the final answer immediately.
6. Act like a cute pet, not a robotic AI. NO EMOJIS ALLOWED.
7. NEVER confuse your name (Kuchu-Puchu) with the user's name. If the user tells you their name, remember it and use it.
"""

    def chat_node(state: AgentState) -> dict:
        # Construct exact Phi-3 prompt manually
        prompt = f"<|system|>\n{system_prompt}<|end|>\n"
        
        # Inject conversation history
        for msg in state["messages"][-6:]: # Keep last 6 messages
            if msg.startswith("User: "):
                prompt += f"<|user|>\n{msg.replace('User: ', '', 1)}<|end|>\n"
            elif msg.startswith("Pet: "):
                prompt += f"<|assistant|>\n{msg.replace('Pet: ', '', 1)}<|end|>\n"
            elif msg.startswith("Tool result"):
                prompt += f"<|user|>\n[SYSTEM NOTIFICATION]: {msg}. Please provide the final short answer based on this result.\n<|end|>\n"
            else:
                prompt += f"<|user|>\n{msg}<|end|>\n"

        prompt += "<|assistant|>\n"
        
        # Clear KV cache to prevent llama-cpp-python segfault on repeated tool calls
        if hasattr(llm, 'reset'):
            llm.reset()
            
        # Call Phi-3 model
        output = llm(
            prompt=prompt,
            max_tokens=150,
            temperature=0.3,
            top_p=0.9,
            repeat_penalty=1.1,
            stop=["<|end|>", "<|user|>", "\nUser:"]
        )
        reply = output["choices"][0]["text"].strip()
        # Force strip any emojis
        reply = reply.encode("ascii", "ignore").decode("ascii").strip()
        print(f"LLM Reply: {reply}")
        
        # Helper to clean hallucinated text and extract exactly one sentence
        def clean_reply(text):
            # Remove any trailing parenthetical notes or tool leftovers
            text = re.sub(r'\(Note:.*?\)', '', text, flags=re.IGNORECASE)
            text = re.sub(r'\[TOOL:.*?\]', '', text, flags=re.IGNORECASE)
            text = re.sub(r'\[ARGS:.*?\]', '', text, flags=re.IGNORECASE)
            text = text.strip()
            # Truncate to the first sentence to prevent infinite repeating loops
            match = re.search(r'(.*?[\.\!\?])(?:\s|$)', text)
            if match:
                text = match.group(1).strip()
            return text if text else "I got a little confused!"

        # Check if reply contains a tool call (ARGS is optional)
        tool_match = re.search(r'\[TOOL:\s*(\w+)\](?:\s*\[ARGS:\s*(.*?)\])?', reply)
        new_msgs = state["messages"][:]
        
        if tool_match:
            text_before = reply[:tool_match.start()].strip()
            if text_before:
                # Model provided conversational text before the tool call. Ignore the tool call.
                final_text = clean_reply(text_before)
                new_msgs.append(f"Pet: {final_text}")
                print(f"Ignored appended tool, returning text: {final_text}")
                return {
                    "messages": new_msgs,
                    "next": END
                }
            
            # Pure tool call
            tool_name = tool_match.group(1)
            args_str = tool_match.group(2).strip() if tool_match.group(2) else ""
            
            # Anti-loop mechanism: If it calls the same tool it just got a result for, force it to stop
            if state["messages"] and state["messages"][-1].startswith(f"Tool result ({tool_name})"):
                cleaned_reply = reply.replace(tool_match.group(0), "").strip()
                if not cleaned_reply:
                    # Extract the result from the previous message
                    cleaned_reply = state["messages"][-1].split(":", 1)[1].strip()
                final_text = clean_reply(cleaned_reply)
                new_msgs.append(f"Pet: {final_text}")
                print(f"Loop detected! Forcing answer: {final_text}")
                return {
                    "messages": new_msgs,
                    "next": END
                }
                
            if args_str.lower() == "none" or not args_str:
                args = ""
            else:
                args = args_str
            new_msgs.append(f"Pet: {reply}")
            print(f"Routing to tool: {tool_name} with args: {args}")
            return {
                "messages": new_msgs,
                "tool_call": (tool_name, args),
                "next": "tools"
            }
        else:
            final_text = clean_reply(reply)
            new_msgs.append(f"Pet: {final_text}")
            return {
                "messages": new_msgs,
                "next": END
            }

    def tool_node(state: AgentState) -> dict:
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
                else:
                    result = "Tool not implemented"
            except Exception as e:
                result = f"Tool error: {e}"
            
            tool_result_msg = f"Tool result ({tool_name}): {result}"
            print(f"Tool Result: {tool_result_msg}")
            new_msgs = state["messages"][:]
            new_msgs.append(tool_result_msg)
            return {
                "messages": new_msgs,
                "next": "chat"
            }
        else:
            new_msgs = state["messages"][:]
            new_msgs.append("Tool result: Invalid tool call.")
            return {
                "messages": new_msgs,
                "next": "chat"
            }

    # Build graph
    workflow = StateGraph(AgentState)
    workflow.add_node("chat", chat_node)
    workflow.add_node("tools", tool_node)
    workflow.set_entry_point("chat")
    
    def router(state: AgentState):
        return state["next"]
        
    workflow.add_conditional_edges(
        "chat",
        router,
        {"tools": "tools", END: END}
    )
    workflow.add_edge("tools", "chat")
    
    return workflow.compile()
