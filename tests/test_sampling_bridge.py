"""Tests for retryctl.sampling_bridge."""

from __future__ import annotations

import pytest

from retryctl.config import FileConfig
from retryctl.sampling import SamplingConfig
from retryctl.sampling_bridge import sampling_config_from_file


class TestSamplingConfigFromFile:
    def _make(self, sampling: dict | None = None) -> FileConfig:
        fc = FileConfig()
        if sampling is not None:
            fc.sampling = sampling
        return fc

    def test_defaults_produce_disabled_sampling(self):
        cfg = sampling_config_from_file(self._make())
        assert isinstance(cfg, SamplingConfig)
        assert cfg.enabled is False
        assert cfg.rate == 1.0

    def test_enabled_forwarded(self):
        cfg = sampling_config_from_file(self._make({"enabled": True}))
        assert cfg.enabled is True

    def test_rate_forwarded(self):
        cfg = sampling_config_from_file(self._make({"enabled": True, "rate": 0.5}))
        assert cfg.rate == 0.5

    def test_seed_forwarded(self):
        cfg = sampling_config_from_file(self._make({"enabled": True, "seed": 123}))
        assert cfg.seed == 123

    def test_invalid_rate_raises(self):
        with pytest.raises(ValueError, match="sampling rate"):
            sampling_config_from_file(self._make({"enabled": True, "rate": 2.0}))

    def test_non_dict_sampling_falls_back_to_defaults(self):
        fc = FileConfig()
        fc.sampling = None  # type: ignore[assignment]
        cfg = sampling_config_from_file(fc)
        assert cfg.enabled is False
