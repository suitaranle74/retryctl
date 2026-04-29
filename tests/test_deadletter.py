"""Tests for retryctl.deadletter and retryctl.deadletter_bridge."""
import os
import tempfile
import unittest
from unittest.mock import MagicMock

from retryctl.deadletter import DeadLetterConfig, DeadLetterEntry, DeadLetterQueue
from retryctl.deadletter_bridge import deadletter_config_from_file


class TestDeadLetterConfig(unittest.TestCase):
    def test_defaults(self):
        cfg = DeadLetterConfig()
        self.assertFalse(cfg.enabled)
        self.assertEqual(cfg.max_entries, 100)
        self.assertIn("retryctl", cfg.path)

    def test_from_dict_full(self):
        cfg = DeadLetterConfig.from_dict(
            {"enabled": True, "path": "/tmp/dl.jsonl", "max_entries": 10}
        )
        self.assertTrue(cfg.enabled)
        self.assertEqual(cfg.path, "/tmp/dl.jsonl")
        self.assertEqual(cfg.max_entries, 10)

    def test_from_dict_ignores_unknown_keys(self):
        cfg = DeadLetterConfig.from_dict({"unknown": "value"})
        self.assertFalse(cfg.enabled)


class TestDeadLetterEntry(unittest.TestCase):
    def _make(self, **kw):
        defaults = dict(command=["ls", "-la"], exit_code=1, attempts=3)
        defaults.update(kw)
        return DeadLetterEntry(**defaults)

    def test_roundtrip_json(self):
        entry = self._make(stderr_tail="err", labels={"env": "prod"})
        restored = DeadLetterEntry.from_json(entry.to_json())
        self.assertEqual(restored.command, ["ls", "-la"])
        self.assertEqual(restored.exit_code, 1)
        self.assertEqual(restored.labels, {"env": "prod"})
        self.assertEqual(restored.stderr_tail, "err")

    def test_timestamp_auto_set(self):
        entry = self._make()
        self.assertGreater(entry.timestamp, 0)


class TestDeadLetterQueue(unittest.TestCase):
    def _queue(self, **kw):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jsonl") as f:
            path = f.name
        os.unlink(path)  # start without the file
        cfg = DeadLetterConfig(enabled=True, path=path, **kw)
        return DeadLetterQueue(cfg), path

    def tearDown(self):
        # Best-effort cleanup handled per test
        pass

    def test_push_and_entries(self):
        q, path = self._queue()
        try:
            entry = DeadLetterEntry(command=["false"], exit_code=1, attempts=2)
            q.push(entry)
            result = q.entries()
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0].command, ["false"])
        finally:
            if os.path.exists(path):
                os.unlink(path)

    def test_disabled_push_is_noop(self):
        cfg = DeadLetterConfig(enabled=False)
        q = DeadLetterQueue(cfg)
        q.push(DeadLetterEntry(command=["x"], exit_code=1, attempts=1))
        self.assertEqual(q.entries(), [])

    def test_max_entries_trim(self):
        q, path = self._queue(max_entries=3)
        try:
            for i in range(5):
                q.push(DeadLetterEntry(command=[str(i)], exit_code=i, attempts=1))
            entries = q.entries()
            self.assertEqual(len(entries), 3)
            self.assertEqual(entries[0].command, ["2"])  # oldest kept
        finally:
            if os.path.exists(path):
                os.unlink(path)

    def test_clear_removes_file(self):
        q, path = self._queue()
        try:
            q.push(DeadLetterEntry(command=["x"], exit_code=1, attempts=1))
            q.clear()
            self.assertFalse(os.path.exists(path))
        finally:
            if os.path.exists(path):
                os.unlink(path)


class TestDeadLetterBridge(unittest.TestCase):
    def _make(self, **kw):
        fc = MagicMock()
        fc.deadletter_enabled = kw.get("deadletter_enabled", None)
        fc.deadletter_path = kw.get("deadletter_path", None)
        fc.deadletter_max_entries = kw.get("deadletter_max_entries", None)
        return fc

    def test_defaults_produce_disabled_config(self):
        cfg = deadletter_config_from_file(self._make())
        self.assertFalse(cfg.enabled)

    def test_enabled_forwarded(self):
        cfg = deadletter_config_from_file(self._make(deadletter_enabled=True))
        self.assertTrue(cfg.enabled)

    def test_path_forwarded(self):
        cfg = deadletter_config_from_file(self._make(deadletter_path="/var/dl.jsonl"))
        self.assertEqual(cfg.path, "/var/dl.jsonl")

    def test_max_entries_forwarded(self):
        cfg = deadletter_config_from_file(self._make(deadletter_max_entries=50))
        self.assertEqual(cfg.max_entries, 50)


if __name__ == "__main__":
    unittest.main()
