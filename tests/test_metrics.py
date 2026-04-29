"""Tests for retryctl.metrics."""
import time
import pytest

from retryctl.metrics import AttemptMetric, MetricsConfig, RunMetrics


class TestMetricsConfig:
    def test_defaults(self):
        cfg = MetricsConfig()
        assert cfg.enabled is True
        assert cfg.include_durations is True
        assert cfg.include_exit_codes is True

    def test_from_dict_partial(self):
        cfg = MetricsConfig.from_dict({"enabled": False})
        assert cfg.enabled is False
        assert cfg.include_durations is True

    def test_from_dict_full(self):
        cfg = MetricsConfig.from_dict(
            {"enabled": True, "include_durations": False, "include_exit_codes": False}
        )
        assert cfg.include_durations is False
        assert cfg.include_exit_codes is False


class TestAttemptMetric:
    def test_succeeded_on_zero(self):
        m = AttemptMetric(attempt_number=1, exit_code=0, duration_seconds=0.1, succeeded=True)
        assert m.succeeded
        assert not m.failed

    def test_failed_on_nonzero(self):
        m = AttemptMetric(attempt_number=1, exit_code=1, duration_seconds=0.2, succeeded=False)
        assert m.failed
        assert not m.succeeded


class TestRunMetrics:
    def _make(self, command: str = "echo hi") -> RunMetrics:
        return RunMetrics(command=command)

    def test_initial_state(self):
        rm = self._make()
        assert rm.total_attempts == 0
        assert not rm.succeeded

    def test_record_attempt_success(self):
        rm = self._make()
        rm.record_attempt(1, 0, 0.5)
        assert rm.total_attempts == 1
        assert rm.succeeded

    def test_record_multiple_attempts(self):
        rm = self._make()
        rm.record_attempt(1, 1, 0.1)
        rm.record_attempt(2, 1, 0.2)
        rm.record_attempt(3, 0, 0.3)
        assert rm.total_attempts == 3
        assert rm.succeeded

    def test_finish_sets_finished_at(self):
        rm = self._make()
        assert rm.finished_at is None
        rm.finish()
        assert rm.finished_at is not None

    def test_total_duration_after_finish(self):
        rm = self._make()
        time.sleep(0.05)
        rm.finish()
        assert rm.total_duration >= 0.0

    def test_summary_includes_all_fields(self):
        rm = self._make(command="ls")
        rm.record_attempt(1, 0, 1.0)
        rm.finish()
        cfg = MetricsConfig()
        s = rm.summary(cfg)
        assert s["command"] == "ls"
        assert s["total_attempts"] == 1
        assert s["succeeded"] is True
        assert "total_duration_seconds" in s
        assert s["attempt_durations"] == [1.0]
        assert s["attempt_exit_codes"] == [0]

    def test_summary_respects_config_flags(self):
        rm = self._make()
        rm.record_attempt(1, 0, 0.5)
        rm.finish()
        cfg = MetricsConfig(include_durations=False, include_exit_codes=False)
        s = rm.summary(cfg)
        assert "attempt_durations" not in s
        assert "attempt_exit_codes" not in s
