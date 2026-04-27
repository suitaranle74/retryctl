"""Alerting hooks for retryctl — notify on failure or exhausted retries."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from typing import Callable, List, Optional


@dataclass
class AlertConfig:
    """Configuration for alerting hooks."""

    # Shell command to run on final failure; {cmd}, {attempts}, {exit_code} are interpolated
    on_failure_cmd: Optional[str] = None

    # Python callables invoked with (command, attempts, exit_code)
    on_failure_hooks: List[Callable[[str, int, int], None]] = field(default_factory=list)

    # If True, alert after every failed attempt, not just the last
    alert_every_attempt: bool = False


class AlertManager:
    """Dispatches alerts based on AlertConfig."""

    def __init__(self, config: AlertConfig) -> None:
        self.config = config

    def notify(self, command: str, attempts: int, exit_code: int) -> None:
        """Fire all configured alert hooks."""
        self._run_shell_hook(command, attempts, exit_code)
        self._run_python_hooks(command, attempts, exit_code)

    def _run_shell_hook(self, command: str, attempts: int, exit_code: int) -> None:
        if not self.config.on_failure_cmd:
            return
        rendered = self.config.on_failure_cmd.format(
            cmd=command,
            attempts=attempts,
            exit_code=exit_code,
        )
        try:
            subprocess.run(rendered, shell=True, check=False)  # noqa: S602
        except OSError:
            pass

    def _run_python_hooks(
        self, command: str, attempts: int, exit_code: int
    ) -> None:
        for hook in self.config.on_failure_hooks:
            try:
                hook(command, attempts, exit_code)
            except Exception:  # noqa: BLE001
                pass
