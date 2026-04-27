"""Tests for retryctl.config module."""

from __future__ import annotations

import json
import os
import tempfile
import unittest

from retryctl.config import FileConfig, load_config


class TestFileConfig(unittest.TestCase):
    def test_defaults(self):
        cfg = FileConfig()
        self.assertEqual(cfg.max_attempts, 3)
        self.assertAlmostEqual(cfg.initial_delay, 1.0)
        self.assertAlmostEqual(cfg.multiplier, 2.0)
        self.assertAlmostEqual(cfg.max_delay, 60.0)
        self.assertTrue(cfg.jitter)
        self.assertFalse(cfg.alert_on_failure)
        self.assertFalse(cfg.alert_on_success)
        self.assertIsNone(cfg.shell_hook)
        self.assertEqual(cfg.env, {})

    def test_from_dict_partial(self):
        cfg = FileConfig.from_dict({"max_attempts": 5, "jitter": False})
        self.assertEqual(cfg.max_attempts, 5)
        self.assertFalse(cfg.jitter)
        self.assertAlmostEqual(cfg.initial_delay, 1.0)  # default preserved

    def test_from_dict_ignores_unknown_keys(self):
        cfg = FileConfig.from_dict({"max_attempts": 2, "unknown_key": "ignored"})
        self.assertEqual(cfg.max_attempts, 2)
        self.assertFalse(hasattr(cfg, "unknown_key"))


class TestLoadConfig(unittest.TestCase):
    def _write_tmp(self, content: str, suffix: str) -> str:
        fd, path = tempfile.mkstemp(suffix=suffix)
        with os.fdopen(fd, "w") as fh:
            fh.write(content)
        return path

    def test_load_json(self):
        data = {"max_attempts": 7, "initial_delay": 0.5, "shell_hook": "echo done"}
        path = self._write_tmp(json.dumps(data), ".json")
        try:
            cfg = load_config(path)
            self.assertEqual(cfg.max_attempts, 7)
            self.assertAlmostEqual(cfg.initial_delay, 0.5)
            self.assertEqual(cfg.shell_hook, "echo done")
        finally:
            os.unlink(path)

    def test_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            load_config("/nonexistent/path/retryctl.yaml")

    def test_unsupported_extension(self):
        path = self._write_tmp("{}", ".toml")
        try:
            with self.assertRaises(ValueError, msg="Unsupported format should raise"):
                load_config(path)
        finally:
            os.unlink(path)

    def test_invalid_json_structure(self):
        path = self._write_tmp(json.dumps([1, 2, 3]), ".json")
        try:
            with self.assertRaises(ValueError):
                load_config(path)
        finally:
            os.unlink(path)

    def test_empty_json_uses_defaults(self):
        path = self._write_tmp("{}", ".json")
        try:
            cfg = load_config(path)
            self.assertEqual(cfg.max_attempts, 3)
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
