"""Named retry profiles for reusable configuration presets."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ProfileConfig:
    """A named collection of retry settings that can be referenced by name."""

    name: str = "default"
    description: str = ""
    tags: List[str] = field(default_factory=list)
    # Raw key/value overrides that will be merged into FileConfig
    settings: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProfileConfig":
        return cls(
            name=data.get("name", "default"),
            description=data.get("description", ""),
            tags=list(data.get("tags", [])),
            settings={k: v for k, v in data.items()
                      if k not in ("name", "description", "tags")},
        )


class ProfileRegistry:
    """Stores and retrieves named profiles."""

    def __init__(self) -> None:
        self._profiles: Dict[str, ProfileConfig] = {}

    def register(self, profile: ProfileConfig) -> None:
        """Add or replace a profile by name."""
        self._profiles[profile.name] = profile

    def get(self, name: str) -> Optional[ProfileConfig]:
        """Return the profile with *name*, or None if not found."""
        return self._profiles.get(name)

    def names(self) -> List[str]:
        """Return sorted list of registered profile names."""
        return sorted(self._profiles.keys())

    def merge_into(self, name: str, base: Dict[str, Any]) -> Dict[str, Any]:
        """Return *base* dict updated with the named profile's settings.

        Unknown profile names are silently ignored so callers do not need to
        guard against missing profiles.
        """
        profile = self.get(name)
        if profile is None:
            return dict(base)
        merged = dict(profile.settings)
        merged.update(base)
        return merged


def load_profiles(data: List[Dict[str, Any]]) -> ProfileRegistry:
    """Build a :class:`ProfileRegistry` from a list of raw profile dicts."""
    registry = ProfileRegistry()
    for item in data:
        registry.register(ProfileConfig.from_dict(item))
    return registry
