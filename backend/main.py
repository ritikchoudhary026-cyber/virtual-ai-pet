from fastapi import FastAPI
from pydantic import BaseModel
import psutil
import chromadb
from sentence_transformers import SentenceTransformer
import datetime
from llama_cpp import Llama
from agent import create_agent

app = FastAPI()

# ---------- Load Phi-3-mini model ----------
model_path = "models/Phi-3-mini-4k-instruct-q4.gguf"
llm = Llama(
    model_path=model_path,
    n_ctx=2048,           # context length
    n_threads=4,          # Number of CPU threads to use for model inference
    verbose=False
)

# ---------- Chroma DB Setup ----------
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="chat_memory")

# ---------- Embedding model ----------
embedder = SentenceTransformer("all-MiniLM-L6-v2")

# ---------- Initialize Agent ----------
agent = create_agent(llm)

# ---------- Status endpoint ----------
@app.get("/status")
def get_status():
    cpu = psutil.cpu_percent()
    mem = psutil.virtual_memory().percent
    
    # macOS aggressively uses memory, so we set a higher threshold (85%) for "idle".
    if cpu < 40 and mem < 85:
        mood = "idle"
    elif cpu < 80 and mem < 95:
        mood = "working"
    else:
        mood = "alert"
    return {"cpu": cpu, "memory": mem, "mood": mood}

# ---------- Chat request model ----------
class ChatRequest(BaseModel):
    message: str

# ---------- Chat endpoint ----------
@app.post("/chat")
def chat(req: ChatRequest):
    # 1. Retrieve relevant past conversations
    query_embedding = embedder.encode(req.message).tolist()
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=2
    )
    retrieved_docs = results['documents'][0] if results['documents'] else []
    
    messages = []
    # Inject memories as actual chat history
    if retrieved_docs:
        for doc in reversed(retrieved_docs):
            parts = doc.split("\nPet: ")
            if len(parts) == 2:
                u_msg = parts[0].replace("User: ", "").strip()
                p_msg = parts[1].strip()
                messages.append(f"User: {u_msg}")
                messages.append(f"Pet: {p_msg}")
                
    messages.append(f"User: {req.message}")
    
    # 2. Run agent
    state = {"messages": messages, "next": "chat"}
    try:
        final_state = agent.invoke(state, {"recursion_limit": 6})
        
        # 3. Extract final assistant message
        assistant_msgs = [msg for msg in final_state["messages"] if msg.startswith("Pet: ")]
        if assistant_msgs:
            reply = assistant_msgs[-1].replace("Pet: ", "")
        else:
            reply = "I got confused!"
    except Exception as e:
        import traceback
        traceback.print_exc()
        reply = "My brain got stuck in a loop! Try asking differently."

    # Clean up any trailing tokens from the model
    reply = reply.replace("<|assistant|>", "").replace("<|end|>", "").strip()

    # Store conversation ONLY if it's not an error message
    if "My brain got stuck in a loop" not in reply:
        conversation_text = f"User: {req.message}\nPet: {reply}"
        embedding = embedder.encode(conversation_text).tolist()
        doc_id = str(datetime.datetime.now().timestamp())
        collection.add(
            documents=[conversation_text],
            embeddings=[embedding],
            ids=[doc_id]
        )

    return {"response": reply}