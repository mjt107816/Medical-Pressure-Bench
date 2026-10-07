from __future__ import annotations

import json
import time
from http.client import RemoteDisconnected
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .api_config import APISettings


def chat_completion(api: APISettings, *, system_prompt: str, user_prompt: str) -> str:
    return chat_completion_with_meta(api, system_prompt=system_prompt, user_prompt=user_prompt)["text"]


def chat_completion_with_meta(api: APISettings, *, system_prompt: str, user_prompt: str) -> dict:
    if api.provider == "anthropic":
        payload = {"model": api.model, "system": system_prompt, "messages": [{"role": "user", "content": user_prompt}], "temperature": api.temperature, "max_tokens": api.max_tokens}
        headers = {"Content-Type": "application/json", "x-api-key": api.api_key, "anthropic-version": "2023-06-01"}
        endpoint = _url(api.api_base, api.api_endpoint)
    else:
        payload = {"model": api.model, "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}], "temperature": api.temperature, "max_tokens": api.max_tokens}
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api.api_key}"}
        endpoint = _url(api.api_base, api.api_endpoint)
    req = Request(endpoint, data=json.dumps(payload).encode(), headers=headers, method="POST")
    last_error: Exception | None = None
    errors: list[dict] = []
    started = time.monotonic()
    attempts_used = 0
    for attempt in range(1, 5):
        attempts_used = attempt
        try:
            with urlopen(req, timeout=max(5, api.timeout_sec)) as response:
                body = json.loads(response.read().decode("utf-8"))
            break
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore") if hasattr(exc, "read") else str(exc)
            last_error = RuntimeError(f"API HTTP {exc.code}: {detail[:500]}")
            errors.append({"attempt": attempt, "error_type": "HTTPError", "status_code": exc.code, "detail": detail[:300]})
            retryable = exc.code == 429 or exc.code >= 500
            if not retryable or attempt == 4:
                raise last_error from exc
        except (URLError, RemoteDisconnected, TimeoutError, ConnectionResetError, json.JSONDecodeError) as exc:
            last_error = RuntimeError(f"API transient error on attempt {attempt}: {exc}")
            errors.append({"attempt": attempt, "error_type": type(exc).__name__, "detail": str(exc)[:300]})
            if attempt == 4:
                raise last_error from exc
        time.sleep(min(2 ** (attempt - 1), 8))
    else:
        raise last_error or RuntimeError("API request failed after retries")
    if api.provider == "anthropic":
        text = "\n".join(str(x.get("text", "")) for x in body.get("content", []) if isinstance(x, dict)).strip()
    else:
        choices = body.get("choices", [])
        text = str(choices[0].get("message", {}).get("content", "")).strip() if choices else ""
    return {
        "text": text,
        "attempts": attempts_used,
        "retry_count": max(0, attempts_used - 1),
        "errors": errors,
        "latency_ms": round((time.monotonic() - started) * 1000, 1),
        "http_status": 200,
        "response_nonempty": bool(text),
    }


def _url(base: str, endpoint: str) -> str:
    return str(base).rstrip("/") + "/" + str(endpoint).lstrip("/")
