"""Tests for RetryPolicy and PolicyConfig."""
import pytest
from retryctl.policy import PolicyConfig, PolicyDecision, RetryPolicy
from retryctl.backoff import BackoffConfig
from retryctl.condition import ConditionConfig
from retryctl.budget import BudgetConfig
from retryctl.circuit_breaker import CircuitBreakerConfig


def _make(
    max_attempts=5,
    retryable_exit_codes=None,
    budget_enabled=False,
    cb_enabled=False,
    cb_threshold=3,
):
    return PolicyConfig(
        backoff=BackoffConfig(max_attempts=max_attempts, base_delay=0.0, multiplier=1.0, max_delay=0.0),
        condition=ConditionConfig(retryable_exit_codes=retryable_exit_codes or [1]),
        budget=BudgetConfig(enabled=budget_enabled, max_retries=2, window_seconds=60),
        circuit_breaker=CircuitBreakerConfig(enabled=cb_enabled, failure_threshold=cb_threshold),
    )


class TestPolicyConfig:
    def test_defaults(self):
        cfg = PolicyConfig()
        assert isinstance(cfg.backoff, BackoffConfig)
        assert isinstance(cfg.condition, ConditionConfig)
        assert isinstance(cfg.budget, BudgetConfig)
        assert isinstance(cfg.circuit_breaker, CircuitBreakerConfig)


class TestRetryPolicy:
    def test_should_retry_on_retryable_exit_code(self):
        policy = RetryPolicy(_make())
        decision = policy.evaluate(exit_code=1)
        assert decision.should_retry is True
        assert decision.delay >= 0.0

    def test_no_retry_on_success_exit_code(self):
        policy = RetryPolicy(_make())
        decision = policy.evaluate(exit_code=0)
        assert decision.should_retry is False
        assert decision.reason == "condition not met"

    def test_no_retry_when_max_attempts_exhausted(self):
        policy = RetryPolicy(_make(max_attempts=1))
        policy.evaluate(exit_code=1)  # consumes the only attempt
        decision = policy.evaluate(exit_code=1)
        assert decision.should_retry is False
        assert decision.reason == "max attempts reached"

    def test_no_retry_when_budget_exhausted(self):
        policy = RetryPolicy(_make(max_attempts=10, budget_enabled=True))
        policy.evaluate(exit_code=1)
        policy.evaluate(exit_code=1)
        decision = policy.evaluate(exit_code=1)  # budget allows only 2
        assert decision.should_retry is False
        assert decision.reason == "retry budget exhausted"

    def test_no_retry_when_circuit_open(self):
        policy = RetryPolicy(_make(max_attempts=10, cb_enabled=True, cb_threshold=2))
        policy.evaluate(exit_code=1)
        policy.evaluate(exit_code=1)
        decision = policy.evaluate(exit_code=1)  # circuit should be open now
        assert decision.should_retry is False
        assert decision.reason == "circuit open"

    def test_record_success_resets_backoff(self):
        policy = RetryPolicy(_make())
        policy.evaluate(exit_code=1)
        policy.record_success()
        # After success, a fresh evaluation should still allow retry
        decision = policy.evaluate(exit_code=1)
        assert decision.should_retry is True

    def test_reset_clears_state(self):
        policy = RetryPolicy(_make(max_attempts=1))
        policy.evaluate(exit_code=1)
        policy.reset()
        decision = policy.evaluate(exit_code=1)
        assert decision.should_retry is True

    def test_decision_reason_on_success(self):
        policy = RetryPolicy(_make())
        decision = policy.evaluate(exit_code=1)
        assert decision.reason == "retry scheduled"
