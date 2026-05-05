"""Tests for retryctl.profile_bridge."""
from unittest.mock import MagicMock

from retryctl.config import FileConfig
from retryctl.profile import ProfileConfig, ProfileRegistry
from retryctl.profile_bridge import apply_profile, profile_registry_from_file


class TestProfileRegistryFromFile:
    def _make(self, profiles=None):
        cfg = MagicMock(spec=FileConfig)
        cfg.profiles = profiles
        return cfg

    def test_no_profiles_field_returns_empty_registry(self):
        cfg = MagicMock(spec=[])
        # object has no 'profiles' attribute at all
        reg = profile_registry_from_file(cfg)
        assert isinstance(reg, ProfileRegistry)
        assert reg.names() == []

    def test_none_profiles_returns_empty_registry(self):
        cfg = self._make(profiles=None)
        reg = profile_registry_from_file(cfg)
        assert reg.names() == []

    def test_profiles_are_registered(self):
        cfg = self._make(profiles=[
            {"name": "fast", "max_attempts": 2},
            {"name": "slow", "max_attempts": 10},
        ])
        reg = profile_registry_from_file(cfg)
        assert set(reg.names()) == {"fast", "slow"}

    def test_profile_settings_forwarded(self):
        cfg = self._make(profiles=[{"name": "p", "initial_delay": 0.5}])
        reg = profile_registry_from_file(cfg)
        assert reg.get("p").settings["initial_delay"] == 0.5


class TestApplyProfile:
    def _make_registry(self, name, settings):
        reg = ProfileRegistry()
        reg.register(ProfileConfig(name=name, settings=settings))
        return reg

    def test_profile_defaults_applied(self):
        reg = self._make_registry("base", {"max_attempts": 5})
        result = apply_profile("base", reg, {})
        assert result["max_attempts"] == 5

    def test_overrides_win_over_profile(self):
        reg = self._make_registry("base", {"max_attempts": 5})
        result = apply_profile("base", reg, {"max_attempts": 1})
        assert result["max_attempts"] == 1

    def test_missing_profile_returns_overrides_unchanged(self):
        reg = ProfileRegistry()
        result = apply_profile("ghost", reg, {"max_attempts": 3})
        assert result == {"max_attempts": 3}
