"""Retry policy composition: combines backoff, condition, budget, and circuit breaker
into a single decision point for the retry loop."""
from dataclasses import dataclass, field
from typing import Optional

from retryctl.backoff import ExponentialBackoff, BackoffConfig
from retryctl.condition import ConditionEvaluator, ConditionConfig
from retryctl.budget import BudgetState, BudgetConfig
from retryctl.circuit_breaker import CircuitBreaker, CircuitBreakerConfig, CircuitState


@dataclass
class PolicyConfig:
    backoff: BackoffConfig = field(default_factory=BackoffConfig)
    condition: ConditionConfig = field(default_factory=ConditionConfig)
    budget: BudgetConfig = field(default_factory=BudgetConfig)
    circuit_breaker: CircuitBreakerConfig = field(default_factory=CircuitBreakerConfig)


@dataclass
class PolicyDecision:
    should_retry: bool
    reason: str
    delay: float = 0.0


class RetryPolicy:
    """Combines all retry sub-systems into a single should_retry / delay decision."""

    def __init__(self, config: PolicyConfig) -> None:
        self._backoff = ExponentialBackoff(config.backoff)
        self._condition = ConditionEvaluator(config.condition)
        self._budget = BudgetState(config.budget)
        self._circuit = CircuitBreaker(config.circuit_breaker)

    # ------------------------------------------------------------------
    def evaluate(self, exit_code: int, output: str = "") -> PolicyDecision:
        """Return a PolicyDecision for the given attempt result."""
        if self._circuit.state == CircuitState.OPEN:
            return PolicyDecision(False, "circuit open")

        if not self._condition.should_retry(exit_code, output):
            return PolicyDecision(False, "condition not met")

        if not self._budget.record_retry():
            return PolicyDecision(False, "retry budget exhausted")

        delay = self._backoff.attempt()
        if delay is None:
            return PolicyDecision(False, "max attempts reached")

        self._circuit.record_failure()
        return PolicyDecision(True, "retry scheduled", delay=delay)

    def record_success(self) -> None:
        """Notify sub-systems of a successful attempt."""
        self._backoff.reset()
        self._circuit.record_success()

    def reset(self) -> None:
        """Full reset of all stateful sub-systems."""
        self._backoff.reset()
        self._circuit.reset()
