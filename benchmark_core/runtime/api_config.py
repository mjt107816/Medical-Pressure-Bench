from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass
class APISettings:
    provider: str = "openai"
    model: str = ""
    api_base: str = ""
    api_endpoint: str = ""
    api_key: str = ""
    timeout_sec: int = 60
    temperature: float = 0.0
    max_tokens: int = 512

    def validate(self) -> list[str]:
        issues = []
        if self.provider not in {"openai", "openrouter", "anthropic"}:
            issues.append("provider must be openai/openrouter/anthropic")
        if not self.model:
            issues.append("model is required")
        if not self.api_key:
            issues.append(f"missing API key for provider={self.provider}")
        parsed_base = urlparse(self.api_base)
        if parsed_base.scheme not in {"http", "https"} or not parsed_base.netloc:
            issues.append("api_base must be a complete HTTP(S) URL")
        if not self.api_endpoint.startswith("/"):
            issues.append("api_endpoint must start with '/'")
        return issues

    def public_dict(self) -> dict:
        return {
            "provider": self.provider,
            "model": self.model,
            "timeout_sec": self.timeout_sec,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }


def load_api_settings(cfg: dict | None = None) -> APISettings:
    cfg = cfg or {}
    provider = str(cfg.get("provider") or os.getenv("BENCH_API_PROVIDER", "openai")).lower()
    key = str(cfg.get("api_key") or os.getenv("BENCH_API_KEY", "") or os.getenv(_key_env(provider), ""))
    return APISettings(
        provider=provider,
        model=str(cfg.get("model") or os.getenv("BENCH_MODEL", "")),
        api_base=str(cfg.get("api_base") or os.getenv("BENCH_API_BASE", "")),
        api_endpoint=str(cfg.get("api_endpoint") or os.getenv("BENCH_API_ENDPOINT", "")),
        api_key=key,
        timeout_sec=int(cfg.get("timeout_sec", os.getenv("BENCH_TIMEOUT_SEC", 60))),
        max_tokens=int(cfg.get("max_tokens", 512)),
    )


def _key_env(provider: str) -> str:
    return {"anthropic": "ANTHROPIC_API_KEY", "openrouter": "OPENROUTER_API_KEY"}.get(provider, "OPENAI_API_KEY")
