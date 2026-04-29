"""Tests for retryctl.throttle_bridge."""
import pytest

from retryctl.config import FileConfig
from retryctl.throttle import ThrottleConfig
from retryctl.throttle_bridge import throttle_config_from_file


class TestThrottleConfigFromFile:
    def _make(self, **kwargs) -> FileConfig:
        """Build a minimal FileConfig, injecting throttle sub-dict if provided."""
        fc = FileConfig()
        if kwargs:
            fc.throttle = kwargs  # type: ignore[attr-defined]
        return fc

    def test_defaults_produce_disabled_throttle(self):
        fc = FileConfig()
        cfg = throttle_config_from_file(fc)
        assert isinstance(cfg, ThrottleConfig)
        assert cfg.enabled is False

    def test_enabled_forwarded(self):
        fc = self._make(enabled=True)
        cfg = throttle_config_from_file(fc)
        assert cfg.enabled is True

    def test_threshold_forwarded(self):
        fc = self._make(enabled=True, consecutive_failures_threshold=5)
        cfg = throttle_config_from_file(fc)
        assert cfg.consecutive_failures_threshold == 5

    def test_delay_forwarded(self):
        fc = self._make(enabled=True, throttle_delay=45.0)
        cfg = throttle_config_from_file(fc)
        assert cfg.throttle_delay == 45.0

    def test_missing_throttle_key_returns_defaults(self):
        """FileConfig with no throttle attribute at all should yield defaults."""
        fc = FileConfig()
        # ensure attribute is absent
        if hasattr(fc, "throttle"):
            del fc.throttle  # type: ignore[attr-defined]
        cfg = throttle_config_from_file(fc)
        assert cfg.enabled is False
        assert cfg.throttle_delay == 30.0
