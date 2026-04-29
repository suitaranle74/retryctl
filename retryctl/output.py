"""Capture and format command output for retryctl."""
from __future__ import annotations

import textwrap
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class OutputConfig:
    """Configuration for output capturing and formatting."""
    max_lines: int = 50
    max_line_length: int = 200
    include_stderr: bool = True
    prefix: str = "  "


@dataclass
class CapturedOutput:
    """Holds stdout/stderr captured from a single command attempt."""
    stdout: str = ""
    stderr: str = ""
    attempt: int = 1

    def combined(self, include_stderr: bool = True) -> str:
        """Return stdout and optionally stderr as a single string."""
        parts = [self.stdout]
        if include_stderr and self.stderr:
            parts.append(self.stderr)
        return "\n".join(p for p in parts if p)

    def is_empty(self) -> bool:
        return not self.stdout and not self.stderr


class OutputFormatter:
    """Formats captured output according to OutputConfig."""

    def __init__(self, config: Optional[OutputConfig] = None) -> None:
        self.config = config or OutputConfig()

    def format(self, captured: CapturedOutput) -> str:
        """Return a human-readable, truncated representation of captured output."""
        if captured.is_empty():
            return f"[attempt {captured.attempt}] (no output)"

        raw = captured.combined(include_stderr=self.config.include_stderr)
        lines = raw.splitlines()

        truncated = False
        if len(lines) > self.config.max_lines:
            lines = lines[: self.config.max_lines]
            truncated = True

        trimmed: List[str] = []
        for line in lines:
            if len(line) > self.config.max_line_length:
                line = line[: self.config.max_line_length] + " ..."
            trimmed.append(self.config.prefix + line)

        header = f"[attempt {captured.attempt}] output:"
        body = "\n".join(trimmed)
        footer = f"{self.config.prefix}... (truncated)" if truncated else ""
        return "\n".join(part for part in [header, body, footer] if part)
