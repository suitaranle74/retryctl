"""Unit tests for the exponential backoff module."""

import time
from unittest.mock import patch

import pytest

from retryctl.backoff import BackoffConfig, ExponentialBackoff


class TestBackoffConfig:
    def test_defaults(self):
        cfg = BackoffConfig()
        assert cfg.initial_delay == 1.0
        assert cfg.multiplier == 2.0
        assert cfg.max_delay == 60.0
        assert cfg.jitter is True
        assert cfg.max_attempts == 5

    def test_custom_values(self):
        cfg = BackoffConfig(initial_delay=0.5, max_attempts=3, jitter=False)
        assert cfg.initial_delay == 0.5
        assert cfg.max_attempts == 3
        assert cfg.jitter is False


class TestExponentialBackoff:
    def _make(self, **kwargs) -> ExponentialBackoff:
        return ExponentialBackoff(BackoffConfig(**kwargs))

    def test_initial_attempt_is_zero(self):
        bo = self._make()
        assert bo.attempt == 0

    def test_should_retry_within_limit(self):
        bo = self._make(max_attempts=3)
        assert bo.should_retry() is True

    def test_should_not_retry_when_exhausted(self):
        bo = self._make(max_attempts=2)
        bo._attempt = 2
        assert bo.should_retry() is False

    def test_next_delay_no_jitter_grows_exponentially(self):
        bo = self._make(initial_delay=1.0, multiplier=2.0, max_delay=100.0, jitter=False)
        delays = []
        for _ in range(4):
            delays.append(bo.next_delay())
            bo._attempt += 1
        assert delays == [1.0, 2.0, 4.0, 8.0]

    def test_next_delay_capped_at_max(self):
        bo = self._make(initial_delay=1.0, multiplier=10.0, max_delay=5.0, jitter=False)
        bo._attempt = 3
        assert bo.next_delay() == 5.0

    def test_jitter_stays_non_negative(self):
        bo = self._make(initial_delay=0.001, jitter=True, jitter_range=1.0)
        for _ in range(50):
            assert bo.next_delay() >= 0.0

    def test_wait_increments_attempt_and_returns_delay(self):
        bo = self._make(initial_delay=0.0, multiplier=1.0, jitter=False)
        with patch("retryctl.backoff.time.sleep") as mock_sleep:
            delay = bo.wait()
        mock_sleep.assert_called_once_with(delay)
        assert bo.attempt == 1

    def test_reset_clears_attempt_counter(self):
        bo = self._make()
        bo._attempt = 4
        bo.reset()
        assert bo.attempt == 0

    def test_full_retry_cycle(self):
        bo = self._make(max_attempts=3, initial_delay=0.0, jitter=False)
        with patch("retryctl.backoff.time.sleep"):
            count = 0
            while bo.should_retry():
                bo.wait()
                count += 1
        assert count == 3
        assert bo.should_retry() is False
