"""File-based configuration dataclass for retryctl."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import json
import os


@dataclass
class FileConfig:
    # Backoff
    initial_delay: Optional[float] = None
    max_delay: Optional[float] = None
    multiplier: Optional[float] = None
    max_attempts: Optional[int] = None
    # Alert
    alert_command: Optional[str] = None
    alert_on_failure: Optional[bool] = None
    # Runner
    command: Optional[List[str]] = None
    # Condition
    retry_exit_codes: Optional[List[int]] = None
    retry_output_patterns: Optional[List[str]] = None
    # Timeout
    attempt_timeout: Optional[float] = None
    total_timeout: Optional[float] = None
    # Throttle
    throttle_enabled: Optional[bool] = None
    throttle_threshold: Optional[int] = None
    throttle_window: Optional[float] = None
    # Jitter
    jitter_strategy: Optional[str] = None
    jitter_max: Optional[float] = None
    # Labels
    labels: Optional[Dict[str, str]] = None
    job_name: Optional[str] = None
    # Budget
    budget_enabled: Optional[bool] = None
    budget_max_retries: Optional[int] = None
    budget_window: Optional[float] = None
    # Dead letter
    deadletter_enabled: Optional[bool] = None
    deadletter_path: Optional[str] = None
    # Snapshot
    snapshot_enabled: Optional[bool] = None
    snapshot_path: Optional[str] = None
    # Circuit breaker
    circuit_breaker_enabled: Optional[bool] = None
    circuit_breaker_failure_threshold: Optional[int] = None
    circuit_breaker_recovery_timeout: Optional[float] = None
    # Concurrency
    max_concurrency: Optional[int] = None
    # Drain
    drain_enabled: Optional[bool] = None
    drain_signal: Optional[str] = None
    drain_timeout: Optional[float] = None
    # Checkpoint
    checkpoint_enabled: Optional[bool] = None
    checkpoint_path: Optional[str] = None
    # Trace
    trace_enabled: Optional[bool] = None
    trace_header_name: Optional[str] = None
    trace_id: Optional[str] = None
    # Warmup
    warmup_enabled: Optional[bool] = None
    warmup_attempts: Optional[int] = None
    warmup_delay: Optional[float] = None
    # Policy
    policy_name: Optional[str] = None
    # Audit
    audit_enabled: Optional[bool] = None
    audit_output_file: Optional[str] = None
    # Sampling
    sampling_enabled: Optional[bool] = None
    sampling_rate: Optional[float] = None
    # Profiles
    profiles: Optional[Dict[str, Any]] = None
    active_profile: Optional[str] = None
    # Quarantine
    quarantine_enabled: Optional[bool] = None
    quarantine_failure_threshold: Optional[int] = None
    quarantine_duration: Optional[float] = None
    quarantine_reset_on_success: Optional[bool] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FileConfig":
        allowed = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in allowed}
        return cls(**filtered)


def load_config(path: str) -> FileConfig:
    """Load a FileConfig from a JSON file. Returns defaults if file not found."""
    if not os.path.exists(path):
        return FileConfig()
    with open(path, "r") as fh:
        data = json.load(fh)
    return FileConfig.from_dict(data)
