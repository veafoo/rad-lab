"""ClaudeCodeRouter — subprocess wrapper for `claude -p` CLI (uses Pro quota)."""
import shutil, subprocess, time
from typing import Optional
from .base import Router

class ClaudeCodeRouter(Router):
    name = "claude_code_cli"
    def __init__(self, model_flag: Optional[str] = None):
        self.model_flag = model_flag

    def complete(self, prompt: str, system: Optional[str] = None, max_tokens: int = 1024) -> dict:
        t0 = time.time()
        if not shutil.which("claude"):
            return {"text": "", "tokens_input": 0, "tokens_output": 0,
                    "duration_ms": 0, "success": False, "error": "claude CLI not in PATH"}
        full_prompt = (system + "\n\n" + prompt) if system else prompt
        cmd = ["claude", "-p", full_prompt]
        if self.model_flag:
            cmd.extend(["--model", self.model_flag])
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            return {
                "text": r.stdout.strip(),
                "tokens_input": len(full_prompt) // 4,
                "tokens_output": len(r.stdout) // 4,
                "duration_ms": int((time.time() - t0) * 1000),
                "success": r.returncode == 0,
                "error": r.stderr.strip() if r.returncode != 0 else None,
            }
        except subprocess.TimeoutExpired:
            return {"text": "", "tokens_input": 0, "tokens_output": 0,
                    "duration_ms": int((time.time() - t0) * 1000),
                    "success": False, "error": "timeout 300s"}

    @staticmethod
    def is_available() -> bool:
        return shutil.which("claude") is not None
