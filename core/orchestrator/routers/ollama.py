"""OllamaRouter — HTTP client to local Ollama server (localhost:11434)."""
import json, time, urllib.request, urllib.error
from typing import Optional
from .base import Router

class OllamaRouter(Router):
    name = "ollama"
    def __init__(self, model: str = "qwen2.5-coder:7b", host: str = "http://localhost:11434"):
        self.model = model
        self.host = host

    def complete(self, prompt: str, system: Optional[str] = None, max_tokens: int = 1024) -> dict:
        t0 = time.time()
        payload = {"model": self.model, "prompt": prompt, "system": system or "",
                   "stream": False, "options": {"num_predict": max_tokens}}
        try:
            req = urllib.request.Request(
                f"{self.host}/api/generate",
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read())
            return {
                "text": data.get("response", ""),
                "tokens_input": data.get("prompt_eval_count", 0),
                "tokens_output": data.get("eval_count", 0),
                "duration_ms": int((time.time() - t0) * 1000),
                "success": True, "error": None,
            }
        except (urllib.error.URLError, ConnectionError, TimeoutError) as e:
            return {"text": "", "tokens_input": 0, "tokens_output": 0,
                    "duration_ms": int((time.time() - t0) * 1000),
                    "success": False, "error": f"{type(e).__name__}: {e}"}

    @staticmethod
    def is_available(host: str = "http://localhost:11434") -> bool:
        try:
            with urllib.request.urlopen(f"{host}/api/tags", timeout=2) as resp:
                return resp.status == 200
        except Exception:
            return False
