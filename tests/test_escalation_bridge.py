"""Tests for retryctl.escalation_bridge."""
import pytest
from retryctl.config import FileConfig
from retryctl.escalation import EscalationConfig
from retryctl.escalation_bridge import escalation_config_from_file


class TestEscalationConfigFromFile:
    def _make(self, **kwargs) -> FileConfig:
        defaults = dict(
            escalation_enabled=None,
            escalation_threshold=None,
            escalation_cooldown=None,
            escalation_hooks=None,
        )
        defaults.update(kwargs)
        return FileConfig(**defaults)

    def test_defaults_produce_disabled_escalation(self):
        cfg = escalation_config_from_file(self._make())
        assert isinstance(cfg, EscalationConfig)
        assert cfg.enabled is False

    def test_enabled_forwarded(self):
        cfg = escalation_config_from_file(self._make(escalation_enabled=True))
        assert cfg.enabled is True

    def test_threshold_forwarded(self):
        cfg = escalation_config_from_file(self._make(escalation_threshold=5))
        assert cfg.threshold == 5

    def test_cooldown_forwarded(self):
        cfg = escalation_config_from_file(self._make(escalation_cooldown=120.0))
        assert cfg.cooldown == 120.0

    def test_hooks_forwarded(self):
        cfg = escalation_config_from_file(self._make(escalation_hooks=["alert.sh"]))
        assert cfg.hooks == ["alert.sh"]
