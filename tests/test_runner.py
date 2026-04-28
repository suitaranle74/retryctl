"""Tests for retryctl.runner — RunnerConfig, AttemptResult, RunResult, and Runner."""

import subprocess
import time
from unittest.mock import MagicMock, patch

import pytest

from retryctl.backoff import BackoffConfig
from retryctl.runner import AttemptResult, RunResult, Runner, RunnerConfig


class TestRunnerConfig:
    def test_defaults(self):
        cfg = RunnerConfig(command=["echo", "hi"])
        assert cfg.command == ["echo", "hi"]
        assert cfg.max_attempts == 3
        assert cfg.timeout is None
        assert cfg.env is None
        assert cfg.shell is False

    def test_custom_values(self):
        cfg = RunnerConfig(
            command=["false"],
            max_attempts=5,
            timeout=10.0,
            shell=True,
            env={"FOO": "bar"},
        )
        assert cfg.max_attempts == 5
        assert cfg.timeout == 10.0
        assert cfg.shell is True
        assert cfg.env == {"FOO": "bar"}


class TestAttemptResult:
    def test_succeeded_zero_exit(self):
        r = AttemptResult(attempt=1, returncode=0, stdout="ok", stderr="", duration=0.1)
        assert r.succeeded is True

    def test_succeeded_nonzero_exit(self):
        r = AttemptResult(attempt=1, returncode=1, stdout="", stderr="err", duration=0.2)
        assert r.succeeded is False


class TestRunResult:
    def _make_attempts(self, codes):
        return [
            AttemptResult(attempt=i + 1, returncode=c, stdout="", stderr="", duration=0.0)
            for i, c in enumerate(codes)
        ]

    def test_last_returns_final_attempt(self):
        attempts = self._make_attempts([1, 1, 0])
        result = RunResult(attempts=attempts)
        assert result.last.returncode == 0
        assert result.last.attempt == 3

    def test_succeeded_when_last_zero(self):
        result = RunResult(attempts=self._make_attempts([1, 0]))
        assert result.succeeded is True

    def test_failed_when_last_nonzero(self):
        result = RunResult(attempts=self._make_attempts([1, 1, 1]))
        assert result.succeeded is False

    def test_total_attempts(self):
        result = RunResult(attempts=self._make_attempts([1, 1, 0]))
        assert result.total_attempts == 3


class TestRunner:
    def _make_runner(self, command=None, max_attempts=3, timeout=None):
        cfg = RunnerConfig(
            command=command or ["echo", "hello"],
            max_attempts=max_attempts,
            timeout=timeout,
        )
        backoff_cfg = BackoffConfig(base_delay=0.0, max_delay=0.0)
        return Runner(runner_config=cfg, backoff_config=backoff_cfg)

    def test_successful_command_on_first_try(self):
        runner = self._make_runner(command=["true"])
        result = runner.run()
        assert result.succeeded is True
        assert result.total_attempts == 1

    def test_failing_command_exhausts_attempts(self):
        runner = self._make_runner(command=["false"], max_attempts=3)
        result = runner.run()
        assert result.succeeded is False
        assert result.total_attempts == 3

    def test_retries_until_success(self):
        call_count = 0
        original_run = subprocess.run

        def fake_run(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            mock = MagicMock()
            mock.returncode = 0 if call_count >= 2 else 1
            mock.stdout = b""
            mock.stderr = b""
            return mock

        with patch("retryctl.runner.subprocess.run", side_effect=fake_run):
            runner = self._make_runner(command=["dummy"], max_attempts=5)
            result = runner.run()

        assert result.succeeded is True
        assert result.total_attempts == 2

    def test_timeout_recorded_in_attempt(self):
        def fake_run(*args, **kwargs):
            raise subprocess.TimeoutExpired(cmd="sleep", timeout=1)

        with patch("retryctl.runner.subprocess.run", side_effect=fake_run):
            runner = self._make_runner(command=["sleep", "99"], max_attempts=2, timeout=1)
            result = runner.run()

        assert result.succeeded is False
        assert result.total_attempts == 2
        for attempt in result.attempts:
            assert attempt.returncode == -1
