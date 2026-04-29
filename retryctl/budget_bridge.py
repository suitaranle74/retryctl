"""Bridge between FileConfig and BudgetConfig."""

from retryctl.budget import BudgetConfig
from retryctl.config import FileConfig


def budget_config_from_file(file_config: FileConfig) -> BudgetConfig:
    """Construct a BudgetConfig from a FileConfig instance."""
    return BudgetConfig(
        enabled=file_config.budget_enabled,
        max_retries_per_window=file_config.budget_max_retries_per_window,
        window_seconds=file_config.budget_window_seconds,
    )
