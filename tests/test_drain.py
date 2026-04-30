"""Tests for retryctl.drain."""
import pytest
from retryctl.drain import DrainConfig, DrainController, DrainState


class TestDrainConfig:
    def test_defaults(self):
        cfg = DrainConfig()
        assert cfg.enabled is False
        assert cfg.grace_period == 5.0
        assert cfg.complete_current is True

    def test_custom_values(self):
        cfg = DrainConfig(enabled=True, grace_period=10.0, complete_current=False)
        assert cfg.enabled is True
        assert cfg.grace_period == 10.0
        assert cfg.complete_current is False

    def test_from_dict_full(self):
        cfg = DrainConfig.from_dict(
            {"enabled": True, "grace_period": 3.5, "complete_current": False}
        )
        assert cfg.enabled is True
        assert cfg.grace_period == 3.5
        assert cfg.complete_current is False

    def test_from_dict_partial(self):
        cfg = DrainConfig.from_dict({"enabled": True})
        assert cfg.enabled is True
        assert cfg.grace_period == 5.0

    def test_from_dict_ignores_unknown_keys(self):
        cfg = DrainConfig.from_dict({"enabled": True, "unknown_key": "ignored"})
        assert cfg.enabled is True


class TestDrainState:
    def test_initial_not_draining(self):
        state = DrainState()
        assert state.draining is False

    def test_signal_sets_draining(self):
        state = DrainState()
        state.signal_drain()
        assert state.draining is True

    def test_reset_clears_draining(self):
        state = DrainState()
        state.signal_drain()
        state.reset()
        assert state.draining is False


class TestDrainController:
    def _make(self, enabled=True, grace_period=5.0, complete_current=True):
        cfg = DrainConfig(enabled=enabled, grace_period=grace_period,
                          complete_current=complete_current)
        return DrainController(cfg)

    def test_not_draining_initially(self):
        ctrl = self._make()
        assert ctrl.is_draining is False

    def test_signal_drain_sets_draining(self):
        ctrl = self._make()
        ctrl.signal_drain()
        assert ctrl.is_draining is True

    def test_should_start_attempt_true_when_not_draining(self):
        ctrl = self._make()
        assert ctrl.should_start_attempt() is True

    def test_should_start_attempt_false_after_drain(self):
        ctrl = self._make()
        ctrl.signal_drain()
        assert ctrl.should_start_attempt() is False

    def test_disabled_drain_ignores_signal(self):
        ctrl = self._make(enabled=False)
        ctrl.signal_drain()
        assert ctrl.is_draining is False
        assert ctrl.should_start_attempt() is True

    def test_grace_period_exposed(self):
        ctrl = self._make(grace_period=12.0)
        assert ctrl.grace_period == 12.0

    def test_reset_clears_drain(self):
        ctrl = self._make()
        ctrl.signal_drain()
        ctrl.reset()
        assert ctrl.is_draining is False
