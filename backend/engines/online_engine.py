"""Online inference engine using Nemotron 3.5 Lightning via OpenRouter API."""

import logging
from typing import List, Dict

import httpx
from config import settings
from .base import BaseEngine

logger = logging.getLogger(__name__)


class OnlineEngine(BaseEngine):
    """Cloud-based Nemotron 3.5 Lightning model via OpenRouter's OpenAI-compatible API."""

    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        self.url = settings.OPENROUTER_API_URL
        self.model = settings.OPENROUTER_MODEL
        self.timeout = settings.OPENROUTER_TIMEOUT
        self.max_retries = settings.OPENROUTER_MAX_RETRIES
        logger.info("Online engine configured: model=%s", self.model)

    def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Send messages to OpenRouter and return the assistant reply."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 4096),
            "top_p": kwargs.get("top_p", 0.9),
            "stream": False,
        }

        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    resp = client.post(self.url, headers=headers, json=payload)
                    resp.raise_for_status()
                    data = resp.json()
                    choice = data["choices"][0]["message"]

                    # Nemotron 3.5 Lightning is a reasoning model: the actual
                    # answer lives in "content", but reasoning uses tokens first.
                    # If content is null, fall back to the reasoning field.
                    content = choice.get("content")
                    if content:
                        return content.strip()

                    # Try reasoning field as fallback
                    reasoning = choice.get("reasoning", "")
                    if reasoning:
                        return reasoning.strip()

                    return "I could not generate a response."
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "Online API attempt %d/%d failed: %s",
                    attempt + 1,
                    self.max_retries + 1,
                    exc,
                )

        raise RuntimeError(f"Online engine unavailable after {self.max_retries + 1} attempts") from last_error

    def health_check(self) -> bool:
        """Verify API reachability with a minimal request."""
        try:
            self.generate(
                [{"role": "user", "content": "ping"}],
                max_tokens=2,
            )
            return True
        except Exception:
            return False
