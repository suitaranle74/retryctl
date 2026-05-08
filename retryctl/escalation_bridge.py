"""Bridge between FileConfig and EscalationConfig."""
from __future__ import annotations

from retryctl.config import FileConfig
from retryctl.escalation import EscalationConfig


def escalation_config_from_file(fc: FileConfig) -> EscalationConfig:
    """Build an EscalationConfig from a parsed FileConfig."""
    data: dict = {}
    if fc.escalation_enabled is not None:
        data["enabled"] = fc.escalation_enabled
    if fc.escalation_threshold is not None:
        data["threshold"] = fc.escalation_threshold
    if fc.escalation_cooldown is not None:
        data["cooldown"] = fc.escalation_cooldown
    if fc.escalation_hooks is not None:
        data["hooks"] = fc.escalation_hooks
    return EscalationConfig.from_dict(data)
