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
    # S8: half-open single-probe. After the reset window elapses, the breaker
    # admits exactly ONE trial call (the probe) instead of hard-resetting and
    # flooding a still-sick provider with every queued caller at once. The probe
    # alone decides the next state: success closes, failure re-opens.
    half_open: bool = False
    probe_in_flight: bool = False


class CircuitBreakerRegistry:
    def __init__(self) -> None:
        self._states: dict[str, CircuitState] = defaultdict(CircuitState)
        self._lock = threading.Lock()

    def before_call(self, provider: str) -> None:
        with self._lock:
            state = self._states[provider]
            if state.opened_at is None:
                if state.half_open and state.probe_in_flight:
                    # A probe is already out; hold everyone else back so we
                    # don't stampede the recovering provider.
                    raise CircuitOpenError(
                        f"Provider circuit is half-open for '{provider}' "
                        "(probe in flight)"
                    )
                if state.half_open:
                    state.probe_in_flight = True
                return
            if (
                time.time() - state.opened_at
                >= settings.provider_circuit_reset_seconds
            ):
                # Reset window elapsed: enter half-open and let THIS caller be
                # the single probe. We intentionally do not zero failures yet —
                # only a successful probe fully closes the breaker.
                state.opened_at = None
                state.half_open = True
                state.probe_in_flight = True
                return
            raise CircuitOpenError(
                f"Provider circuit is open for '{provider}'"
            )

    def record_success(self, provider: str) -> None:
        with self._lock:
            state = self._states[provider]
            state.failures = 0
            state.opened_at = None
            state.half_open = False
            state.probe_in_flight = False

    def record_failure(self, provider: str) -> None:
        with self._lock:
            state = self._states[provider]
            if state.half_open:
                # A half-open probe failed: re-open immediately for another full
                # reset window rather than counting toward the closed-state
                # threshold.
                state.opened_at = time.time()
                state.half_open = False
                state.probe_in_flight = False
                state.failures = max(
                    state.failures, settings.provider_circuit_failure_threshold
                )
                return
            state.failures += 1
            if state.failures >= settings.provider_circuit_failure_threshold:
                state.opened_at = time.time()

    def status(self) -> list[dict[str, object]]:
        now = time.time()
        with self._lock:
            result: list[dict[str, object]] = []
            for provider, state in sorted(self._states.items()):
                if (
                    state.opened_at is not None
                    and now - state.opened_at
                    < settings.provider_circuit_reset_seconds
                ):
                    label = "open"
                elif state.half_open:
                    label = "half_open"
                else:
                    label = "closed"
                result.append(
                    {
                        "provider": provider,
                        "state": label,
                        "failures": state.failures,
                        "opened_at_epoch": state.opened_at,
                    }
                )
            return result

    def reset(self) -> None:
        with self._lock:
            self._states.clear()


gateway_limiter = GatewayLimiter()
circuit_breakers = CircuitBreakerRegistry()
