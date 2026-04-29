"""Bridge between FileConfig and ConditionConfig."""
from __future__ import annotations

from retryctl.condition import ConditionConfig
from retryctl.config import FileConfig


def condition_config_from_file(fc: FileConfig) -> ConditionConfig:
    """Build a ConditionConfig from a FileConfig instance."""
    return ConditionConfig(
        retry_on_exit_codes=list(fc.retry_on_exit_codes),
        no_retry_on_exit_codes=list(fc.no_retry_on_exit_codes),
        retry_on_output_pattern=fc.retry_on_output_pattern,
        no_retry_on_output_pattern=fc.no_retry_on_output_pattern,
    )
