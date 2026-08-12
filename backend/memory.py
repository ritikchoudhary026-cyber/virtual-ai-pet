"""Shared Chroma RAG memory used by both offline and online engines."""

import logging
import datetime
from typing import List

import chromadb
from sentence_transformers import SentenceTransformer
from config import settings

logger = logging.getLogger(__name__)

# Module-level singletons (initialized once on import)
_chroma_client = chromadb.PersistentClient(path=settings.CHROMA_DB_PATH)
_collection = _chroma_client.get_or_create_collection(name="chat_memory")
_embedder = SentenceTransformer("all-MiniLM-L6-v2")


def retrieve_context(message: str, n_results: int = 2) -> List[str]:
    """Retrieve the most relevant past conversations for a given message.

    Returns:
        List of "User: ...\nPet: ..." document strings from Chroma.
    """
    query_embedding = _embedder.encode(message).tolist()
    results = _collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
    )
    return results["documents"][0] if results["documents"] else []


def store_conversation(user_msg: str, pet_reply: str) -> None:
    """Persist a conversation turn into Chroma for future retrieval.

    Skips storage if the reply is an error fallback message.
    """
    if "My brain got stuck in a loop" in pet_reply:
        return
    if "I got confused" in pet_reply:
        return

    conversation_text = f"User: {user_msg}\nPet: {pet_reply}"
    embedding = _embedder.encode(conversation_text).tolist()
    doc_id = str(datetime.datetime.now().timestamp())
    _collection.add(
        documents=[conversation_text],
        embeddings=[embedding],
        ids=[doc_id],
    )
    logger.debug("Stored conversation: %s", conversation_text[:80])
