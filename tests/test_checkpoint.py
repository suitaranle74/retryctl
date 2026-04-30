"""Tests for retryctl.checkpoint."""
import json
import os
import time
import pytest

from retryctl.checkpoint import (
    CheckpointConfig,
    CheckpointState,
    CheckpointManager,
)


class TestCheckpointConfig:
    def test_defaults(self):
        cfg = CheckpointConfig()
        assert cfg.enabled is False
        assert cfg.path is None
        assert cfg.ttl_seconds is None

    def test_custom_values(self):
        cfg = CheckpointConfig(enabled=True, path="/tmp/cp.json", ttl_seconds=300.0)
        assert cfg.enabled is True
        assert cfg.path == "/tmp/cp.json"
        assert cfg.ttl_seconds == 300.0

    def test_from_dict_full(self):
        cfg = CheckpointConfig.from_dict(
            {"enabled": True, "path": "/tmp/cp.json", "ttl_seconds": 60.0}
        )
        assert cfg.enabled is True
        assert cfg.path == "/tmp/cp.json"
        assert cfg.ttl_seconds == 60.0

    def test_from_dict_ignores_unknown_keys(self):
        cfg = CheckpointConfig.from_dict({"unknown": "value"})
        assert cfg.enabled is False


class TestCheckpointState:
    def test_round_trip(self):
        s = CheckpointState(attempt=3, last_exit_code=1)
        restored = CheckpointState.from_dict(s.to_dict())
        assert restored.attempt == 3
        assert restored.last_exit_code == 1

    def test_defaults(self):
        s = CheckpointState()
        assert s.attempt == 0
        assert s.last_exit_code is None


class TestCheckpointManager:
    def _make(self, tmp_path, enabled=True, ttl=None):
        p = str(tmp_path / "cp.json")
        cfg = CheckpointConfig(enabled=enabled, path=p, ttl_seconds=ttl)
        return CheckpointManager(cfg), p

    def test_load_returns_none_when_disabled(self, tmp_path):
        mgr, _ = self._make(tmp_path, enabled=False)
        assert mgr.load() is None

    def test_save_and_load(self, tmp_path):
        mgr, _ = self._make(tmp_path)
        state = CheckpointState(attempt=2, last_exit_code=127)
        mgr.save(state)
        loaded = mgr.load()
        assert loaded is not None
        assert loaded.attempt == 2
        assert loaded.last_exit_code == 127

    def test_load_returns_none_when_file_missing(self, tmp_path):
        mgr, _ = self._make(tmp_path)
        assert mgr.load() is None

    def test_clear_removes_file(self, tmp_path):
        mgr, path = self._make(tmp_path)
        mgr.save(CheckpointState(attempt=1))
        assert os.path.exists(path)
        mgr.clear()
        assert not os.path.exists(path)

    def test_ttl_expiry_returns_none(self, tmp_path):
        mgr, path = self._make(tmp_path, ttl=1.0)
        old_state = CheckpointState(attempt=1, created_at=time.time() - 10)
        with open(path, "w") as fh:
            json.dump(old_state.to_dict(), fh)
        assert mgr.load() is None
        assert not os.path.exists(path)

    def test_ttl_not_expired(self, tmp_path):
        mgr, _ = self._make(tmp_path, ttl=3600.0)
        mgr.save(CheckpointState(attempt=5))
        loaded = mgr.load()
        assert loaded is not None
        assert loaded.attempt == 5

    def test_save_noop_when_disabled(self, tmp_path):
        mgr, path = self._make(tmp_path, enabled=False)
        mgr.save(CheckpointState(attempt=1))
        assert not os.path.exists(path)
