"""Tests for retryctl.condition_bridge."""
from retryctl.config import FileConfig
from retryctl.condition import ConditionConfig
from retryctl.condition_bridge import condition_config_from_file


class TestConditionConfigFromFile:
    def _make(self, **kwargs) -> FileConfig:
        return FileConfig(**kwargs)

    def test_defaults_produce_valid_condition_config(self):
        fc = self._make()
        cc = condition_config_from_file(fc)
        assert isinstance(cc, ConditionConfig)
        assert cc.retry_on_exit_codes == []
        assert cc.no_retry_on_exit_codes == []
        assert cc.retry_on_output_pattern is None
        assert cc.no_retry_on_output_pattern is None

    def test_exit_codes_forwarded(self):
        fc = self._make(retry_on_exit_codes=[1, 2], no_retry_on_exit_codes=[3])
        cc = condition_config_from_file(fc)
        assert cc.retry_on_exit_codes == [1, 2]
        assert cc.no_retry_on_exit_codes == [3]

    def test_output_patterns_forwarded(self):
        fc = self._make(
            retry_on_output_pattern="timeout",
            no_retry_on_output_pattern="fatal",
        )
        cc = condition_config_from_file(fc)
        assert cc.retry_on_output_pattern == "timeout"
        assert cc.no_retry_on_output_pattern == "fatal"

    def test_returns_independent_list_copy(self):
        original = [1, 2, 3]
        fc = self._make(retry_on_exit_codes=original)
        cc = condition_config_from_file(fc)
        original.append(99)
        assert 99 not in cc.retry_on_exit_codes
