"""Bridge between FileConfig and ProfileRegistry."""
from __future__ import annotations

from typing import Any, Dict

from retryctl.config import FileConfig
from retryctl.profile import ProfileRegistry, load_profiles


def profile_registry_from_file(cfg: FileConfig) -> ProfileRegistry:
    """Return a :class:`ProfileRegistry` populated from *cfg*.

    ``FileConfig`` exposes a ``profiles`` list that contains raw dicts; each
    dict is converted into a :class:`~retryctl.profile.ProfileConfig` and
    registered.  When the field is absent an empty registry is returned.
    """
    raw: Any = getattr(cfg, "profiles", None) or []
    return load_profiles(raw)


def apply_profile(
    name: str,
    registry: ProfileRegistry,
    overrides: Dict[str, Any],
) -> Dict[str, Any]:
    """Return *overrides* merged on top of the named profile's settings.

    CLI / caller-supplied *overrides* always win over profile defaults.
    """
    return registry.merge_into(name, overrides)
