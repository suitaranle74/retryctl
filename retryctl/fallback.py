"""Fallback command support: run an alternative command when all retries are exhausted."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class FallbackConfig:
    """Configuration for the fallback command feature."""

    enabled: bool = False
    command: List[str] = field(default_factory=list)
    capture_output: bool = True

    @classmethod
    def from_dict(cls, data: dict) -> "FallbackConfig":
        known = {"enabled", "command", "capture_output"}
        filtered = {k: v for k, v in data.items() if k in known}
        raw_cmd = filtered.get("command", [])
        if isinstance(raw_cmd, str):
            raw_cmd = raw_cmd.split()
        filtered["command"] = raw_cmd
        return cls(**filtered)


@dataclass
class FallbackResult:
    """Result produced by running the fallback command."""

    exit_code: int
    stdout: str = ""
    stderr: str = ""

    @property
    def succeeded(self) -> bool:
        return self.exit_code == 0


class FallbackRunner:
    """Runs the configured fallback command when primary retries are exhausted."""

    def __init__(self, config: FallbackConfig) -> None:
        self._config = config

    def should_run(self) -> bool:
        return self._config.enabled and bool(self._config.command)

    def run(self) -> Optional[FallbackResult]:
        """Execute the fallback command and return its result, or None if disabled."""
        if not self.should_run():
            return None

        import subprocess  # noqa: PLC0415

        try:
            proc = subprocess.run(
                self._config.command,
                capture_output=self._config.capture_output,
                text=True,
            )
            return FallbackResult(
                exit_code=proc.returncode,
                stdout=proc.stdout or "",
                stderr=proc.stderr or "",
            )
        except FileNotFoundError as exc:
            return FallbackResult(exit_code=127, stderr=str(exc))
