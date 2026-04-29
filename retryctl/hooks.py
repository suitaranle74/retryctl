"""Pre/post attempt hook execution for retryctl."""
from __future__ import annotations

import subprocess
import shlex
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class HooksConfig:
    """Configuration for pre/post attempt shell hooks."""
    pre_attempt: Optional[str] = None
    post_attempt: Optional[str] = None
    on_success: Optional[str] = None
    on_failure: Optional[str] = None
    timeout: float = 10.0

    @classmethod
    def from_dict(cls, data: dict) -> "HooksConfig":
        known = {"pre_attempt", "post_attempt", "on_success", "on_failure", "timeout"}
        filtered = {k: v for k, v in data.items() if k in known}
        return cls(**filtered)


@dataclass
class HookContext:
    """Context passed as environment variables to hook scripts."""
    attempt_number: int
    exit_code: Optional[int] = None
    command: str = ""

    def to_env(self) -> dict:
        env = {
            "RETRYCTL_ATTEMPT": str(self.attempt_number),
            "RETRYCTL_COMMAND": self.command,
        }
        if self.exit_code is not None:
            env["RETRYCTL_EXIT_CODE"] = str(self.exit_code)
        return env


class HookRunner:
    """Executes configured shell hooks at retry lifecycle points."""

    def __init__(self, config: HooksConfig) -> None:
        self.config = config

    def run_pre_attempt(self, ctx: HookContext) -> bool:
        return self._run(self.config.pre_attempt, ctx)

    def run_post_attempt(self, ctx: HookContext) -> bool:
        return self._run(self.config.post_attempt, ctx)

    def run_on_success(self, ctx: HookContext) -> bool:
        return self._run(self.config.on_success, ctx)

    def run_on_failure(self, ctx: HookContext) -> bool:
        return self._run(self.config.on_failure, ctx)

    def _run(self, hook: Optional[str], ctx: HookContext) -> bool:
        """Run a shell hook. Returns True on success, False on error/skip."""
        if not hook:
            return True
        import os
        env = {**os.environ, **ctx.to_env()}
        try:
            result = subprocess.run(
                shlex.split(hook),
                env=env,
                timeout=self.config.timeout,
                capture_output=True,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return False
