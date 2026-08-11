import chromadb
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_collection("chat_memory")
print(collection.get())
