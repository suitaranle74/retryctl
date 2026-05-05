"""Tests for retryctl.profile."""
import pytest

from retryctl.profile import (
    ProfileConfig,
    ProfileRegistry,
    load_profiles,
)


class TestProfileConfig:
    def test_defaults(self):
        p = ProfileConfig()
        assert p.name == "default"
        assert p.description == ""
        assert p.tags == []
        assert p.settings == {}

    def test_from_dict_full(self):
        p = ProfileConfig.from_dict({
            "name": "aggressive",
            "description": "Retry hard",
            "tags": ["prod", "critical"],
            "max_attempts": 10,
            "initial_delay": 0.1,
        })
        assert p.name == "aggressive"
        assert p.description == "Retry hard"
        assert p.tags == ["prod", "critical"]
        assert p.settings["max_attempts"] == 10
        assert p.settings["initial_delay"] == 0.1

    def test_from_dict_ignores_meta_keys_in_settings(self):
        p = ProfileConfig.from_dict({"name": "x", "description": "y", "tags": []})
        assert "name" not in p.settings
        assert "description" not in p.settings
        assert "tags" not in p.settings

    def test_from_dict_empty(self):
        p = ProfileConfig.from_dict({})
        assert p.name == "default"
        assert p.settings == {}


class TestProfileRegistry:
    def _make(self):
        return ProfileRegistry()

    def test_register_and_get(self):
        reg = self._make()
        p = ProfileConfig(name="fast")
        reg.register(p)
        assert reg.get("fast") is p

    def test_get_missing_returns_none(self):
        reg = self._make()
        assert reg.get("nonexistent") is None

    def test_names_sorted(self):
        reg = self._make()
        reg.register(ProfileConfig(name="zebra"))
        reg.register(ProfileConfig(name="alpha"))
        assert reg.names() == ["alpha", "zebra"]

    def test_merge_into_applies_profile_then_base_wins(self):
        reg = self._make()
        reg.register(ProfileConfig(name="p", settings={"max_attempts": 5, "initial_delay": 1.0}))
        result = reg.merge_into("p", {"max_attempts": 3})
        assert result["max_attempts"] == 3   # caller override wins
        assert result["initial_delay"] == 1.0  # from profile

    def test_merge_into_unknown_profile_returns_base(self):
        reg = self._make()
        base = {"max_attempts": 2}
        result = reg.merge_into("missing", base)
        assert result == {"max_attempts": 2}

    def test_register_replaces_existing(self):
        reg = self._make()
        reg.register(ProfileConfig(name="p", settings={"x": 1}))
        reg.register(ProfileConfig(name="p", settings={"x": 99}))
        assert reg.get("p").settings["x"] == 99


class TestLoadProfiles:
    def test_empty_list(self):
        reg = load_profiles([])
        assert reg.names() == []

    def test_multiple_profiles(self):
        reg = load_profiles([
            {"name": "a", "max_attempts": 1},
            {"name": "b", "max_attempts": 5},
        ])
        assert set(reg.names()) == {"a", "b"}
        assert reg.get("a").settings["max_attempts"] == 1
