"""Tests for config_bridge module — verifies that FileConfig values are
correctly translated into domain-specific config objects."""

import pytest
from retryctl.config import FileConfig
from retryctl.config_bridge import (
    backoff_config_from_file,
    alert_config_from_file,
    runner_config_from_file,
)


class TestBackoffConfigFromFile:
    """Tests for backoff_config_from_file."""

    def _make(self, **kwargs) -> FileConfig:
        fc = FileConfig()
        for k, v in kwargs.items():
            setattr(fc, k, v)
        return fc

    def test_defaults_produce_valid_backoff_config(self):
        fc = self._make()
        cfg = backoff_config_from_file(fc)
        assert cfg.base_delay == fc.base_delay
        assert cfg.max_delay == fc.max_delay
        assert cfg.multiplier == fc.multiplier
        assert cfg.jitter == fc.jitter

    def test_custom_values_are_forwarded(self):
        fc = self._make(base_delay=2.0, max_delay=60.0, multiplier=3.0, jitter=False)
        cfg = backoff_config_from_file(fc)
        assert cfg.base_delay == 2.0
        assert cfg.max_delay == 60.0
        assert cfg.multiplier == 3.0
        assert cfg.jitter is False


class TestAlertConfigFromFile:
    """Tests for alert_config_from_file."""

    def _make(self, **kwargs) -> FileConfig:
        fc = FileConfig()
        for k, v in kwargs.items():
            setattr(fc, k, v)
        return fc

    def test_defaults_produce_valid_alert_config(self):
        fc = self._make()
        cfg = alert_config_from_file(fc)
        assert cfg.on_failure_hook == fc.on_failure_hook
        assert cfg.on_success_hook == fc.on_success_hook
        assert cfg.on_retry_hook == fc.on_retry_hook

    def test_custom_hooks_are_forwarded(self):
        fc = self._make(
            on_failure_hook="echo fail",
            on_success_hook="echo ok",
            on_retry_hook="echo retry",
        )
        cfg = alert_config_from_file(fc)
        assert cfg.on_failure_hook == "echo fail"
        assert cfg.on_success_hook == "echo ok"
        assert cfg.on_retry_hook == "echo retry"

    def test_none_hooks_remain_none(self):
        fc = self._make(on_failure_hook=None, on_success_hook=None, on_retry_hook=None)
        cfg = alert_config_from_file(fc)
        assert cfg.on_failure_hook is None
        assert cfg.on_success_hook is None
        assert cfg.on_retry_hook is None


class TestRunnerConfigFromFile:
    """Tests for runner_config_from_file."""

    def _make(self, **kwargs) -> FileConfig:
        fc = FileConfig()
        for k, v in kwargs.items():
            setattr(fc, k, v)
        return fc

    def test_defaults_produce_valid_runner_config(self):
        fc = self._make()
        cfg = runner_config_from_file(fc)
        assert cfg.max_attempts == fc.max_attempts
        assert cfg.timeout == fc.timeout
        assert cfg.retryable_exit_codes == fc.retryable_exit_codes

    def test_custom_values_are_forwarded(self):
        fc = self._make(max_attempts=10, timeout=30.0, retryable_exit_codes=[1, 2, 3])
        cfg = runner_config_from_file(fc)
        assert cfg.max_attempts == 10
        assert cfg.timeout == 30.0
        assert cfg.retryable_exit_codes == [1, 2, 3]

    def test_none_timeout_is_preserved(self):
        fc = self._make(timeout=None)
        cfg = runner_config_from_file(fc)
        assert cfg.timeout is None

    def test_empty_retryable_exit_codes(self):
        fc = self._make(retryable_exit_codes=[])
        cfg = runner_config_from_file(fc)
        assert cfg.retryable_exit_codes == []
