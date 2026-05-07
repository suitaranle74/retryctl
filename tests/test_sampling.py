"""Tests for retryctl.sampling."""

from __future__ import annotations

import pytest

from retryctl.sampling import SamplingConfig, SamplingEvaluator


class TestSamplingConfig:
    def test_defaults(self):
        cfg = SamplingConfig()
        assert cfg.enabled is False
        assert cfg.rate == 1.0
        assert cfg.seed is None

    def test_custom_values(self):
        cfg = SamplingConfig(enabled=True, rate=0.5, seed=42)
        assert cfg.enabled is True
        assert cfg.rate == 0.5
        assert cfg.seed == 42

    def test_from_dict_full(self):
        cfg = SamplingConfig.from_dict({"enabled": True, "rate": 0.25, "seed": 7})
        assert cfg.enabled is True
        assert cfg.rate == 0.25
        assert cfg.seed == 7

    def test_from_dict_partial(self):
        cfg = SamplingConfig.from_dict({"enabled": True})
        assert cfg.enabled is True
        assert cfg.rate == 1.0

    def test_from_dict_ignores_unknown_keys(self):
        cfg = SamplingConfig.from_dict({"enabled": True, "unknown": "value"})
        assert cfg.enabled is True

    def test_validate_passes_on_valid_rate(self):
        SamplingConfig(enabled=True, rate=0.5).validate()

    def test_validate_raises_on_negative_rate(self):
        with pytest.raises(ValueError, match="sampling rate"):
            SamplingConfig(enabled=True, rate=-0.1).validate()

    def test_validate_raises_on_rate_above_one(self):
        with pytest.raises(ValueError, match="sampling rate"):
            SamplingConfig(enabled=True, rate=1.1).validate()


class TestSamplingEvaluator:
    def _make(self, **kwargs) -> SamplingEvaluator:
        return SamplingEvaluator(SamplingConfig(**kwargs))

    def test_disabled_never_samples(self):
        ev = self._make(enabled=False, rate=1.0)
        assert ev.should_sample() is False
        assert ev.should_sample(attempt_number=5) is False

    def test_enabled_rate_one_always_samples(self):
        ev = self._make(enabled=True, rate=1.0)
        for i in range(10):
            assert ev.should_sample(attempt_number=i) is True

    def test_enabled_rate_zero_never_samples(self):
        ev = self._make(enabled=True, rate=0.0)
        for i in range(10):
            assert ev.should_sample(attempt_number=i) is False

    def test_deterministic_with_seed(self):
        ev1 = self._make(enabled=True, rate=0.5, seed=99)
        ev2 = self._make(enabled=True, rate=0.5, seed=99)
        results1 = [ev1.should_sample(i) for i in range(20)]
        results2 = [ev2.should_sample(i) for i in range(20)]
        assert results1 == results2

    def test_reset_replays_same_sequence(self):
        ev = self._make(enabled=True, rate=0.5, seed=42)
        first_run = [ev.should_sample(i) for i in range(10)]
        ev.reset()
        second_run = [ev.should_sample(i) for i in range(10)]
        assert first_run == second_run

    def test_partial_rate_samples_approximately(self):
        ev = self._make(enabled=True, rate=0.3, seed=0)
        hits = sum(ev.should_sample(i) for i in range(1000))
        # Allow generous tolerance for probabilistic test
        assert 200 <= hits <= 420
