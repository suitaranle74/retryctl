"""Tests for policy_config_from_file bridge."""
import pytest
from retryctl.policy import PolicyConfig
from retryctl.policy_bridge import policy_config_from_file
from retryctl.config import FileConfig


def _make(**kwargs):
    defaults = dict(
        max_attempts=3,
        base_delay=1.0,
        multiplier=2.0,
        max_delay=30.0,
        retryable_exit_codes=[1, 2],
        output_patterns=[],
        budget_enabled=False,
        budget_max_retries=5,
        budget_window_seconds=60,
        circuit_breaker_enabled=False,
        circuit_breaker_failure_threshold=5,
        circuit_breaker_recovery_timeout=30,
    )
    defaults.update(kwargs)
    return FileConfig(**defaults)


class TestPolicyConfigFromFile:
    def test_returns_policy_config(self):
        result = policy_config_from_file(_make())
        assert isinstance(result, PolicyConfig)

    def test_backoff_forwarded(self):
        result = policy_config_from_file(_make(max_attempts=7, base_delay=2.0))
        assert result.backoff.max_attempts == 7
        assert result.backoff.base_delay == 2.0

    def test_condition_forwarded(self):
        result = policy_config_from_file(_make(retryable_exit_codes=[42, 99]))
        assert result.condition.retryable_exit_codes == [42, 99]

    def test_budget_forwarded(self):
        result = policy_config_from_file(_make(budget_enabled=True, budget_max_retries=3))
        assert result.budget.enabled is True
        assert result.budget.max_retries == 3

    def test_circuit_breaker_forwarded(self):
        result = policy_config_from_file(
            _make(circuit_breaker_enabled=True, circuit_breaker_failure_threshold=2)
        )
        assert result.circuit_breaker.enabled is True
        assert result.circuit_breaker.failure_threshold == 2

    def test_defaults_produce_valid_policy_config(self):
        """Default FileConfig should yield a usable PolicyConfig without error."""
        cfg = FileConfig()
        result = policy_config_from_file(cfg)
        assert isinstance(result, PolicyConfig)
