"""Bridge between FileConfig and TraceConfig."""
from retryctl.config import FileConfig
from retryctl.trace import TraceConfig


def trace_config_from_file(fc: FileConfig) -> TraceConfig:
    """Build a TraceConfig from a FileConfig instance."""
    data = {}
    if fc.trace_enabled is not None:
        data["enabled"] = fc.trace_enabled
    if fc.trace_header_name is not None:
        data["header_name"] = fc.trace_header_name
    if fc.trace_propagate_env is not None:
        data["propagate_env"] = fc.trace_propagate_env
    if fc.trace_env_var is not None:
        data["env_var"] = fc.trace_env_var
    return TraceConfig.from_dict(data)
