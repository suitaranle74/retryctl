"""Bridge between FileConfig and DebounceConfig."""
from __future__ import annotations

from retryctl.config import FileConfig
from retryctl.debounce import DebounceConfig


def debounce_config_from_file(fc: FileConfig) -> DebounceConfig:
    """Build a :class:`DebounceConfig` from a :class:`FileConfig`.

    Reads the ``debounce`` section of the file config when present.
    Falls back to defaults when the section is absent.
    """
    raw: dict = {}
    if fc.debounce is not None:
        raw = fc.debounce
    return DebounceConfig.from_dict(raw)
