"""Tests for CircuitBreakerConfig and CircuitBreaker."""
import time
import unittest
from unittest.mock import patch

from retryctl.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitState,
)


class TestCircuitBreakerConfig(unittest.TestCase):
    def test_defaults(self):
        cfg = CircuitBreakerConfig()
        self.assertFalse(cfg.enabled)
        self.assertEqual(cfg.failure_threshold, 5)
        self.assertEqual(cfg.recovery_timeout, 60.0)
        self.assertEqual(cfg.success_threshold, 1)

    def test_from_dict_full(self):
        cfg = CircuitBreakerConfig.from_dict(
            {"enabled": True, "failure_threshold": 3, "recovery_timeout": 30.0, "success_threshold": 2}
        )
        self.assertTrue(cfg.enabled)
        self.assertEqual(cfg.failure_threshold, 3)
        self.assertEqual(cfg.recovery_timeout, 30.0)
        self.assertEqual(cfg.success_threshold, 2)

    def test_from_dict_ignores_unknown_keys(self):
        cfg = CircuitBreakerConfig.from_dict({"enabled": True, "unknown": "x"})
        self.assertTrue(cfg.enabled)


def _make(enabled=True, failure_threshold=3, recovery_timeout=60.0, success_threshold=1):
    cfg = CircuitBreakerConfig(
        enabled=enabled,
        failure_threshold=failure_threshold,
        recovery_timeout=recovery_timeout,
        success_threshold=success_threshold,
    )
    return CircuitBreaker(config=cfg)


class TestCircuitBreaker(unittest.TestCase):
    def test_initial_state_is_closed(self):
        cb = _make()
        self.assertEqual(cb.state, CircuitState.CLOSED)
        self.assertFalse(cb.is_open())

    def test_opens_after_threshold_failures(self):
        cb = _make(failure_threshold=3)
        for _ in range(3):
            cb.record_failure()
        self.assertEqual(cb.state, CircuitState.OPEN)
        self.assertTrue(cb.is_open())

    def test_does_not_open_before_threshold(self):
        cb = _make(failure_threshold=3)
        cb.record_failure()
        cb.record_failure()
        self.assertFalse(cb.is_open())

    def test_transitions_to_half_open_after_timeout(self):
        cb = _make(failure_threshold=1, recovery_timeout=1.0)
        cb.record_failure()
        self.assertTrue(cb.is_open())
        with patch("retryctl.circuit_breaker.time.monotonic", return_value=cb._opened_at + 2.0):
            self.assertEqual(cb.state, CircuitState.HALF_OPEN)

    def test_closes_after_success_in_half_open(self):
        cb = _make(failure_threshold=1, recovery_timeout=1.0, success_threshold=1)
        cb.record_failure()
        with patch("retryctl.circuit_breaker.time.monotonic", return_value=cb._opened_at + 2.0):
            cb.record_success()
            self.assertEqual(cb.state, CircuitState.CLOSED)

    def test_reopens_on_failure_in_half_open(self):
        cb = _make(failure_threshold=1, recovery_timeout=1.0)
        cb.record_failure()
        opened_at = cb._opened_at
        with patch("retryctl.circuit_breaker.time.monotonic", return_value=opened_at + 2.0):
            self.assertEqual(cb.state, CircuitState.HALF_OPEN)
            cb.record_failure()
        self.assertEqual(cb._state, CircuitState.OPEN)

    def test_disabled_never_opens(self):
        cb = _make(enabled=False, failure_threshold=1)
        cb.record_failure()
        self.assertFalse(cb.is_open())

    def test_reset_restores_closed_state(self):
        cb = _make(failure_threshold=1)
        cb.record_failure()
        self.assertTrue(cb.is_open())
        cb.reset()
        self.assertEqual(cb.state, CircuitState.CLOSED)
        self.assertFalse(cb.is_open())

    def test_success_resets_failure_count_when_closed(self):
        cb = _make(failure_threshold=3)
        cb.record_failure()
        cb.record_failure()
        cb.record_success()
        self.assertEqual(cb._failure_count, 0)


if __name__ == "__main__":
    unittest.main()
