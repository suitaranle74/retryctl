"""Bridge between FileConfig and PolicyConfig."""
from retryctl.policy import PolicyConfig
from retryctl.config_bridge import (
    backoff_config_from_file,
    runner_config_from_file,
)
from retryctl.condition_bridge import condition_config_from_file
from retryctl.budget_bridge import budget_config_from_file
from retryctl.circuit_breaker_bridge import circuit_breaker_config_from_file


def policy_config_from_file(file_cfg) -> PolicyConfig:
    """Build a PolicyConfig from a FileConfig instance."""
    return PolicyConfig(
        backoff=backoff_config_from_file(file_cfg),
        condition=condition_config_from_file(file_cfg),
        budget=budget_config_from_file(file_cfg),
        circuit_breaker=circuit_breaker_config_from_file(file_cfg),
    )
