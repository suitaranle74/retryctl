"""Tests for retryctl.suppress and retryctl.suppress_bridge."""
from __future__ import annotations

import pytest

from retryctl.suppress import SuppressConfig, SuppressEvaluator
from retryctl.suppress_bridge import suppress_config_from_file


# ---------------------------------------------------------------------------
# SuppressConfig
# ---------------------------------------------------------------------------

class TestSuppressConfig:
    def test_defaults(self):
        cfg = SuppressConfig()
        assert cfg.enabled is False
        assert cfg.exit_codes == []
        assert cfg.output_patterns == []
        assert cfg.max_suppressed is None

    def test_custom_values(self):
        cfg = SuppressConfig(enabled=True, exit_codes=[1, 2], output_patterns=["warn"], max_suppressed=3)
        assert cfg.enabled is True
        assert cfg.exit_codes == [1, 2]
        assert cfg.output_patterns == ["warn"]
        assert cfg.max_suppressed == 3

    def test_from_dict_full(self):
        cfg = SuppressConfig.from_dict(
            {"enabled": True, "exit_codes": [42], "output_patterns": ["SKIP"], "max_suppressed": 5}
        )
        assert cfg.enabled is True
        assert cfg.exit_codes == [42]
        assert cfg.output_patterns == ["SKIP"]
        assert cfg.max_suppressed == 5

    def test_from_dict_ignores_unknown_keys(self):
        cfg = SuppressConfig.from_dict({"enabled": True, "unknown_key": "value"})
        assert cfg.enabled is True
        assert not hasattr(cfg, "unknown_key")


# ---------------------------------------------------------------------------
# SuppressEvaluator
# ---------------------------------------------------------------------------

class TestSuppressEvaluator:
    def _make(self, **kwargs) -> SuppressEvaluator:
        return SuppressEvaluator(SuppressConfig(**kwargs))

    def test_disabled_never_suppresses(self):
        ev = self._make(enabled=False, exit_codes=[1])
        assert ev.should_suppress(1) is False

    def test_suppresses_matching_exit_code(self):
        ev = self._make(enabled=True, exit_codes=[1, 2])
        assert ev.should_suppress(1) is True
        assert ev.should_suppress(2) is True

    def test_does_not_suppress_non_matching_exit_code(self):
        ev = self._make(enabled=True, exit_codes=[1])
        assert ev.should_suppress(99) is False

    def test_suppresses_matching_output_pattern(self):
        ev = self._make(enabled=True, output_patterns=["WARN"])
        assert ev.should_suppress(1, output="some WARN message") is True

    def test_does_not_suppress_non_matching_output(self):
        ev = self._make(enabled=True, output_patterns=["WARN"])
        assert ev.should_suppress(1, output="all good") is False

    def test_max_suppressed_cap(self):
        ev = self._make(enabled=True, exit_codes=[1], max_suppressed=2)
        assert ev.should_suppress(1) is True   # count=1
        assert ev.should_suppress(1) is True   # count=2
        assert ev.should_suppress(1) is False  # cap reached

    def test_suppressed_count_increments(self):
        ev = self._make(enabled=True, exit_codes=[1])
        ev.should_suppress(1)
        ev.should_suppress(1)
        assert ev.suppressed_count == 2

    def test_reset_clears_count(self):
        ev = self._make(enabled=True, exit_codes=[1])
        ev.should_suppress(1)
        ev.reset()
        assert ev.suppressed_count == 0


# ---------------------------------------------------------------------------
# suppress_bridge
# ---------------------------------------------------------------------------

class TestSuppressConfigFromFile:
    class _FakeFileConfig:
        def __init__(self, suppress=None):
            self.suppress = suppress

    def test_defaults_produce_disabled_suppress(self):
        cfg = suppress_config_from_file(self._FakeFileConfig())
        assert cfg.enabled is False
        assert cfg.exit_codes == []

    def test_enabled_forwarded(self):
        cfg = suppress_config_from_file(self._FakeFileConfig(suppress={"enabled": True}))
        assert cfg.enabled is True

    def test_exit_codes_forwarded(self):
        cfg = suppress_config_from_file(self._FakeFileConfig(suppress={"enabled": True, "exit_codes": [3, 4]}))
        assert cfg.exit_codes == [3, 4]

    def test_max_suppressed_forwarded(self):
        cfg = suppress_config_from_file(self._FakeFileConfig(suppress={"max_suppressed": 10}))
        assert cfg.max_suppressed == 10
