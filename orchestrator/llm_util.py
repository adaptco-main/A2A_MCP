"""Orchestration-facing LLM service built on internal adapter abstractions."""
from __future__ import annotations

from dotenv import load_dotenv

from orchestrator.llm_adapters.base import InternalLLMRequest, InternalLLMResponse
from orchestrator.llm_adapters.registry import LLMAdapterRegistry

load_dotenv()


class LLMService:
    """High-level service for LLM generation through provider adapters."""

    def __init__(self, registry: LLMAdapterRegistry | None = None):
        self.registry = registry or LLMAdapterRegistry()

    def generate(self, request: InternalLLMRequest) -> InternalLLMResponse:
        """Execute generation via provider resolved from routing policy."""
        adapter = self.registry.resolve(request)
        return adapter.generate(request)

    def generate_text(self, request: InternalLLMRequest) -> str:
        """Convenience wrapper that returns only generated content."""
        return self.generate(request).content

    # Backwards compatibility while call sites are migrated.
    def call_llm(self, prompt: str, system_prompt: str = "You are a helpful coding assistant.") -> str:
        request = InternalLLMRequest(prompt=prompt, system_prompt=system_prompt)
        return self.generate_text(request)
