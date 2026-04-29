"""Tests for retryctl.labels."""
import pytest
from retryctl.labels import LabelsConfig, AttemptLabels, LabelResolver


class TestLabelsConfig:
    def test_defaults(self):
        cfg = LabelsConfig()
        assert cfg.static == {}
        assert cfg.include_attempt_number is True
        assert cfg.include_command_hash is False
        assert cfg.prefix == ""

    def test_custom_values(self):
        cfg = LabelsConfig(
            static={"env": "prod"},
            include_attempt_number=False,
            include_command_hash=True,
            prefix="app_",
        )
        assert cfg.static == {"env": "prod"}
        assert cfg.include_attempt_number is False
        assert cfg.include_command_hash is True
        assert cfg.prefix == "app_"

    def test_from_dict_partial(self):
        cfg = LabelsConfig.from_dict({"prefix": "x_", "include_command_hash": True})
        assert cfg.prefix == "x_"
        assert cfg.include_command_hash is True
        assert cfg.include_attempt_number is True  # default

    def test_from_dict_ignores_unknown_keys(self):
        cfg = LabelsConfig.from_dict({"unknown_key": "value", "prefix": "p_"})
        assert cfg.prefix == "p_"


class TestAttemptLabels:
    def test_get_existing_key(self):
        al = AttemptLabels(labels={"attempt": "1"})
        assert al.get("attempt") == "1"

    def test_get_missing_key_returns_default(self):
        al = AttemptLabels(labels={})
        assert al.get("missing", "fallback") == "fallback"

    def test_as_env_uppercases_keys(self):
        al = AttemptLabels(labels={"attempt": "3", "env": "staging"})
        env = al.as_env()
        assert env["RETRYCTL_LABEL_ATTEMPT"] == "3"
        assert env["RETRYCTL_LABEL_ENV"] == "staging"


class TestLabelResolver:
    def _make(self, **kwargs) -> LabelResolver:
        cfg = LabelsConfig(**kwargs)
        return LabelResolver(cfg, command="echo hello")

    def test_includes_attempt_number_by_default(self):
        resolver = self._make()
        labels = resolver.resolve(attempt_number=2)
        assert labels.get("attempt") == "2"

    def test_excludes_attempt_number_when_disabled(self):
        resolver = self._make(include_attempt_number=False)
        labels = resolver.resolve(attempt_number=1)
        assert labels.get("attempt") is None

    def test_static_labels_are_included(self):
        resolver = self._make(static={"region": "us-east-1"})
        labels = resolver.resolve(attempt_number=1)
        assert labels.get("region") == "us-east-1"

    def test_command_hash_included_when_enabled(self):
        resolver = self._make(include_command_hash=True)
        labels = resolver.resolve(attempt_number=1)
        assert labels.get("command_hash") is not None
        assert len(labels.get("command_hash")) == 8

    def test_prefix_applied_to_all_keys(self):
        resolver = self._make(
            static={"env": "prod"},
            include_attempt_number=True,
            prefix="app_",
        )
        labels = resolver.resolve(attempt_number=1)
        assert labels.get("app_attempt") == "1"
        assert labels.get("app_env") == "prod"
        assert labels.get("attempt") is None

    def test_same_command_produces_same_hash(self):
        r1 = LabelResolver(LabelsConfig(include_command_hash=True), command="ls -la")
        r2 = LabelResolver(LabelsConfig(include_command_hash=True), command="ls -la")
        h1 = r1.resolve(1).get("command_hash")
        h2 = r2.resolve(1).get("command_hash")
        assert h1 == h2

    def test_different_commands_produce_different_hashes(self):
        r1 = LabelResolver(LabelsConfig(include_command_hash=True), command="ls -la")
        r2 = LabelResolver(LabelsConfig(include_command_hash=True), command="echo hi")
        h1 = r1.resolve(1).get("command_hash")
        h2 = r2.resolve(1).get("command_hash")
        assert h1 != h2
