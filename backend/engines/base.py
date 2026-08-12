"""Abstract base class that all inference engines must implement."""

from abc import ABC, abstractmethod
from typing import List, Dict


class BaseEngine(ABC):
    """Interface for LLM inference engines (offline and online)."""

    @abstractmethod
    def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate a response from the model.

        Args:
            messages: List of {"role": "system"|"user"|"assistant", "content": "..."} dicts.
            **kwargs: Engine-specific parameters (max_tokens, temperature, etc.).

        Returns:
            The assistant's reply as a plain string.
        """
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Return True if the engine is available and ready to serve requests."""
        pass
