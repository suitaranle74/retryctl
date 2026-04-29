"""Tests for retryctl.condition."""
import pytest
from retryctl.condition import ConditionConfig, ConditionEvaluator


class TestConditionConfig:
    def test_defaults(self):
        cfg = ConditionConfig()
        assert cfg.retry_on_exit_codes == []
        assert cfg.no_retry_on_exit_codes == []
        assert cfg.retry_on_output_pattern is None
        assert cfg.no_retry_on_output_pattern is None

    def test_from_dict_full(self):
        cfg = ConditionConfig.from_dict({
            "retry_on_exit_codes": [1, 2],
            "no_retry_on_exit_codes": [3],
            "retry_on_output_pattern": "timeout",
            "no_retry_on_output_pattern": "fatal",
        })
        assert cfg.retry_on_exit_codes == [1, 2]
        assert cfg.no_retry_on_exit_codes == [3]
        assert cfg.retry_on_output_pattern == "timeout"
        assert cfg.no_retry_on_output_pattern == "fatal"

    def test_from_dict_ignores_unknown_keys(self):
        cfg = ConditionConfig.from_dict({"unknown_key": "value", "retry_on_exit_codes": [1]})
        assert cfg.retry_on_exit_codes == [1]


class TestConditionEvaluator:
    def _make(self, **kwargs) -> ConditionEvaluator:
        return ConditionEvaluator(ConditionConfig(**kwargs))

    def test_success_never_retried(self):
        ev = self._make()
        assert ev.should_retry(0) is False

    def test_any_nonzero_retried_by_default(self):
        ev = self._make()
        assert ev.should_retry(1) is True
        assert ev.should_retry(127) is True

    def test_no_retry_on_exit_code(self):
        ev = self._make(no_retry_on_exit_codes=[1])
        assert ev.should_retry(1) is False
        assert ev.should_retry(2) is True

    def test_retry_only_on_specified_exit_codes(self):
        ev = self._make(retry_on_exit_codes=[2, 3])
        assert ev.should_retry(1) is False
        assert ev.should_retry(2) is True
        assert ev.should_retry(3) is True

    def test_retry_on_output_pattern_match(self):
        ev = self._make(retry_on_output_pattern="timeout")
        assert ev.should_retry(1, output="connection timeout") is True
        assert ev.should_retry(1, output="permission denied") is False

    def test_no_retry_on_output_pattern_match(self):
        ev = self._make(no_retry_on_output_pattern="fatal")
        assert ev.should_retry(1, output="fatal error") is False
        assert ev.should_retry(1, output="transient error") is True

    def test_no_retry_pattern_takes_priority_over_retry_pattern(self):
        ev = self._make(
            retry_on_output_pattern="error",
            no_retry_on_output_pattern="fatal error",
        )
        assert ev.should_retry(1, output="fatal error") is False

    def test_no_retry_exit_code_takes_priority_over_retry_exit_code(self):
        ev = self._make(retry_on_exit_codes=[1], no_retry_on_exit_codes=[1])
        assert ev.should_retry(1) is False
