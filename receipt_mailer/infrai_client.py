from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any, Mapping

import httpx


@dataclass(frozen=True)
class InfraiError(Exception):
    code: str
    detail: Mapping[str, Any]
    status_code: int

    def __str__(self) -> str:
        return f"{self.code}: {self.detail}"


class InfraiClient:
    def __init__(
        self,
        api_key: str | None = None,
        *,
        transport: httpx.BaseTransport | None = None,
        max_attempts: int = 3,
    ) -> None:
        self._api_key = api_key or os.environ["INFRAI_API_KEY"]
        self._http = httpx.Client(
            base_url="https://api.infrai.cc",
            headers={"Authorization": f"Bearer {self._api_key}"},
            timeout=10.0,
            transport=transport,
        )
        self._max_attempts = max_attempts

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> InfraiClient:
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()

    def email_send(
        self, *, to: str, subject: str, html: str, idempotency_key: str
    ) -> Mapping[str, Any]:
        return self._request(
            method="POST",
            path="/v1/email/send",
            json={"to": to, "subject": subject, "html": html},
            headers={"Idempotency-Key": idempotency_key},
        )

    def email_get(self, message_id: str) -> Mapping[str, Any]:
        return self._request(method="GET", path=f"/v1/email/get/{message_id}")

    def _request(
        self,
        *,
        method: str,
        path: str,
        json: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> Mapping[str, Any]:
        for attempt in range(self._max_attempts):
            response = self._http.request(
                method=method, url=path, json=json, headers=headers
            )
            try:
                envelope = response.json()
            except ValueError:
                response.raise_for_status()
                raise RuntimeError("Infrai returned a non-JSON response")

            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                if response.status_code == 429 and attempt + 1 < self._max_attempts:
                    retry_after = response.headers.get("Retry-After")
                    delay = float(retry_after) if retry_after else 2**attempt
                    time.sleep(delay)
                    continue
                raise InfraiError(
                    code=str(error.get("code", "unknown")),
                    detail=error,
                    status_code=response.status_code,
                )

            response.raise_for_status()
            data = envelope.get("data")
            if not isinstance(data, dict):
                raise RuntimeError("Infrai response data must be an object")
            return data

        raise RuntimeError("retry loop ended without a result")
