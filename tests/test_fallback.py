"""Tests for retryctl.fallback."""
from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from retryctl.fallback import FallbackConfig, FallbackResult, FallbackRunner


class TestFallbackConfig(unittest.TestCase):
    def test_defaults(self):
        cfg = FallbackConfig()
        self.assertFalse(cfg.enabled)
        self.assertEqual(cfg.command, [])
        self.assertTrue(cfg.capture_output)

    def test_custom_values(self):
        cfg = FallbackConfig(enabled=True, command=["echo", "hi"], capture_output=False)
        self.assertTrue(cfg.enabled)
        self.assertEqual(cfg.command, ["echo", "hi"])
        self.assertFalse(cfg.capture_output)

    def test_from_dict_full(self):
        cfg = FallbackConfig.from_dict(
            {"enabled": True, "command": ["ls", "-la"], "capture_output": False}
        )
        self.assertTrue(cfg.enabled)
        self.assertEqual(cfg.command, ["ls", "-la"])
        self.assertFalse(cfg.capture_output)

    def test_from_dict_string_command_splits(self):
        cfg = FallbackConfig.from_dict({"command": "echo hello"})
        self.assertEqual(cfg.command, ["echo", "hello"])

    def test_from_dict_ignores_unknown_keys(self):
        cfg = FallbackConfig.from_dict({"enabled": True, "unknown_key": "ignored"})
        self.assertTrue(cfg.enabled)


class TestFallbackResult(unittest.TestCase):
    def test_succeeded_on_zero(self):
        r = FallbackResult(exit_code=0)
        self.assertTrue(r.succeeded)

    def test_failed_on_nonzero(self):
        r = FallbackResult(exit_code=1)
        self.assertFalse(r.succeeded)


class TestFallbackRunner(unittest.TestCase):
    def _make(self, enabled=True, command=None):
        cmd = command if command is not None else ["echo", "fallback"]
        return FallbackRunner(FallbackConfig(enabled=enabled, command=cmd))

    def test_should_run_when_enabled_with_command(self):
        runner = self._make(enabled=True)
        self.assertTrue(runner.should_run())

    def test_should_not_run_when_disabled(self):
        runner = self._make(enabled=False)
        self.assertFalse(runner.should_run())

    def test_should_not_run_when_no_command(self):
        runner = self._make(enabled=True, command=[])
        self.assertFalse(runner.should_run())

    def test_run_returns_none_when_disabled(self):
        runner = self._make(enabled=False)
        self.assertIsNone(runner.run())

    def test_run_returns_result_on_success(self):
        mock_proc = MagicMock(returncode=0, stdout="ok\n", stderr="")
        with patch("subprocess.run", return_value=mock_proc):
            runner = self._make()
            result = runner.run()
        self.assertIsNotNone(result)
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.stdout, "ok\n")

    def test_run_returns_exit_127_on_file_not_found(self):
        with patch("subprocess.run", side_effect=FileNotFoundError("not found")):
            runner = self._make(command=["nonexistent_cmd"])
            result = runner.run()
        self.assertEqual(result.exit_code, 127)
        self.assertIn("not found", result.stderr)
