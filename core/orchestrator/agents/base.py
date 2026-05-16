"""Agent base class — wraps a Router with structured I/O and metric logging."""
from abc import ABC, abstractmethod
from core.orchestrator.routers.base import Router

class Agent(ABC):
    agent_id: str = "base"
    tier: str = "default"

    def __init__(self, router: Router):
        self.router = router

    @abstractmethod
    def run(self, inputs: dict) -> dict:
        """Returns {success, output, metrics}"""
        ...

    def log_invocation(self, success: bool, duration_ms: int, tokens_in: int, tokens_out: int, error=None):
        from core.orchestrator.memory.index_db import log_agent_invocation
        log_agent_invocation(
            agent_id=self.agent_id, duration_ms=duration_ms,
            tokens_input=tokens_in, tokens_output=tokens_out,
            router=self.router.name, success=success, error=error,
        )
