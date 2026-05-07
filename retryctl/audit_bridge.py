"""Bridge between FileConfig and AuditConfig."""

from __future__ import annotations

from retryctl.audit import AuditConfig
from retryctl.config import FileConfig


def audit_config_from_file(fc: FileConfig) -> AuditConfig:
    """Construct an AuditConfig from a FileConfig instance."""
    data = {}
    if fc.audit_enabled is not None:
        data["enabled"] = fc.audit_enabled
    if fc.audit_output_file is not None:
        data["output_file"] = fc.audit_output_file
    if fc.audit_include_output is not None:
        data["include_output"] = fc.audit_include_output
    if fc.audit_include_env is not None:
        data["include_env"] = fc.audit_include_env
    return AuditConfig.from_dict(data)
