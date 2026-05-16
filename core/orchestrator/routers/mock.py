"""MockRouter — canned responses for tests without LLM dependencies."""
import time
from .base import Router

class MockRouter(Router):
    name = "mock"
    def __init__(self, canned_text: str = "MOCK_RESPONSE"):
        self.canned = canned_text
    def complete(self, prompt, system=None, max_tokens=1024):
        t0 = time.time()
        return {
            "text": self.canned,
            "tokens_input": len(prompt) // 4,
            "tokens_output": len(self.canned) // 4,
            "duration_ms": int((time.time() - t0) * 1000),
            "success": True, "error": None,
        }
