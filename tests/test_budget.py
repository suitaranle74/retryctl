"""Tests for retryctl/budget.py"""

import pytest
from retryctl.budget import BudgetConfig, BudgetState, RetryBudget


class TestBudgetConfig:
    def test_defaults(self):
        cfg = BudgetConfig()
        assert cfg.enabled is False
        assert cfg.max_retries_per_window == 10
        assert cfg.window_seconds == 60.0

    def test_custom_values(self):
        cfg = BudgetConfig(enabled=True, max_retries_per_window=5, window_seconds=30.0)
        assert cfg.enabled is True
        assert cfg.max_retries_per_window == 5
        assert cfg.window_seconds == 30.0

    def test_from_dict_full(self):
        cfg = BudgetConfig.from_dict(
            {"enabled": True, "max_retries_per_window": 3, "window_seconds": 10.0}
        )
        assert cfg.enabled is True
        assert cfg.max_retries_per_window == 3
        assert cfg.window_seconds == 10.0

    def test_from_dict_ignores_unknown_keys(self):
        cfg = BudgetConfig.from_dict({"enabled": True, "unknown_key": "ignored"})
        assert cfg.enabled is True


class TestBudgetState:
    def test_empty_window_count_is_zero(self):
        state = BudgetState()
        assert state.retry_count_in_window(60.0, now=100.0) == 0

    def test_counts_retries_within_window(self):
        state = BudgetState()
        state.record_retry(now=50.0)
        state.record_retry(now=80.0)
        assert state.retry_count_in_window(60.0, now=100.0) == 2

    def test_excludes_retries_outside_window(self):
        state = BudgetState()
        state.record_retry(now=10.0)  # outside window
        state.record_retry(now=80.0)  # inside window
        assert state.retry_count_in_window(60.0, now=100.0) == 1

    def test_reset_clears_timestamps(self):
        state = BudgetState()
        state.record_retry(now=90.0)
        state.reset()
        assert state.retry_count_in_window(60.0, now=100.0) == 0


class TestRetryBudget:
    def _make(self, enabled=True, max_retries=3, window=60.0):
        cfg = BudgetConfig(enabled=enabled, max_retries_per_window=max_retries, window_seconds=window)
        return RetryBudget(cfg)

    def test_not_exhausted_when_disabled(self):
        budget = self._make(enabled=False)
        for _ in range(100):
            budget.consume(now=1.0)
        assert budget.is_exhausted(now=1.0) is False

    def test_not_exhausted_below_limit(self):
        budget = self._make(max_retries=3)
        budget.consume(now=10.0)
        budget.consume(now=20.0)
        assert budget.is_exhausted(now=30.0) is False

    def test_exhausted_at_limit(self):
        budget = self._make(max_retries=3)
        budget.consume(now=10.0)
        budget.consume(now=20.0)
        budget.consume(now=30.0)
        assert budget.is_exhausted(now=40.0) is True

    def test_not_exhausted_after_window_slides(self):
        budget = self._make(max_retries=2, window=30.0)
        budget.consume(now=10.0)
        budget.consume(now=20.0)
        # At now=50, both are outside window [20, 50]
        assert budget.is_exhausted(now=50.0) is False

    def test_reset_allows_retries_again(self):
        budget = self._make(max_retries=2)
        budget.consume(now=10.0)
        budget.consume(now=20.0)
        assert budget.is_exhausted(now=30.0) is True
        budget.reset()
        assert budget.is_exhausted(now=30.0) is False
