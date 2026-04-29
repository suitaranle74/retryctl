"""Tests for retryctl.throttle."""
import pytest
from unittest.mock import patch

from retryctl.throttle import ThrottleConfig, ThrottleState, Throttler


class TestThrottleConfig:
    def test_defaults(self):
        cfg = ThrottleConfig()
        assert cfg.enabled is False
        assert cfg.consecutive_failures_threshold == 3
        assert cfg.throttle_delay == 30.0
        assert cfg.max_throttle_delay == 300.0

    def test_custom_values(self):
        cfg = ThrottleConfig(enabled=True, consecutive_failures_threshold=5, throttle_delay=60.0)
        assert cfg.enabled is True
        assert cfg.consecutive_failures_threshold == 5
        assert cfg.throttle_delay == 60.0

    def test_from_dict_partial(self):
        cfg = ThrottleConfig.from_dict({"enabled": True, "throttle_delay": 10.0})
        assert cfg.enabled is True
        assert cfg.throttle_delay == 10.0
        assert cfg.consecutive_failures_threshold == 3  # default

    def test_from_dict_ignores_unknown_keys(self):
        cfg = ThrottleConfig.from_dict({"enabled": True, "unknown_key": "x"})
        assert cfg.enabled is True
        assert not hasattr(cfg, "unknown_key")

    def test_from_dict_full(self):
        cfg = ThrottleConfig.from_dict(
            {
                "enabled": True,
                "consecutive_failures_threshold": 2,
                "throttle_delay": 15.0,
                "max_throttle_delay": 120.0,
            }
        )
        assert cfg.consecutive_failures_threshold == 2
        assert cfg.max_throttle_delay == 120.0


class TestThrottler:
    def _make(self, **kwargs):
        slept = []
        cfg = ThrottleConfig(**kwargs)
        t = Throttler(cfg, _sleep=slept.append)
        return t, slept

    def test_no_throttle_when_disabled(self):
        t, slept = self._make(enabled=False, consecutive_failures_threshold=1)
        t.record_failure()
        result = t.maybe_throttle()
        assert result is False
        assert slept == []

    def test_no_throttle_below_threshold(self):
        t, slept = self._make(enabled=True, consecutive_failures_threshold=3)
        t.record_failure()
        t.record_failure()
        result = t.maybe_throttle()
        assert result is False
        assert slept == []

    def test_throttle_at_threshold(self):
        t, slept = self._make(enabled=True, consecutive_failures_threshold=3, throttle_delay=5.0)
        for _ in range(3):
            t.record_failure()
        result = t.maybe_throttle()
        assert result is True
        assert slept == [5.0]
        assert t.state.total_throttle_events == 1

    def test_throttle_respects_max_delay(self):
        t, slept = self._make(
            enabled=True,
            consecutive_failures_threshold=1,
            throttle_delay=500.0,
            max_throttle_delay=60.0,
        )
        t.record_failure()
        t.maybe_throttle()
        assert slept == [60.0]

    def test_record_success_resets_failures(self):
        t, slept = self._make(enabled=True, consecutive_failures_threshold=2, throttle_delay=5.0)
        t.record_failure()
        t.record_failure()
        t.record_success()
        result = t.maybe_throttle()
        assert result is False
        assert slept == []

    def test_reset_clears_state(self):
        t, slept = self._make(enabled=True, consecutive_failures_threshold=1, throttle_delay=1.0)
        t.record_failure()
        t.maybe_throttle()
        t.reset()
        assert t.state.consecutive_failures == 0
        assert t.state.total_throttle_events == 0
