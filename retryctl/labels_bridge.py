"""Bridge between FileConfig and LabelsConfig."""
from retryctl.labels import LabelsConfig
from retryctl.config import FileConfig


def labels_config_from_file(fc: FileConfig) -> LabelsConfig:
    """Construct a LabelsConfig from a FileConfig instance."""
    data: dict = {}

    if fc.label_static is not None:
        data["static"] = fc.label_static
    if fc.label_include_attempt_number is not None:
        data["include_attempt_number"] = fc.label_include_attempt_number
    if fc.label_include_command_hash is not None:
        data["include_command_hash"] = fc.label_include_command_hash
    if fc.label_prefix is not None:
        data["prefix"] = fc.label_prefix

    return LabelsConfig.from_dict(data)
