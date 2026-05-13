"""Tests for retryctl.debounce and retryctl.debounce_bridge."""
from __future__ import annotations

import time
from unittest.mock import patch

import pytest

from retryctl.debounce import DebounceConfig, DebounceState
from retryctl.debounce_bridge import debounce_config_from_file
from retryctl.config import FileConfig


# ---------------------------------------------------------------------------
# DebounceConfig
# ---------------------------------------------------------------------------

class TestDebounceConfig:
    def test_defaults(self):
        cfg = DebounceConfig()
        assert cfg.enabled is False
        assert cfg.window_seconds == 1.0

    def test_custom_values(self):
        cfg = DebounceConfig(enabled=True, window_seconds=2.5)
        assert cfg.enabled is True
        assert cfg.window_seconds == 2.5

    def test_from_dict_full(self):
        cfg = DebounceConfig.from_dict({"enabled": True, "window_seconds": 0.5})
        assert cfg.enabled is True
        assert cfg.window_seconds == 0.5

    def test_from_dict_partial(self):
        cfg = DebounceConfig.from_dict({"enabled": True})
        assert cfg.enabled is True
        assert cfg.window_seconds == 1.0

    def test_from_dict_ignores_unknown_keys(self):
        cfg = DebounceConfig.from_dict({"enabled": True, "unknown_key": 99})
        assert cfg.enabled is True


# ---------------------------------------------------------------------------
# DebounceState
# ---------------------------------------------------------------------------

class TestDebounceState:
    def _make(self, enabled=True, window=1.0) -> DebounceState:
        return DebounceState(config=DebounceConfig(enabled=enabled, window_seconds=window))

    def test_no_debounce_when_disabled(self):
        state = self._make(enabled=False)
        state.record_attempt()
        assert state.should_debounce() is False

    def test_no_debounce_before_first_attempt(self):
        state = self._make()
        assert state.should_debounce() is False

    def test_debounces_immediately_after_attempt(self):
        state = self._make(window=10.0)
        state.record_attempt()
        assert state.should_debounce() is True

    def test_no_debounce_after_window_expires(self):
        state = self._make(window=0.05)
        state.record_attempt()
        time.sleep(0.1)
        assert state.should_debounce() is False

    def test_remaining_wait_positive_when_inside_window(self):
        state = self._make(window=10.0)
        state.record_attempt()
        remaining = state.remaining_wait()
        assert 0.0 < remaining <= 10.0

    def test_remaining_wait_zero_when_disabled(self):
        state = self._make(enabled=False)
        state.record_attempt()
        assert state.remaining_wait() == 0.0

    def test_reset_clears_state(self):
        state = self._make(window=10.0)
        state.record_attempt()
        state.reset()
        assert state.should_debounce() is False
        assert state.remaining_wait() == 0.0


# ---------------------------------------------------------------------------
# debounce_config_from_file
# ---------------------------------------------------------------------------

class TestDebounceConfigFromFile:
    def _make(self, debounce=None) -> FileConfig:
        fc = FileConfig()
        fc.debounce = debounce
        return fc

    def test_defaults_produce_disabled_debounce(self):
        cfg = debounce_config_from_file(self._make())
        assert cfg.enabled is False

    def test_enabled_forwarded(self):
        cfg = debounce_config_from_file(self._make(debounce={"enabled": True}))
        assert cfg.enabled is True

    def test_window_seconds_forwarded(self):
        cfg = debounce_config_from_file(self._make(debounce={"enabled": True, "window_seconds": 3.0}))
        assert cfg.window_seconds == 3.0
