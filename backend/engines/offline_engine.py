"""Offline inference engine using Phi-3-mini GGUF via llama-cpp-python."""

import logging
from typing import List, Dict

from llama_cpp import Llama
from config import settings
from .base import BaseEngine

logger = logging.getLogger(__name__)


class OfflineEngine(BaseEngine):
    """Local Phi-3 model for private, zero-latency inference."""

    def __init__(self):
        logger.info("Loading offline model from %s", settings.PHI_MODEL_PATH)
        self.model = Llama(
            model_path=settings.PHI_MODEL_PATH,
            n_ctx=2048,
            n_threads=4,
            verbose=False,
        )
        logger.info("Offline model loaded successfully.")

    def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Convert standard messages to Phi-3 chat template and run inference."""
        prompt = self._build_phi3_prompt(messages)

        # Reset KV cache to prevent segfaults on repeated calls
        if hasattr(self.model, "reset"):
            self.model.reset()

        output = self.model(
            prompt=prompt,
            max_tokens=kwargs.get("max_tokens", 150),
            temperature=kwargs.get("temperature", 0.3),
            top_p=kwargs.get("top_p", 0.9),
            repeat_penalty=1.1,
            stop=["<|end|>", "<|user|>", "\nUser:"],
        )
        return output["choices"][0]["text"].strip()

    def health_check(self) -> bool:
        """Offline engine is always available once loaded."""
        return True

    @staticmethod
    def _build_phi3_prompt(messages: List[Dict[str, str]]) -> str:
        """Convert OpenAI-style messages to Phi-3 instruct format."""
        prompt = ""
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            if role == "system":
                prompt += f"<|system|>\n{content}<|end|>\n"
            elif role == "user":
                prompt += f"<|user|>\n{content}<|end|>\n"
            elif role == "assistant":
                prompt += f"<|assistant|>\n{content}<|end|>\n"
        prompt += "<|assistant|>\n"
        return prompt
