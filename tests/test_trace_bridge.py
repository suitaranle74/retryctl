"""Tests for retryctl.trace_bridge."""
import pytest
from retryctl.config import FileConfig
from retryctl.trace import TraceConfig
from retryctl.trace_bridge import trace_config_from_file


class TestTraceConfigFromFile:
    def _make(self, **kwargs) -> FileConfig:
        fc = FileConfig()
        for k, v in kwargs.items():
            setattr(fc, k, v)
        return fc

    def test_defaults_produce_disabled_trace(self):
        cfg = trace_config_from_file(self._make())
        assert isinstance(cfg, TraceConfig)
        assert cfg.enabled is False

    def test_enabled_forwarded(self):
        cfg = trace_config_from_file(self._make(trace_enabled=True))
        assert cfg.enabled is True

    def test_header_name_forwarded(self):
        cfg = trace_config_from_file(self._make(trace_header_name="X-My-Header"))
        assert cfg.header_name == "X-My-Header"

    def test_propagate_env_forwarded(self):
        cfg = trace_config_from_file(self._make(trace_propagate_env=False))
        assert cfg.propagate_env is False

    def test_env_var_forwarded(self):
        cfg = trace_config_from_file(self._make(trace_env_var="CUSTOM_TRACE"))
        assert cfg.env_var == "CUSTOM_TRACE"

    def test_unset_fields_use_defaults(self):
        cfg = trace_config_from_file(self._make(trace_enabled=True))
        assert cfg.header_name == "X-Retry-Trace-Id"
        assert cfg.propagate_env is True
        assert cfg.env_var == "RETRYCTL_TRACE_ID"
