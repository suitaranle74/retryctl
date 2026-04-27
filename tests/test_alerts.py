"""Tests for retryctl.alerts."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from retryctl.alerts import AlertConfig, AlertManager


class TestAlertConfig:
    def test_defaults(self):
        cfg = AlertConfig()
        assert cfg.on_failure_cmd is None
        assert cfg.on_failure_hooks == []
        assert cfg.alert_every_attempt is False

    def test_custom_values(self):
        hook = lambda cmd, attempts, code: None
        cfg = AlertConfig(
            on_failure_cmd="echo {cmd}",
            on_failure_hooks=[hook],
            alert_every_attempt=True,
        )
        assert cfg.on_failure_cmd == "echo {cmd}"
        assert hook in cfg.on_failure_hooks
        assert cfg.alert_every_attempt is True


class TestAlertManager:
    def _make(self, **kwargs) -> AlertManager:
        return AlertManager(AlertConfig(**kwargs))

    def test_python_hook_called(self):
        hook = MagicMock()
        mgr = self._make(on_failure_hooks=[hook])
        mgr.notify("ls", 3, 1)
        hook.assert_called_once_with("ls", 3, 1)

    def test_multiple_hooks_called(self):
        hooks = [MagicMock(), MagicMock()]
        mgr = self._make(on_failure_hooks=hooks)
        mgr.notify("ls", 1, 2)
        for h in hooks:
            h.assert_called_once_with("ls", 1, 2)

    def test_failing_hook_does_not_raise(self):
        bad_hook = MagicMock(side_effect=RuntimeError("boom"))
        mgr = self._make(on_failure_hooks=[bad_hook])
        mgr.notify("ls", 1, 1)  # should not raise

    def test_shell_hook_interpolation(self):
        with patch("retryctl.alerts.subprocess.run") as mock_run:
            mgr = self._make(on_failure_cmd="echo {cmd} {attempts} {exit_code}")
            mgr.notify("ls -la", 2, 127)
            mock_run.assert_called_once()
            call_args = mock_run.call_args
            assert "ls -la" in call_args[0][0]
            assert "127" in call_args[0][0]

    def test_no_shell_hook_when_none(self):
        with patch("retryctl.alerts.subprocess.run") as mock_run:
            mgr = self._make()
            mgr.notify("ls", 1, 1)
            mock_run.assert_not_called()
