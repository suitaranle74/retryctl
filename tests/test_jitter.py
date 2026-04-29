"""Tests for retryctl.jitter and retryctl.jitter_bridge."""
from __future__ import annotations

import pytest

from retryctl.jitter import JitterConfig, JitterStrategy, JitterApplicator
from retryctl.jitter_bridge import jitter_config_from_file
from retryctl.config import FileConfig


class TestJitterConfig:
    def test_defaults(self):
        cfg = JitterConfig()
        assert cfg.strategy == JitterStrategy.NONE
        assert cfg.min_delay == 0.0
        assert cfg.max_multiplier == 2.0
        assert cfg.seed is None

    def test_from_dict_full(self):
        cfg = JitterConfig.from_dict({
            "strategy": "full",
            "min_delay": 0.1,
            "max_multiplier": 3.0,
            "seed": 42,
        })
        assert cfg.strategy == JitterStrategy.FULL
        assert cfg.min_delay == 0.1
        assert cfg.max_multiplier == 3.0
        assert cfg.seed == 42

    def test_from_dict_ignores_unknown_keys(self):
        cfg = JitterConfig.from_dict({"strategy": "equal", "unknown": "value"})
        assert cfg.strategy == JitterStrategy.EQUAL

    def test_from_dict_invalid_strategy(self):
        with pytest.raises(ValueError):
            JitterConfig.from_dict({"strategy": "bogus"})


class TestJitterApplicator:
    def _make(self, strategy: str = "none", seed: int = 0, **kwargs) -> JitterApplicator:
        cfg = JitterConfig.from_dict({"strategy": strategy, "seed": seed, **kwargs})
        return JitterApplicator(cfg)

    def test_none_returns_base(self):
        app = self._make("none")
        assert app.apply(1.5) == 1.5
        assert app.apply(0.0) == 0.0

    def test_full_jitter_within_range(self):
        app = self._make("full", seed=7)
        for _ in range(20):
            result = app.apply(4.0)
            assert 0.0 <= result <= 4.0

    def test_equal_jitter_within_range(self):
        app = self._make("equal", seed=3)
        for _ in range(20):
            result = app.apply(2.0)
            assert 1.0 <= result <= 2.0

    def test_decorrelated_jitter_respects_min(self):
        app = self._make("decorrelated", seed=1, min_delay=0.5)
        for _ in range(20):
            result = app.apply(2.0)
            assert result >= 0.5

    def test_reset_restores_state(self):
        app = self._make("full", seed=99)
        first_run = [app.apply(5.0) for _ in range(5)]
        app.reset()
        second_run = [app.apply(5.0) for _ in range(5)]
        assert first_run == second_run


class TestJitterBridge:
    def _make(self, **kwargs) -> FileConfig:
        defaults = {
            "jitter_strategy": None,
            "jitter_min_delay": None,
            "jitter_max_multiplier": None,
        }
        defaults.update(kwargs)
        fc = FileConfig.__new__(FileConfig)
        for k, v in defaults.items():
            setattr(fc, k, v)
        return fc

    def test_defaults_produce_none_strategy(self):
        cfg = jitter_config_from_file(self._make())
        assert cfg.strategy == JitterStrategy.NONE

    def test_strategy_forwarded(self):
        cfg = jitter_config_from_file(self._make(jitter_strategy="full"))
        assert cfg.strategy == JitterStrategy.FULL

    def test_min_delay_forwarded(self):
        cfg = jitter_config_from_file(self._make(jitter_min_delay=0.25))
        assert cfg.min_delay == 0.25

    def test_max_multiplier_forwarded(self):
        cfg = jitter_config_from_file(self._make(jitter_max_multiplier=4.0))
        assert cfg.max_multiplier == 4.0
