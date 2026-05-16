"""Router base class — abstracts LLM call (Ollama, Claude CLI, Anthropic API, etc.)"""
from abc import ABC, abstractmethod
from typing import Optional

class Router(ABC):
    name: str = "base"
    @abstractmethod
    def complete(self, prompt: str, system: Optional[str] = None, max_tokens: int = 1024) -> dict:
        """Returns {text, tokens_input, tokens_output, duration_ms, success, error}"""
        ...
