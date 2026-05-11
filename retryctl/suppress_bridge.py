"""Bridge: build SuppressConfig from a FileConfig instance."""
from __future__ import annotations

from retryctl.suppress import SuppressConfig


def suppress_config_from_file(file_config) -> SuppressConfig:
    """Construct a SuppressConfig from a FileConfig object.

    Falls back to defaults when the file config has no suppress section.
    """
    data = getattr(file_config, "suppress", None)
    if not data:
        return SuppressConfig()
    return SuppressConfig.from_dict(data)
