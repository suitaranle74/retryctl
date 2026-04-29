"""Tests for retryctl.hooks module."""
import sys
import pytest
from retryctl.hooks import HooksConfig, HookContext, HookRunner


class TestHooksConfig:
    def test_defaults(self):
        cfg = HooksConfig()
        assert cfg.pre_attempt is None
        assert cfg.post_attempt is None
        assert cfg.on_success is None
        assert cfg.on_failure is None
        assert cfg.timeout == 10.0

    def test_custom_values(self):
        cfg = HooksConfig(pre_attempt="echo pre", on_success="echo ok", timeout=5.0)
        assert cfg.pre_attempt == "echo pre"
        assert cfg.on_success == "echo ok"
        assert cfg.timeout == 5.0

    def test_from_dict_full(self):
        cfg = HooksConfig.from_dict({
            "pre_attempt": "echo pre",
            "post_attempt": "echo post",
            "on_success": "echo success",
            "on_failure": "echo fail",
            "timeout": 3.0,
        })
        assert cfg.pre_attempt == "echo pre"
        assert cfg.timeout == 3.0

    def test_from_dict_ignores_unknown_keys(self):
        cfg = HooksConfig.from_dict({"pre_attempt": "echo x", "unknown_key": "ignored"})
        assert cfg.pre_attempt == "echo x"


class TestHookContext:
    def test_to_env_without_exit_code(self):
        ctx = HookContext(attempt_number=1, command="ls -la")
        env = ctx.to_env()
        assert env["RETRYCTL_ATTEMPT"] == "1"
        assert env["RETRYCTL_COMMAND"] == "ls -la"
        assert "RETRYCTL_EXIT_CODE" not in env

    def test_to_env_with_exit_code(self):
        ctx = HookContext(attempt_number=2, exit_code=1, command="false")
        env = ctx.to_env()
        assert env["RETRYCTL_EXIT_CODE"] == "1"
        assert env["RETRYCTL_ATTEMPT"] == "2"


class TestHookRunner:
    def _make(self, **kwargs) -> HookRunner:
        return HookRunner(HooksConfig(**kwargs))

    def _ctx(self, attempt=1, exit_code=None, command="echo test"):
        return HookContext(attempt_number=attempt, exit_code=exit_code, command=command)

    def test_run_pre_attempt_no_hook_returns_true(self):
        runner = self._make()
        assert runner.run_pre_attempt(self._ctx()) is True

    def test_run_on_success_no_hook_returns_true(self):
        runner = self._make()
        assert runner.run_on_success(self._ctx()) is True

    @pytest.mark.skipif(sys.platform == "win32", reason="POSIX only")
    def test_run_succeeding_hook(self):
        runner = self._make(pre_attempt="true")
        assert runner.run_pre_attempt(self._ctx()) is True

    @pytest.mark.skipif(sys.platform == "win32", reason="POSIX only")
    def test_run_failing_hook(self):
        runner = self._make(on_failure="false")
        assert runner.run_on_failure(self._ctx(exit_code=1)) is False

    def test_run_nonexistent_command_returns_false(self):
        runner = self._make(post_attempt="__no_such_binary_xyz__")
        assert runner.run_post_attempt(self._ctx()) is False

    @pytest.mark.skipif(sys.platform == "win32", reason="POSIX only")
    def test_hook_receives_env_variables(self, tmp_path):
        out_file = tmp_path / "attempt.txt"
        hook = f"sh -c 'echo $RETRYCTL_ATTEMPT > {out_file}'"
        runner = self._make(pre_attempt=hook)
        runner.run_pre_attempt(self._ctx(attempt=3))
        assert out_file.read_text().strip() == "3"
