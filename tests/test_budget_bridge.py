"""Tests for retryctl/budget_bridge.py"""

import pytest
from retryctl.budget import BudgetConfig
from retryctl.budget_bridge import budget_config_from_file
from retryctl.config import FileConfig


class TestBudgetConfigFromFile:
    def _make(self, **kwargs) -> FileConfig:
        defaults = dict(
            budget_enabled=False,
            budget_max_retries_per_window=10,
            budget_window_seconds=60.0,
        )
        defaults.update(kwargs)
        return FileConfig(**defaults)

    def test_defaults_produce_disabled_budget(self):
        cfg = budget_config_from_file(self._make())
        assert isinstance(cfg, BudgetConfig)
        assert cfg.enabled is False

    def test_enabled_forwarded(self):
        cfg = budget_config_from_file(self._make(budget_enabled=True))
        assert cfg.enabled is True

    def test_max_retries_forwarded(self):
        cfg = budget_config_from_file(self._make(budget_max_retries_per_window=5))
        assert cfg.max_retries_per_window == 5

    def test_window_seconds_forwarded(self):
        cfg = budget_config_from_file(self._make(budget_window_seconds=120.0))
        assert cfg.window_seconds == 120.0
