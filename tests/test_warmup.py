"""Tests for retryctl.warmup and retryctl.warmup_bridge."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from retryctl.warmup import WarmupConfig, WarmupManager
from retryctl.warmup_bridge import warmup_config_from_file


class TestWarmupConfig:
    def test_defaults(self):
        cfg = WarmupConfig()
        assert cfg.enabled is False
        assert cfg.delay_seconds == 0.0
        assert cfg.message is None

    def test_custom_values(self):
        cfg = WarmupConfig(enabled=True, delay_seconds=2.5, message="warming up")
        assert cfg.enabled is True
        assert cfg.delay_seconds == 2.5
        assert cfg.message == "warming up"

    def test_from_dict_full(self):
        cfg = WarmupConfig.from_dict(
            {"enabled": True, "delay_seconds": 1.5, "message": "please wait"}
        )
        assert cfg.enabled is True
        assert cfg.delay_seconds == 1.5
        assert cfg.message == "please wait"

    def test_from_dict_partial(self):
        cfg = WarmupConfig.from_dict({"enabled": True})
        assert cfg.enabled is True
        assert cfg.delay_seconds == 0.0
        assert cfg.message is None

    def test_from_dict_ignores_unknown_keys(self):
        cfg = WarmupConfig.from_dict({"enabled": False, "unknown_key": "ignored"})
        assert cfg.enabled is False


class TestWarmupManager:
    def _make(self, enabled=True, delay=0.0, message=None):
        cfg = WarmupConfig(enabled=enabled, delay_seconds=delay, message=message)
        return WarmupManager(cfg)

    def test_warmup_disabled_returns_false(self):
        mgr = self._make(enabled=False)
        assert mgr.maybe_warmup() is False
        assert mgr.applied is False

    def test_warmup_enabled_returns_true_first_call(self):
        mgr = self._make(enabled=True, delay=0.0)
        assert mgr.maybe_warmup() is True
        assert mgr.applied is True

    def test_warmup_only_applied_once(self):
        mgr = self._make(enabled=True, delay=0.0)
        assert mgr.maybe_warmup() is True
        assert mgr.maybe_warmup() is False

    def test_warmup_calls_sleep(self):
        mgr = self._make(enabled=True, delay=1.5)
        with patch("retryctl.warmup.time.sleep") as mock_sleep:
            mgr.maybe_warmup()
            mock_sleep.assert_called_once_with(1.5)

    def test_warmup_zero_delay_no_sleep(self):
        mgr = self._make(enabled=True, delay=0.0)
        with patch("retryctl.warmup.time.sleep") as mock_sleep:
            mgr.maybe_warmup()
            mock_sleep.assert_not_called()

    def test_message_property(self):
        mgr = self._make(enabled=True, message="hold on")
        assert mgr.message == "hold on"


class TestWarmupConfigFromFile:
    def _make(
        self,
        warmup_enabled=False,
        warmup_delay_seconds=0.0,
        warmup_message=None,
    ):
        class _FC:
            pass

        fc = _FC()
        fc.warmup_enabled = warmup_enabled
        fc.warmup_delay_seconds = warmup_delay_seconds
        fc.warmup_message = warmup_message
        return fc

    def test_defaults_produce_disabled_warmup(self):
        cfg = warmup_config_from_file(self._make())
        assert cfg.enabled is False
        assert cfg.delay_seconds == 0.0
        assert cfg.message is None

    def test_enabled_forwarded(self):
        cfg = warmup_config_from_file(self._make(warmup_enabled=True))
        assert cfg.enabled is True

    def test_delay_forwarded(self):
        cfg = warmup_config_from_file(self._make(warmup_delay_seconds=3.0))
        assert cfg.delay_seconds == 3.0

    def test_message_forwarded(self):
        cfg = warmup_config_from_file(self._make(warmup_message="starting"))
        assert cfg.message == "starting"
