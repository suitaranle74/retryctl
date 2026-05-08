"""File-based configuration for retryctl."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import json
import os


@dataclass
class FileConfig:  # noqa: too-many-instance-attributes
    # backoff
    initial_delay: float = 1.0
    multiplier: float = 2.0
    max_delay: float = 60.0
    max_attempts: int = 5
    # alerts
    alert_enabled: bool = False
    alert_on_failure: bool = True
    alert_on_success: bool = False
    alert_shell_hook: Optional[str] = None
    # runner
    command: List[str] = field(default_factory=list)
    # condition
    retry_exit_codes: Optional[List[int]] = None
    retry_output_patterns: Optional[List[str]] = None
    # timeout
    attempt_timeout: Optional[float] = None
    total_timeout: Optional[float] = None
    # throttle
    throttle_enabled: bool = False
    throttle_threshold: int = 5
    throttle_window: float = 60.0
    throttle_pause: float = 10.0
    # jitter
    jitter_strategy: str = "none"
    jitter_max: float = 1.0
    # labels
    labels: Dict[str, str] = field(default_factory=dict)
    job_name: Optional[str] = None
    # budget
    budget_enabled: bool = False
    budget_max_retries: int = 10
    budget_window: float = 3600.0
    # deadletter
    deadletter_enabled: bool = False
    deadletter_path: Optional[str] = None
    # snapshot
    snapshot_enabled: bool = False
    snapshot_path: Optional[str] = None
    snapshot_max: int = 10
    # circuit breaker
    circuit_breaker_enabled: bool = False
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_recovery_timeout: float = 30.0
    # concurrency
    concurrency_max: Optional[int] = None
    # checkpoint
    checkpoint_enabled: bool = False
    checkpoint_path: Optional[str] = None
    # trace
    trace_enabled: bool = False
    trace_header_name: str = "X-Trace-ID"
    trace_propagate: bool = False
    # warmup
    warmup_enabled: bool = False
    warmup_attempts: int = 1
    warmup_delay: float = 0.0
    # policy
    policy_mode: str = "default"
    # audit
    audit_enabled: bool = False
    audit_output_file: Optional[str] = None
    # sampling
    sampling_enabled: bool = False
    sampling_rate: float = 1.0
    # quarantine
    quarantine_enabled: bool = False
    quarantine_failure_threshold: int = 3
    quarantine_duration: float = 300.0
    # escalation
    escalation_enabled: Optional[bool] = None
    escalation_threshold: Optional[int] = None
    escalation_cooldown: Optional[float] = None
    escalation_hooks: Optional[List[str]] = None

    @classmethod
    def from_dict(cls, data: dict) -> "FileConfig":
        known = cls.__dataclass_fields__.keys()
        filtered = {k: v for k, v in data.items() if k in known}
        return cls(**filtered)


def load_config(path: str) -> FileConfig:
    if not os.path.exists(path):
        return FileConfig()
    with open(path) as fh:
        data: Dict[str, Any] = json.load(fh)
    return FileConfig.from_dict(data)
