"""Bridge between FileConfig and CircuitBreakerConfig."""
from retryctl.circuit_breaker import CircuitBreakerConfig
from retryctl.config import FileConfig


def circuit_breaker_config_from_file(fc: FileConfig) -> CircuitBreakerConfig:
    """Build a CircuitBreakerConfig from a FileConfig instance."""
    data: dict = {}
    if fc.circuit_breaker_enabled is not None:
        data["enabled"] = fc.circuit_breaker_enabled
    if fc.circuit_breaker_failure_threshold is not None:
        data["failure_threshold"] = fc.circuit_breaker_failure_threshold
    if fc.circuit_breaker_recovery_timeout is not None:
        data["recovery_timeout"] = fc.circuit_breaker_recovery_timeout
    if fc.circuit_breaker_success_threshold is not None:
        data["success_threshold"] = fc.circuit_breaker_success_threshold
    return CircuitBreakerConfig.from_dict(data)
