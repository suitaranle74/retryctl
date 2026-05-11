"""Tests for retryctl.fallback_bridge."""
from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from retryctl.fallback_bridge import fallback_config_from_file


class TestFallbackConfigFromFile(unittest.TestCase):
    def _make(
        self,
        enabled=None,
        command=None,
        capture_output=None,
    ):
        fc = MagicMock()
        fc.fallback_enabled = enabled
        fc.fallback_command = command
        fc.fallback_capture_output = capture_output
        return fc

    def test_defaults_produce_disabled_fallback(self):
        cfg = fallback_config_from_file(self._make())
        self.assertFalse(cfg.enabled)
        self.assertEqual(cfg.command, [])
        self.assertTrue(cfg.capture_output)

    def test_enabled_forwarded(self):
        cfg = fallback_config_from_file(self._make(enabled=True))
        self.assertTrue(cfg.enabled)

    def test_command_forwarded(self):
        cfg = fallback_config_from_file(self._make(command=["curl", "http://backup"]))
        self.assertEqual(cfg.command, ["curl", "http://backup"])

    def test_capture_output_forwarded(self):
        cfg = fallback_config_from_file(self._make(capture_output=False))
        self.assertFalse(cfg.capture_output)

    def test_all_fields_forwarded(self):
        cfg = fallback_config_from_file(
            self._make(enabled=True, command=["sh", "fallback.sh"], capture_output=True)
        )
        self.assertTrue(cfg.enabled)
        self.assertEqual(cfg.command, ["sh", "fallback.sh"])
        self.assertTrue(cfg.capture_output)
