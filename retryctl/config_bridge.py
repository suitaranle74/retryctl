"""Bridge between FileConfig and the runner/alert/backoff dataclasses."""

from __future__ import annotations

from typing import List

from retryctl.backoff import BackoffConfig
from retryctl.alerts import AlertConfig
from retryctl.config import FileConfig
from retryctl.runner import RunnerConfig


def backoff_config_from_file(fc: FileConfig) -> BackoffConfig:
    """Build a BackoffConfig from a FileConfig."""
    return BackoffConfig(
        initial_delay=fc.initial_delay,
        multiplier=fc.multiplier,
        max_delay=fc.max_delay,
        jitter=fc.jitter,
    )


def alert_config_from_file(fc: FileConfig) -> AlertConfig:
    """Build an AlertConfig from a FileConfig."""
    return AlertConfig(
        on_failure=fc.alert_on_failure,
        on_success=fc.alert_on_success,
        shell_hook=fc.shell_hook,
    )


def runner_config_from_file(
    fc: FileConfig,
    command: List[str],
    *,
    use_shell: bool = False,
) -> RunnerConfig:
    """Build a complete RunnerConfig from a FileConfig and a command.

    Args:
        fc: Populated FileConfig (from a YAML/JSON config file).
        command: The CLI command tokens to execute.
        use_shell: Whether to run the command through the shell.

    Returns:
        A RunnerConfig ready to pass to Runner.
    """
    return RunnerConfig(
        command=command,
        max_attempts=fc.max_attempts,
        backoff=backoff_config_from_file(fc),
        alert=alert_config_from_file(fc),
        env=fc.env if fc.env else None,
        use_shell=use_shell,
    )
