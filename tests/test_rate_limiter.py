"""Tests for retryctl.rate_limiter."""
import time
from unittest.mock import patch

import pytest

from retryctl.rate_limiter import RateLimiter, RateLimiterConfig


class TestRateLimiterConfig:
    def test_defaults(self):
        cfg = RateLimiterConfig()
        assert cfg.max_attempts_per_minute is None
        assert cfg.min_gap_seconds == 0.0

    def test_custom_values(self):
        cfg = RateLimiterConfig(max_attempts_per_minute=10, min_gap_seconds=1.5)
        assert cfg.max_attempts_per_minute == 10
        assert cfg.min_gap_seconds == 1.5

    def test_from_dict_full(self):
        cfg = RateLimiterConfig.from_dict(
            {"max_attempts_per_minute": 5, "min_gap_seconds": 2.0}
        )
        assert cfg.max_attempts_per_minute == 5
        assert cfg.min_gap_seconds == 2.0

    def test_from_dict_empty(self):
        cfg = RateLimiterConfig.from_dict({})
        assert cfg.max_attempts_per_minute is None
        assert cfg.min_gap_seconds == 0.0

    def test_from_dict_ignores_unknown_keys(self):
        cfg = RateLimiterConfig.from_dict({"unknown_key": 99})
        assert cfg.max_attempts_per_minute is None


class TestRateLimiter:
    def _make(self, **kwargs) -> RateLimiter:
        return RateLimiter(config=RateLimiterConfig(**kwargs))

    def test_acquire_no_limits_returns_zero_wait(self):
        rl = self._make()
        waited = rl.acquire()
        assert waited == 0.0

    def test_acquire_records_attempt_time(self):
        rl = self._make()
        rl.acquire()
        assert len(rl._attempt_times) == 1

    def test_reset_clears_state(self):
        rl = self._make()
        rl.acquire()
        rl.reset()
        assert rl._attempt_times == []
        assert rl._last_attempt_time is None

    def test_min_gap_enforced(self):
        rl = self._make(min_gap_seconds=0.05)
        rl.acquire()
        start = time.monotonic()
        rl.acquire()
        elapsed = time.monotonic() - start
        assert elapsed >= 0.04

    def test_min_gap_not_applied_on_first_call(self):
        rl = self._make(min_gap_seconds=5.0)
        start = time.monotonic()
        rl.acquire()
        elapsed = time.monotonic() - start
        assert elapsed < 0.1

    def test_max_attempts_per_minute_blocks_when_exceeded(self):
        """When the window is saturated, acquire should sleep."""
        rl = self._make(max_attempts_per_minute=2)
        fake_times = [0.0, 1.0, 2.0, 63.0]
        call_iter = iter(fake_times)

        slept = []

        with patch("retryctl.rate_limiter.time.monotonic", side_effect=lambda: next(call_iter)):
            with patch("retryctl.rate_limiter.time.sleep", side_effect=lambda s: slept.append(s)):
                rl._attempt_times = [0.0, 1.0]
                rl.acquire()

        assert len(slept) >= 1

    def test_multiple_acquires_accumulate_times(self):
        rl = self._make()
        for _ in range(5):
            rl.acquire()
        assert len(rl._attempt_times) == 5
