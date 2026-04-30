"""Tests for retryctl.correlation."""
import pytest
from retryctl.correlation import (
    CorrelationConfig,
    CorrelationContext,
    CorrelationManager,
)


class TestCorrelationConfig:
    def test_defaults(self):
        cfg = CorrelationConfig()
        assert cfg.enabled is True
        assert cfg.header_name == "X-Retry-Correlation-Id"
        assert cfg.env_var == "RETRYCTL_CORRELATION_ID"
        assert cfg.fixed_id is None

    def test_from_dict_partial(self):
        cfg = CorrelationConfig.from_dict({"enabled": False, "fixed_id": "abc-123"})
        assert cfg.enabled is False
        assert cfg.fixed_id == "abc-123"
        assert cfg.header_name == "X-Retry-Correlation-Id"

    def test_from_dict_ignores_unknown_keys(self):
        cfg = CorrelationConfig.from_dict({"unknown_key": "value", "enabled": True})
        assert cfg.enabled is True


class TestCorrelationContext:
    def test_auto_generated_id(self):
        ctx = CorrelationContext()
        assert ctx.correlation_id != ""
        assert ctx.parent_id is None

    def test_to_env_enabled(self):
        cfg = CorrelationConfig()
        ctx = CorrelationContext(correlation_id="test-id-42")
        env = ctx.to_env(cfg)
        assert env["RETRYCTL_CORRELATION_ID"] == "test-id-42"
        assert "RETRYCTL_CORRELATION_ID_PARENT" not in env

    def test_to_env_with_parent(self):
        cfg = CorrelationConfig()
        ctx = CorrelationContext(correlation_id="child-id", parent_id="parent-id")
        env = ctx.to_env(cfg)
        assert env["RETRYCTL_CORRELATION_ID"] == "child-id"
        assert env["RETRYCTL_CORRELATION_ID_PARENT"] == "parent-id"

    def test_to_env_disabled(self):
        cfg = CorrelationConfig(enabled=False)
        ctx = CorrelationContext(correlation_id="ignored")
        assert ctx.to_env(cfg) == {}

    def test_child_sets_parent_id(self):
        ctx = CorrelationContext(correlation_id="parent-42")
        child = ctx.child()
        assert child.parent_id == "parent-42"
        assert child.correlation_id != "parent-42"


class TestCorrelationManager:
    def _make(self, **kwargs) -> CorrelationManager:
        return CorrelationManager(CorrelationConfig(**kwargs))

    def test_start_returns_context(self):
        mgr = self._make()
        ctx = mgr.start()
        assert ctx.correlation_id != ""
        assert mgr.current is ctx

    def test_start_uses_fixed_id(self):
        mgr = self._make(fixed_id="fixed-999")
        ctx = mgr.start()
        assert ctx.correlation_id == "fixed-999"

    def test_start_disabled_returns_empty_id(self):
        mgr = self._make(enabled=False)
        ctx = mgr.start()
        assert ctx.correlation_id == ""

    def test_current_none_before_start(self):
        mgr = self._make()
        assert mgr.current is None

    def test_env_for_attempt_before_start(self):
        mgr = self._make()
        assert mgr.env_for_attempt() == {}

    def test_env_for_attempt_after_start(self):
        mgr = self._make()
        mgr.start()
        env = mgr.env_for_attempt()
        assert "RETRYCTL_CORRELATION_ID" in env
        assert env["RETRYCTL_CORRELATION_ID"] != ""
