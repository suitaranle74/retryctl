"""Tests for retryctl.cli entry point."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from retryctl.cli import build_parser, main


class TestBuildParser:
    def test_defaults(self):
        parser = build_parser()
        args = parser.parse_args(["echo", "hi"])
        assert args.attempts == 3
        assert args.base_delay == 1.0
        assert args.max_delay == 60.0
        assert args.multiplier == 2.0
        assert args.jitter is False
        assert args.on_failure_cmd is None

    def test_custom_flags(self):
        parser = build_parser()
        args = parser.parse_args(
            ["-n", "5", "--base-delay", "0.5", "--jitter", "--on-failure-cmd", "echo fail", "ls"]
        )
        assert args.attempts == 5
        assert args.base_delay == 0.5
        assert args.jitter is True
        assert args.on_failure_cmd == "echo fail"


class TestMain:
    def _fake_run_result(self, exit_code: int):
        attempt = MagicMock()
        attempt.exit_code = exit_code
        result = MagicMock()
        result.last = attempt
        return result

    def test_success_returns_zero(self):
        with patch("retryctl.cli.Runner") as MockRunner:
            instance = MockRunner.return_value
            instance.run.return_value = self._fake_run_result(0)
            code = main(["echo", "hello"])
        assert code == 0

    def test_failure_returns_nonzero(self):
        with patch("retryctl.cli.Runner") as MockRunner:
            instance = MockRunner.return_value
            instance.run.return_value = self._fake_run_result(1)
            code = main(["false"])
        assert code == 1

    def test_no_command_exits(self):
        with pytest.raises(SystemExit):
            main([])
