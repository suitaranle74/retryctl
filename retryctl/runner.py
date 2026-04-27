"""Command runner module for retryctl.

Handles subprocess execution, exit code inspection, and retry orchestration
using the backoff strategy defined in retryctl.backoff.
"""

from __future__ import annotations

import subprocess
import time
import logging
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Sequence

from retryctl.backoff import BackoffConfig, ExponentialBackoff

logger = logging.getLogger(__name__)


@dataclass
class RunnerConfig:
    """Configuration for the command runner."""

    # Command and arguments to execute
    command: Sequence[str]

    # Backoff / retry configuration
    backoff: BackoffConfig = field(default_factory=BackoffConfig)

    # Exit codes that are considered retriable (empty = retry on any non-zero)
    retriable_exit_codes: List[int] = field(default_factory=list)

    # Optional shell mode (use with caution)
    shell: bool = False

    # Optional environment variables to pass to the subprocess
    env: Optional[dict] = None

    # Timeout in seconds for each individual attempt (None = no timeout)
    timeout: Optional[float] = None


@dataclass
class AttemptResult:
    """Result of a single command attempt."""

    attempt: int
    returncode: int
    stdout: str
    stderr: str
    elapsed: float  # seconds

    @property
    def succeeded(self) -> bool:
        return self.returncode == 0


@dataclass
class RunResult:
    """Aggregated result of all attempts for a command run."""

    attempts: List[AttemptResult] = field(default_factory=list)
    succeeded: bool = False

    @property
    def last(self) -> Optional[AttemptResult]:
        return self.attempts[-1] if self.attempts else None

    @property
    def total_attempts(self) -> int:
        return len(self.attempts)


class CommandRunner:
    """Runs a CLI command with configurable retry / backoff logic."""

    def __init__(
        self,
        config: RunnerConfig,
        on_failure: Optional[Callable[[AttemptResult], None]] = None,
    ) -> None:
        """
        Args:
            config: Runner and backoff configuration.
            on_failure: Optional callback invoked after each failed attempt.
                        Useful for alerting hooks.
        """
        self.config = config
        self.on_failure = on_failure
        self._backoff = ExponentialBackoff(config.backoff)

    def _is_retriable(self, returncode: int) -> bool:
        """Determine whether an exit code warrants a retry."""
        if returncode == 0:
            return False
        codes = self.config.retriable_exit_codes
        return (not codes) or (returncode in codes)

    def _execute_once(self, attempt_number: int) -> AttemptResult:
        """Run the command once and return an AttemptResult."""
        start = time.monotonic()
        try:
            proc = subprocess.run(
                self.config.command,
                capture_output=True,
                text=True,
                shell=self.config.shell,
                env=self.config.env,
                timeout=self.config.timeout,
            )
            returncode = proc.returncode
            stdout = proc.stdout
            stderr = proc.stderr
        except subprocess.TimeoutExpired as exc:
            returncode = -1
            stdout = exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
            stderr = f"Command timed out after {self.config.timeout}s"
        except FileNotFoundError as exc:
            returncode = 127  # POSIX convention: command not found
            stdout = ""
            stderr = str(exc)

        elapsed = time.monotonic() - start
        return AttemptResult(
            attempt=attempt_number,
            returncode=returncode,
            stdout=stdout,
            stderr=stderr,
            elapsed=elapsed,
        )

    def run(self) -> RunResult:
        """Execute the command with retry/backoff logic.

        Returns:
            A RunResult containing all attempt results and overall success flag.
        """
        result = RunResult()
        self._backoff.reset()

        while True:
            attempt_number = result.total_attempts + 1
            logger.info("Attempt %d: running %s", attempt_number, list(self.config.command))

            attempt = self._execute_once(attempt_number)
            result.attempts.append(attempt)

            if attempt.succeeded:
                result.succeeded = True
                logger.info("Attempt %d succeeded (exit 0) in %.2fs", attempt_number, attempt.elapsed)
                break

            logger.warning(
                "Attempt %d failed (exit %d) in %.2fs: %s",
                attempt_number,
                attempt.returncode,
                attempt.elapsed,
                attempt.stderr.strip(),
            )

            if self.on_failure:
                try:
                    self.on_failure(attempt)
                except Exception:  # noqa: BLE001
                    logger.exception("on_failure hook raised an exception")

            if not self._is_retriable(attempt.returncode):
                logger.error("Exit code %d is not retriable; giving up.", attempt.returncode)
                break

            delay = self._backoff.attempt()
            if delay is None:
                logger.error("Maximum retries reached; giving up.")
                break

            logger.info("Waiting %.2fs before next attempt...", delay)
            time.sleep(delay)

        return result
