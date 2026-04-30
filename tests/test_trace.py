"""Tests for retryctl.trace."""
import pytest
from retryctl.trace import TraceConfig, TraceContext, Tracer


class TestTraceConfig:
    def test_defaults(self):
        cfg = TraceConfig()
        assert cfg.enabled is False
        assert cfg.header_name == "X-Retry-Trace-Id"
        assert cfg.propagate_env is True
        assert cfg.env_var == "RETRYCTL_TRACE_ID"

    def test_from_dict_full(self):
        cfg = TraceConfig.from_dict({
            "enabled": True,
            "header_name": "X-Custom",
            "propagate_env": False,
            "env_var": "MY_TRACE",
        })
        assert cfg.enabled is True
        assert cfg.header_name == "X-Custom"
        assert cfg.propagate_env is False
        assert cfg.env_var == "MY_TRACE"

    def test_from_dict_ignores_unknown_keys(self):
        cfg = TraceConfig.from_dict({"enabled": True, "unknown": "ignored"})
        assert cfg.enabled is True


class TestTraceContext:
    def test_to_env_contains_required_keys(self):
        ctx = TraceContext(trace_id="tid", span_id="sid", attempt=2)
        env = ctx.to_env()
        assert env["RETRYCTL_TRACE_ID"] == "tid"
        assert env["RETRYCTL_SPAN_ID"] == "sid"
        assert env["RETRYCTL_ATTEMPT"] == "2"
        assert "RETRYCTL_PARENT_SPAN_ID" not in env

    def test_to_env_includes_parent_when_set(self):
        ctx = TraceContext(trace_id="tid", span_id="sid", parent_span_id="psid")
        env = ctx.to_env()
        assert env["RETRYCTL_PARENT_SPAN_ID"] == "psid"

    def test_child_inherits_trace_id(self):
        ctx = TraceContext(trace_id="root-trace")
        child = ctx.child(attempt=1)
        assert child.trace_id == "root-trace"
        assert child.parent_span_id == ctx.span_id
        assert child.attempt == 1
        assert child.span_id != ctx.span_id


class TestTracer:
    def _make(self, enabled=True):
        return Tracer(TraceConfig(enabled=enabled))

    def test_start_returns_context(self):
        tracer = self._make()
        ctx = tracer.start()
        assert isinstance(ctx, TraceContext)

    def test_span_for_attempt_returns_child(self):
        tracer = self._make()
        tracer.start()
        span = tracer.span_for_attempt(3)
        assert span is not None
        assert span.attempt == 3

    def test_span_for_attempt_disabled_returns_none(self):
        tracer = self._make(enabled=False)
        tracer.start()
        assert tracer.span_for_attempt(1) is None

    def test_env_for_attempt_disabled_returns_empty(self):
        tracer = self._make(enabled=False)
        tracer.start()
        assert tracer.env_for_attempt(1) == {}

    def test_env_for_attempt_enabled_returns_env(self):
        tracer = self._make()
        tracer.start()
        env = tracer.env_for_attempt(2)
        assert "RETRYCTL_TRACE_ID" in env
        assert env["RETRYCTL_ATTEMPT"] == "2"
