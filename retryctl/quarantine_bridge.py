"""Bridge: builds QuarantineConfig from FileConfig."""
from retryctl.config import FileConfig
from retryctl.quarantine import QuarantineConfig


def quarantine_config_from_file(fc: FileConfig) -> QuarantineConfig:
    """Construct a QuarantineConfig from a FileConfig instance."""
    data: dict = {}

    if fc.quarantine_enabled is not None:
        data["enabled"] = fc.quarantine_enabled
    if fc.quarantine_failure_threshold is not None:
        data["failure_threshold"] = fc.quarantine_failure_threshold
    if fc.quarantine_duration is not None:
        data["quarantine_duration"] = fc.quarantine_duration
    if fc.quarantine_reset_on_success is not None:
        data["reset_on_success"] = fc.quarantine_reset_on_success

    return QuarantineConfig.from_dict(data)
