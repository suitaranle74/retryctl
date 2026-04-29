"""Retry condition evaluation — decide whether a failed attempt should be retried."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ConditionConfig:
    """Configuration for retry conditions."""
    retry_on_exit_codes: List[int] = field(default_factory=list)   # empty = retry on any non-zero
    no_retry_on_exit_codes: List[int] = field(default_factory=list)
    retry_on_output_pattern: Optional[str] = None   # regex matched against combined output
    no_retry_on_output_pattern: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "ConditionConfig":
        known = {
            "retry_on_exit_codes",
            "no_retry_on_exit_codes",
            "retry_on_output_pattern",
            "no_retry_on_output_pattern",
        }
        filtered = {k: v for k, v in data.items() if k in known}
        return cls(**filtered)


class ConditionEvaluator:
    """Evaluates whether an attempt result warrants a retry."""

    def __init__(self, config: ConditionConfig) -> None:
        self._config = config
        self._retry_pat = (
            re.compile(config.retry_on_output_pattern)
            if config.retry_on_output_pattern
            else None
        )
        self._no_retry_pat = (
            re.compile(config.no_retry_on_output_pattern)
            if config.no_retry_on_output_pattern
            else None
        )

    def should_retry(self, exit_code: int, output: str = "") -> bool:
        """Return True if the attempt should be retried."""
        # A successful exit is never retried.
        if exit_code == 0:
            return False

        cfg = self._config

        # Hard no-retry exit codes take priority.
        if cfg.no_retry_on_exit_codes and exit_code in cfg.no_retry_on_exit_codes:
            return False

        # Hard no-retry output pattern takes priority.
        if self._no_retry_pat and self._no_retry_pat.search(output):
            return False

        # If an allow-list of exit codes is specified, honour it.
        if cfg.retry_on_exit_codes and exit_code not in cfg.retry_on_exit_codes:
            return False

        # If an output pattern is required, the output must match.
        if self._retry_pat and not self._retry_pat.search(output):
            return False

        return True
