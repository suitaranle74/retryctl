"""Tests for retryctl.quarantine."""
import time
import pytest
from retryctl.quarantine import QuarantineConfig, QuarantineState, QuarantineManager


class TestQuarantineConfig:
    def test_defaults(self):
        cfg = QuarantineConfig()
        assert cfg.enabled is False
        assert cfg.failure_threshold == 5
        assert cfg.quarantine_duration == 60.0
        assert cfg.reset_on_success is True

    def test_custom_values(self):
        cfg = QuarantineConfig(enabled=True, failure_threshold=3, quarantine_duration=30.0, reset_on_success=False)
        assert cfg.enabled is True
        assert cfg.failure_threshold == 3
        assert cfg.quarantine_duration == 30.0
        assert cfg.reset_on_success is False

    def test_from_dict_full(self):
        cfg = QuarantineConfig.from_dict({
            "enabled": True, "failure_threshold": 2,
            "quarantine_duration": 10.0, "reset_on_success": False
        })
        assert cfg.enabled is True
        assert cfg.failure_threshold == 2

    def test_from_dict_ignores_unknown_keys(self):
        cfg = QuarantineConfig.from_dict({"enabled": True, "unknown_key": "ignored"})
        assert cfg.enabled is True


class TestQuarantineManager:
    def _make(self, **kwargs) -> QuarantineManager:
        cfg = QuarantineConfig(enabled=True, **kwargs)
        return QuarantineManager(cfg)

    def test_not_quarantined_initially(self):
        mgr = self._make(failure_threshold=3)
        assert mgr.is_quarantined() is False

    def test_quarantined_after_threshold(self):
        mgr = self._make(failure_threshold=3, quarantine_duration=60.0)
        for _ in range(3):
            mgr.record_failure()
        assert mgr.is_quarantined() is True

    def test_not_quarantined_below_threshold(self):
        mgr = self._make(failure_threshold=3)
        mgr.record_failure()
        mgr.record_failure()
        assert mgr.is_quarantined() is False

    def test_success_resets_when_configured(self):
        mgr = self._make(failure_threshold=2, reset_on_success=True)
        mgr.record_failure()
        mgr.record_failure()
        assert mgr.is_quarantined() is True
        mgr.record_success()
        assert mgr.is_quarantined() is False

    def test_success_does_not_reset_when_disabled(self):
        mgr = self._make(failure_threshold=2, reset_on_success=False, quarantine_duration=60.0)
        mgr.record_failure()
        mgr.record_failure()
        assert mgr.is_quarantined() is True
        mgr.record_success()
        assert mgr.is_quarantined() is True

    def test_disabled_never_quarantines(self):
        cfg = QuarantineConfig(enabled=False, failure_threshold=1)
        mgr = QuarantineManager(cfg)
        mgr.record_failure()
        assert mgr.is_quarantined() is False

    def test_remaining_seconds_positive_when_quarantined(self):
        mgr = self._make(failure_threshold=1, quarantine_duration=60.0)
        mgr.record_failure()
        assert mgr.state.remaining_seconds() > 0

    def test_remaining_seconds_zero_when_not_quarantined(self):
        mgr = self._make(failure_threshold=5)
        assert mgr.state.remaining_seconds() == 0.0

    def test_reset_clears_state(self):
        mgr = self._make(failure_threshold=1, quarantine_duration=60.0)
        mgr.record_failure()
        assert mgr.is_quarantined() is True
        mgr.reset()
        assert mgr.is_quarantined() is False
        assert mgr.state.consecutive_failures == 0
