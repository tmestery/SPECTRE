import httpx

from spectre.config import settings
from spectre.llm.types import LLMCompletionResult, LLMMessage


class LLMClient:
    def __init__(
        self,
        *,
        provider: str,
        api_key: str,
        model: str,
        base_url: str,
        timeout: float = 60.0,
    ) -> None:
        self.provider = provider
        self.api_key = api_key.strip()
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=self._headers(),
            timeout=self.timeout,
        )

    @classmethod
    def from_settings(cls) -> "LLMClient":
        return cls(
            provider=settings.llm_provider,
            api_key=settings.llm_api_key,
            model=settings.llm_model,
            base_url=settings.llm_base_url_resolved,
            timeout=settings.llm_timeout_seconds,
        )

    @property
    def available(self) -> bool:
        return settings.llm_enabled and bool(self.api_key)

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def close(self) -> None:
        await self._client.aclose()

    async def complete(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.2,
        json_mode: bool = False,
    ) -> LLMCompletionResult:
        if not self.available:
            raise RuntimeError("LLM is not configured (missing API key or disabled)")

        payload: dict = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        from spectre.safety.audit import AuditTimer

        timer = AuditTimer()
        response = await self._client.post("/chat/completions", json=payload)
        if response.is_error:
            detail = response.text[:300]
            try:
                err = response.json().get("error") or {}
                if isinstance(err, dict) and err.get("message"):
                    detail = str(err["message"])
            except Exception:
                pass
            raise RuntimeError(
                f"LLM request failed ({self.provider} {self.model}): "
                f"HTTP {response.status_code} — {detail}"
            )
        data = response.json()
        choice = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        return LLMCompletionResult(
            content=str(choice),
            model=self.model,
            provider=self.provider,
            prompt_tokens=int(usage.get("prompt_tokens", 0)),
            completion_tokens=int(usage.get("completion_tokens", 0)),
            duration_ms=timer.elapsed_ms(),
        )

    async def complete_json(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.1,
    ) -> tuple[dict, LLMCompletionResult]:
        result = await self.complete(messages, temperature=temperature, json_mode=True)
        from spectre.llm.json_utils import extract_json_object

        return extract_json_object(result.content), result


class MockLLMClient(LLMClient):
    """Deterministic LLM responses for tests."""

    def __init__(self, responses: dict[str, str] | None = None, queue: list[str] | None = None) -> None:
        super().__init__(
            provider="mock",
            api_key="mock-key",
            model="mock-model",
            base_url="http://mock.local",
        )
        self._responses = responses or {}
        self._queue = list(queue or [])

    @property
    def available(self) -> bool:
        return True

    async def complete_json(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.1,
    ) -> tuple[dict, LLMCompletionResult]:
        if self._queue:
            content = self._queue.pop(0)
        else:
            joined = "\n".join(m.content for m in messages)
            content = self._default_response(joined, json_mode=True)
            for key, value in self._responses.items():
                if key in joined:
                    content = value
                    break
        from spectre.llm.json_utils import extract_json_object

        parsed = extract_json_object(content)
        result = LLMCompletionResult(
            content=content,
            model=self.model,
            provider=self.provider,
            prompt_tokens=10,
            completion_tokens=20,
            duration_ms=1,
        )
        return parsed, result

    async def complete(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.2,
        json_mode: bool = False,
    ) -> LLMCompletionResult:
        joined = "\n".join(m.content for m in messages)
        content = self._default_response(joined, json_mode=json_mode)
        for key, value in self._responses.items():
            if key in joined:
                content = value
                break
        return LLMCompletionResult(
            content=content,
            model=self.model,
            provider=self.provider,
            prompt_tokens=10,
            completion_tokens=20,
            duration_ms=1,
        )

    async def close(self) -> None:
        return None

    def _default_response(self, prompt: str, *, json_mode: bool) -> str:
        if json_mode:
            if "surface" in prompt.lower() or "attack surface" in prompt.lower():
                return (
                    '{"summary":"Mock attack surface review.",'
                    '"risk_areas":["dependencies","ci workflows"],'
                    '"recommended_focus":"Scan dependency manifests and GitHub Actions."}'
                )
            if "secret" in prompt.lower():
                return (
                    '{"summary":"Mock secret triage.",'
                    '"priorities":[{"finding_title":"Potential secret",'
                    '"priority":"high","rationale":"High-confidence credential pattern."}]}'
                )
            if "cve" in prompt.lower() or "vulnerability" in prompt.lower():
                return (
                    '{"summary":"Mock CVE prioritization.",'
                    '"ranked":[{"cve_id":"CVE-0000-0000","priority":"medium",'
                    '"rationale":"Reachable dependency path uncertain."}]}'
                )
            if "validation" in prompt.lower():
                return (
                    '{"summary":"Mock validation review.",'
                    '"confirmed_count":1,"false_positive_risk":"low",'
                    '"narrative":"One secret format validated; continue to report."}'
                )
            if "executive" in prompt.lower():
                return (
                    '{"executive_summary":"Mock executive summary for authorized repo audit.",'
                    '"top_risks":["exposed credentials","outdated dependencies"],'
                    '"recommended_actions":["rotate secrets","patch dependencies"]}'
                )
            return '{"summary":"mock"}'
        return "Mock LLM analysis complete."
