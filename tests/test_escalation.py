"""Tests for retryctl.escalation."""
import pytest
from retryctl.escalation import EscalationConfig, EscalationManager


class TestEscalationConfig:
    def test_defaults(self):
        cfg = EscalationConfig()
        assert cfg.enabled is False
        assert cfg.threshold == 3
        assert cfg.cooldown == 60.0
        assert cfg.hooks == []

    def test_custom_values(self):
        cfg = EscalationConfig(enabled=True, threshold=2, cooldown=30.0, hooks=["echo hi"])
        assert cfg.enabled is True
        assert cfg.threshold == 2
        assert cfg.cooldown == 30.0
        assert cfg.hooks == ["echo hi"]

    def test_from_dict_full(self):
        cfg = EscalationConfig.from_dict(
            {"enabled": True, "threshold": 5, "cooldown": 120.0, "hooks": ["notify.sh"]}
        )
        assert cfg.enabled is True
        assert cfg.threshold == 5
        assert cfg.cooldown == 120.0
        assert cfg.hooks == ["notify.sh"]

    def test_from_dict_ignores_unknown_keys(self):
        cfg = EscalationConfig.from_dict({"enabled": True, "unknown_key": "value"})
        assert cfg.enabled is True
        assert not hasattr(cfg, "unknown_key")


class TestEscalationManager:
    def _make(self, **kwargs) -> EscalationManager:
        return EscalationManager(EscalationConfig(enabled=True, **kwargs))

    def test_disabled_never_escalates(self):
        mgr = EscalationManager(EscalationConfig(enabled=False, threshold=1))
        mgr.record_failure()
        assert mgr.should_escalate(now=9999.0) is False

    def test_below_threshold_does_not_escalate(self):
        mgr = self._make(threshold=3)
        mgr.record_failure()
        mgr.record_failure()
        assert mgr.should_escalate(now=0.0) is False

    def test_at_threshold_escalates(self):
        mgr = self._make(threshold=3)
        for _ in range(3):
            mgr.record_failure()
        assert mgr.should_escalate(now=0.0) is True

    def test_cooldown_prevents_re_escalation(self):
        mgr = self._make(threshold=1, cooldown=60.0)
        mgr.record_failure()
        called = []
        mgr.escalate(now=100.0, run_hook=called.append)
        assert mgr.should_escalate(now=130.0) is False

    def test_re_escalates_after_cooldown(self):
        mgr = self._make(threshold=1, cooldown=60.0)
        mgr.record_failure()
        mgr.escalate(now=100.0, run_hook=lambda h: None)
        assert mgr.should_escalate(now=161.0) is True

    def test_escalate_runs_all_hooks(self):
        mgr = self._make(threshold=1, hooks=["hook1", "hook2"])
        mgr.record_failure()
        ran = []
        mgr.escalate(now=0.0, run_hook=ran.append)
        assert ran == ["hook1", "hook2"]

    def test_reset_clears_state(self):
        mgr = self._make(threshold=1)
        mgr.record_failure()
        mgr.escalate(now=0.0, run_hook=lambda h: None)
        mgr.reset()
        assert mgr.should_escalate(now=9999.0) is False
