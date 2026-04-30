"""Tests for retryctl.snapshot and retryctl.snapshot_bridge."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from retryctl.snapshot import SnapshotConfig, AttemptSnapshot, SnapshotManager
from retryctl.snapshot_bridge import snapshot_config_from_file


class TestSnapshotConfig:
    def test_defaults(self):
        cfg = SnapshotConfig()
        assert cfg.enabled is False
        assert cfg.compare_stdout is True
        assert cfg.compare_exit_code is False

    def test_custom_values(self):
        cfg = SnapshotConfig(enabled=True, compare_stdout=False, compare_exit_code=True)
        assert cfg.enabled is True
        assert cfg.compare_stdout is False
        assert cfg.compare_exit_code is True

    def test_from_dict_full(self):
        cfg = SnapshotConfig.from_dict(
            {"enabled": True, "compare_stdout": False, "compare_exit_code": True}
        )
        assert cfg.enabled is True
        assert cfg.compare_stdout is False
        assert cfg.compare_exit_code is True

    def test_from_dict_ignores_unknown_keys(self):
        cfg = SnapshotConfig.from_dict({"enabled": True, "unknown": "value"})
        assert cfg.enabled is True


class TestAttemptSnapshot:
    def test_matches_same_stdout(self):
        cfg = SnapshotConfig(compare_stdout=True, compare_exit_code=False)
        a = AttemptSnapshot(stdout_hash="abc", exit_code=0)
        b = AttemptSnapshot(stdout_hash="abc", exit_code=1)
        assert a.matches(b, cfg) is True

    def test_not_matches_different_stdout(self):
        cfg = SnapshotConfig(compare_stdout=True, compare_exit_code=False)
        a = AttemptSnapshot(stdout_hash="abc", exit_code=0)
        b = AttemptSnapshot(stdout_hash="xyz", exit_code=0)
        assert a.matches(b, cfg) is False

    def test_matches_exit_code(self):
        cfg = SnapshotConfig(compare_stdout=False, compare_exit_code=True)
        a = AttemptSnapshot(stdout_hash=None, exit_code=0)
        b = AttemptSnapshot(stdout_hash=None, exit_code=0)
        assert a.matches(b, cfg) is True

    def test_to_dict_and_from_dict(self):
        snap = AttemptSnapshot(stdout_hash="deadbeef", exit_code=2)
        d = snap.to_dict()
        restored = AttemptSnapshot.from_dict(d)
        assert restored.stdout_hash == "deadbeef"
        assert restored.exit_code == 2


class TestSnapshotManager:
    def _make(self, **kwargs) -> SnapshotManager:
        return SnapshotManager(SnapshotConfig(**kwargs))

    def test_capture_hashes_stdout(self):
        mgr = self._make(compare_stdout=True)
        snap = mgr.capture(stdout="hello", exit_code=0)
        assert snap.stdout_hash is not None
        assert len(snap.stdout_hash) == 64  # sha256 hex

    def test_capture_omits_stdout_when_disabled(self):
        mgr = self._make(compare_stdout=False)
        snap = mgr.capture(stdout="hello", exit_code=0)
        assert snap.stdout_hash is None

    def test_has_changed_true_on_first_call(self):
        mgr = self._make()
        snap = mgr.capture(stdout="data", exit_code=0)
        assert mgr.has_changed(snap) is True

    def test_has_changed_false_when_same(self):
        mgr = self._make(compare_stdout=True)
        snap = mgr.capture(stdout="data", exit_code=0)
        mgr.record(snap)
        snap2 = mgr.capture(stdout="data", exit_code=0)
        assert mgr.has_changed(snap2) is False

    def test_has_changed_true_when_different(self):
        mgr = self._make(compare_stdout=True)
        snap = mgr.capture(stdout="data", exit_code=0)
        mgr.record(snap)
        snap2 = mgr.capture(stdout="different", exit_code=0)
        assert mgr.has_changed(snap2) is True

    def test_reset_clears_last(self):
        mgr = self._make()
        snap = mgr.capture(stdout="data", exit_code=0)
        mgr.record(snap)
        mgr.reset()
        assert mgr._last is None


class TestSnapshotBridge:
    def _make_file_config(self, **kwargs):
        fc = MagicMock()
        fc.snapshot_enabled = kwargs.get("snapshot_enabled", False)
        fc.snapshot_compare_stdout = kwargs.get("snapshot_compare_stdout", True)
        fc.snapshot_compare_exit_code = kwargs.get("snapshot_compare_exit_code", False)
        return fc

    def test_defaults_produce_disabled_snapshot(self):
        cfg = snapshot_config_from_file(self._make_file_config())
        assert cfg.enabled is False
        assert cfg.compare_stdout is True
        assert cfg.compare_exit_code is False

    def test_enabled_forwarded(self):
        cfg = snapshot_config_from_file(self._make_file_config(snapshot_enabled=True))
        assert cfg.enabled is True

    def test_compare_exit_code_forwarded(self):
        cfg = snapshot_config_from_file(
            self._make_file_config(snapshot_compare_exit_code=True)
        )
        assert cfg.compare_exit_code is True
