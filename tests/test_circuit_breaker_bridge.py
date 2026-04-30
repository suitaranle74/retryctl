"""Tests for circuit_breaker_config_from_file bridge."""
import unittest
from retryctl.circuit_breaker import CircuitBreakerConfig
from retryctl.circuit_breaker_bridge import circuit_breaker_config_from_file
from retryctl.config import FileConfig


class TestCircuitBreakerConfigFromFile(unittest.TestCase):
    @staticmethod
    def _make(**kwargs) -> FileConfig:
        defaults = dict(
            circuit_breaker_enabled=None,
            circuit_breaker_failure_threshold=None,
            circuit_breaker_recovery_timeout=None,
            circuit_breaker_success_threshold=None,
        )
        defaults.update(kwargs)
        return FileConfig(**defaults)

    def test_defaults_produce_disabled_circuit_breaker(self):
        fc = self._make()
        cfg = circuit_breaker_config_from_file(fc)
        self.assertIsInstance(cfg, CircuitBreakerConfig)
        self.assertFalse(cfg.enabled)

    def test_enabled_forwarded(self):
        fc = self._make(circuit_breaker_enabled=True)
        cfg = circuit_breaker_config_from_file(fc)
        self.assertTrue(cfg.enabled)

    def test_failure_threshold_forwarded(self):
        fc = self._make(circuit_breaker_failure_threshold=4)
        cfg = circuit_breaker_config_from_file(fc)
        self.assertEqual(cfg.failure_threshold, 4)

    def test_recovery_timeout_forwarded(self):
        fc = self._make(circuit_breaker_recovery_timeout=45.0)
        cfg = circuit_breaker_config_from_file(fc)
        self.assertEqual(cfg.recovery_timeout, 45.0)

    def test_success_threshold_forwarded(self):
        fc = self._make(circuit_breaker_success_threshold=2)
        cfg = circuit_breaker_config_from_file(fc)
        self.assertEqual(cfg.success_threshold, 2)


if __name__ == "__main__":
    unittest.main()
