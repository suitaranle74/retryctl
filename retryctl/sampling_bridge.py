"""Bridge between FileConfig and SamplingConfig."""

from __future__ import annotations

from retryctl.config import FileConfig
from retryctl.sampling import SamplingConfig


def sampling_config_from_file(fc: FileConfig) -> SamplingConfig:
    """Build a SamplingConfig from a FileConfig instance.

    Reads the ``sampling`` sub-dict when present; falls back to defaults.
    """
    raw: dict = fc.sampling if isinstance(fc.sampling, dict) else {}
    cfg = SamplingConfig.from_dict(raw)
    cfg.validate()
    return cfg
