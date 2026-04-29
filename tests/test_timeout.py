"""Tests for retryctl.timeout."""
from __future__ import annotations

import pytest

from retryctl.timeout import TimeoutConfig, TimeoutTracker


class TestTimeoutConfig:
    def test_defaults(self):
        cfg = TimeoutConfig()
        assert cfg.attempt_timeout is None
        assert cfg.total_timeout is None

    def test_custom_values(self):
        cfg = TimeoutConfig(attempt_timeout=5.0, total_timeout=30.0)
        assert cfg.attempt_timeout == 5.0
        assert cfg.total_timeout == 30.0

    def test_from_dict_full(self):
        cfg = TimeoutConfig.from_dict({"attempt_timeout": 2.5, "total_timeout": 10.0})
        assert cfg.attempt_timeout == 2.5
        assert cfg.total_timeout == 10.0

    def test_from_dict_ignores_unknown_keys(self):
        cfg = TimeoutConfig.from_dict({"attempt_timeout": 1.0, "unknown": "x"})
        assert cfg.attempt_timeout == 1.0

    def test_validate_ok(self):
        TimeoutConfig(attempt_timeout=1.0, total_timeout=10.0).validate()

    def test_validate_zero_attempt(self):
        with pytest.raises(ValueError, match="attempt_timeout"):
            TimeoutConfig(attempt_timeout=0).validate()

    def test_validate_negative_total(self):
        with pytest.raises(ValueError, match="total_timeout"):
            TimeoutConfig(total_timeout=-5.0).validate()


class TestTimeoutTracker:
    def _make(self, attempt=None, total=None, start=0.0):
        cfg = TimeoutConfig(attempt_timeout=attempt, total_timeout=total)
        tick = [start]

        def clock():
            return tick[0]

        tracker = TimeoutTracker(cfg, clock=clock)
        return tracker, tick

    def test_elapsed(self):
        tracker, tick = self._make()
        tick[0] = 3.0
        assert tracker.elapsed() == pytest.approx(3.0)

    def test_total_not_exceeded(self):
        tracker, tick = self._make(total=10.0)
        tick[0] = 5.0
        assert not tracker.total_exceeded()

    def test_total_exceeded(self):
        tracker, tick = self._make(total=10.0)
        tick[0] = 11.0
        assert tracker.total_exceeded()

    def test_remaining_total_none_when_unlimited(self):
        tracker, _ = self._make()
        assert tracker.remaining_total() is None

    def test_remaining_total_decreases(self):
        tracker, tick = self._make(total=10.0)
        tick[0] = 4.0
        assert tracker.remaining_total() == pytest.approx(6.0)

    def test_remaining_total_floors_at_zero(self):
        tracker, tick = self._make(total=5.0)
        tick[0] = 99.0
        assert tracker.remaining_total() == pytest.approx(0.0)

    def test_effective_attempt_timeout_no_limits(self):
        tracker, _ = self._make()
        assert tracker.effective_attempt_timeout() is None

    def test_effective_attempt_timeout_only_attempt(self):
        tracker, _ = self._make(attempt=5.0)
        assert tracker.effective_attempt_timeout() == pytest.approx(5.0)

    def test_effective_attempt_timeout_tightest_wins(self):
        tracker, tick = self._make(attempt=5.0, total=10.0)
        tick[0] = 7.0  # remaining total = 3.0 < attempt 5.0
        assert tracker.effective_attempt_timeout() == pytest.approx(3.0)
