"""Ollama inference provider with explicit, per-request sampling parameters.

Determinism rule (house PB-071): sampling options travel in every request.
Telemetry (token counts, timings) is returned with each call so the runner
can enforce budgets and the trace can carry the evidence.
"""

from __future__ import annotations

import json
import urllib.request


class ProviderError(RuntimeError):
    pass


class OllamaProvider:
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "granite-code:8b",
        temperature: float = 0.0,
        seed: int = 42,
        num_ctx: int = 4096,
        keep_alive: str = "30m",
        timeout_s: int = 300,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        # Sampling contract — merged into every request payload.
        self.options = {"temperature": temperature, "seed": seed, "num_ctx": num_ctx}
        self.keep_alive = keep_alive
        self.timeout_s = timeout_s

    def _post(self, path: str, payload: dict) -> dict:
        url = self.base_url + path
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            url, data=data, headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_s) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")[:500]
            raise ProviderError(f"{path} -> HTTP {exc.code}: {body}") from exc
        except urllib.error.URLError as exc:
            raise ProviderError(f"{path} -> connection failed: {exc.reason}") from exc

    def version(self) -> str:
        with urllib.request.urlopen(self.base_url + "/api/version", timeout=30) as response:
            return json.loads(response.read().decode("utf-8")).get("version", "unknown")

    def model_info(self) -> dict:
        """Pin the loaded model via /api/ps (CN-001: /api/show exposes no digest)."""
        try:
            with urllib.request.urlopen(self.base_url + "/api/ps", timeout=30) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise ProviderError(f"/api/ps -> connection failed: {exc.reason}") from exc
        for entry in data.get("models", []):
            if entry.get("name", "").split(":")[0] == self.model.split(":")[0]:
                return {
                    "digest": entry.get("digest", "unknown"),
                    "size_vram": entry.get("size_vram", 0),
                }
        return {"digest": "not-loaded", "size_vram": 0}

    def chat(self, messages: list[dict]) -> dict:
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": dict(self.options),
            "keep_alive": self.keep_alive,
        }
        response = self._post("/api/chat", payload)
        message = response.get("message") or {}
        eval_count = response.get("eval_count", 0)
        prompt_eval_count = response.get("prompt_eval_count", 0)
        total_duration_ns = response.get("total_duration", 0)
        return {
            "content": message.get("content", ""),
            "usage": {
                "prompt_tokens": prompt_eval_count,
                "eval_tokens": eval_count,
                "total_tokens": prompt_eval_count + eval_count,
            },
            "total_duration_ms": round(total_duration_ns / 1e6, 1),
        }
