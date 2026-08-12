"""Inference engine manager that routes requests to offline or online engines."""

import logging
from typing import List, Dict

from config import settings
from .offline_engine import OfflineEngine
from .online_engine import OnlineEngine

logger = logging.getLogger(__name__)


class InferenceManager:
    """Routes inference requests to the appropriate engine based on selected mode.

    Modes:
        offline - Always uses local Phi-3 model. No internet required.
        online  - Always uses Nemotron 3.5 via OpenRouter. Raises on failure.
        auto    - Tries online first; falls back to offline silently on failure.
    """

    def __init__(self):
        # Offline engine is always loaded (it's the safety net)
        self.offline = OfflineEngine()

        # Online engine is only initialized if an API key is configured
        if settings.OPENROUTER_API_KEY:
            self.online = OnlineEngine()
            logger.info("InferenceManager ready: offline + online engines loaded.")
        else:
            self.online = None
            logger.warning(
                "No OPENROUTER_API_KEY set. Online mode is disabled; "
                "only offline inference is available."
            )

    def get_response(
        self,
        messages: List[Dict[str, str]],
        mode: str = "auto",
        **kwargs,
    ) -> tuple[str, str]:
        """Generate a response using the selected mode.

        Returns:
            A tuple of (reply_text, mode_actually_used).
        """
        if mode == "offline":
            return self.offline.generate(messages, **kwargs), "offline"

        if mode == "online":
            if self.online is None:
                raise ValueError("Online mode not configured (no API key in .env).")
            return self.online.generate(messages, **kwargs), "online"

        # mode == "auto": try online first, fall back to offline
        if self.online:
            try:
                reply = self.online.generate(messages, **kwargs)
                return reply, "online"
            except Exception as exc:
                logger.warning("Auto mode: online failed (%s), falling back to offline.", exc)

        return self.offline.generate(messages, **kwargs), "offline"
