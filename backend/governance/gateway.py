from __future__ import annotations

import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass

from backend.config.settings import settings


class GatewayLimitExceeded(RuntimeError):
    pass


class CircuitOpenError(RuntimeError):
    pass


class GatewayLimiter:
    def __init__(self) -> None:
        self._requests: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def check_rate(self, key: str, *, now: float | None = None) -> None:
        timestamp = now if now is not None else time.time()
        cutoff = timestamp - 60
        with self._lock:
            bucket = self._requests[key]
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()
            if len(bucket) >= settings.gateway_requests_per_minute:
                raise GatewayLimitExceeded(
                    "Gateway request rate limit exceeded"
                )
            bucket.append(timestamp)

    def reset(self) -> None:
        with self._lock:
            self._requests.clear()


@dataclass
class CircuitState:
    failures: int = 0
    opened_at: float | None = None


class CircuitBreakerRegistry:
    def __init__(self) -> None:
        self._states: dict[str, CircuitState] = defaultdict(CircuitState)
        self._lock = threading.Lock()

    def before_call(self, provider: str) -> None:
        with self._lock:
            state = self._states[provider]
            if state.opened_at is None:
                return
            if (
                time.time() - state.opened_at
                >= settings.provider_circuit_reset_seconds
            ):
                state.failures = 0
                state.opened_at = None
                return
            raise CircuitOpenError(
                f"Provider circuit is open for '{provider}'"
            )

    def record_success(self, provider: str) -> None:
        with self._lock:
            state = self._states[provider]
            state.failures = 0
            state.opened_at = None

    def record_failure(self, provider: str) -> None:
        with self._lock:
            state = self._states[provider]
            state.failures += 1
            if state.failures >= settings.provider_circuit_failure_threshold:
                state.opened_at = time.time()

    def status(self) -> list[dict[str, object]]:
        now = time.time()
        with self._lock:
            return [
                {
                    "provider": provider,
                    "state": (
                        "open"
                        if state.opened_at is not None
                        and now - state.opened_at
                        < settings.provider_circuit_reset_seconds
                        else "closed"
                    ),
                    "failures": state.failures,
                    "opened_at_epoch": state.opened_at,
                }
                for provider, state in sorted(self._states.items())
            ]

    def reset(self) -> None:
        with self._lock:
            self._states.clear()


gateway_limiter = GatewayLimiter()
circuit_breakers = CircuitBreakerRegistry()
