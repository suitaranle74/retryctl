"""Tests for retryctl.quarantine_bridge."""
import pytest
from retryctl.config import FileConfig
from retryctl.quarantine import QuarantineConfig
from retryctl.quarantine_bridge import quarantine_config_from_file


class TestQuarantineConfigFromFile:
    def _make(self, **kwargs) -> FileConfig:
        fc = FileConfig()
        for k, v in kwargs.items():
            setattr(fc, k, v)
        return fc

    def test_defaults_produce_disabled_quarantine(self):
        fc = self._make()
        cfg = quarantine_config_from_file(fc)
        assert isinstance(cfg, QuarantineConfig)
        assert cfg.enabled is False

    def test_enabled_forwarded(self):
        fc = self._make(quarantine_enabled=True)
        cfg = quarantine_config_from_file(fc)
        assert cfg.enabled is True

    def test_failure_threshold_forwarded(self):
        fc = self._make(quarantine_enabled=True, quarantine_failure_threshold=3)
        cfg = quarantine_config_from_file(fc)
        assert cfg.failure_threshold == 3

    def test_duration_forwarded(self):
        fc = self._make(quarantine_enabled=True, quarantine_duration=120.0)
        cfg = quarantine_config_from_file(fc)
        assert cfg.quarantine_duration == 120.0

    def test_reset_on_success_forwarded(self):
        fc = self._make(quarantine_enabled=True, quarantine_reset_on_success=False)
        cfg = quarantine_config_from_file(fc)
        assert cfg.reset_on_success is False
