"""Tests for retryctl.timeout_bridge."""
from __future__ import annotations

from retryctl.config import FileConfig
from retryctl.timeout import TimeoutConfig
from retryctl.timeout_bridge import timeout_config_from_file


class TestTimeoutConfigFromFile:
    def _make(self, **kwargs) -> FileConfig:
        return FileConfig(**kwargs)

    def test_defaults_produce_none_timeouts(self):
        cfg = timeout_config_from_file(self._make())
        assert isinstance(cfg, TimeoutConfig)
        assert cfg.attempt_timeout is None
        assert cfg.total_timeout is None

    def test_attempt_timeout_forwarded(self):
        cfg = timeout_config_from_file(self._make(attempt_timeout=7.5))
        assert cfg.attempt_timeout == 7.5

    def test_total_timeout_forwarded(self):
        cfg = timeout_config_from_file(self._make(total_timeout=60.0))
        assert cfg.total_timeout == 60.0

    def test_both_forwarded(self):
        cfg = timeout_config_from_file(
            self._make(attempt_timeout=3.0, total_timeout=20.0)
        )
        assert cfg.attempt_timeout == 3.0
        assert cfg.total_timeout == 20.0
