"""Tests for retryctl.metrics_reporter."""
import io
import json
from pathlib import Path

import pytest

from retryctl.metrics import MetricsConfig, RunMetrics
from retryctl.metrics_reporter import MetricsReporter


class TestMetricsReporter:
    def _make_metrics(self, exit_code: int = 0) -> RunMetrics:
        rm = RunMetrics(command="echo test")
        rm.record_attempt(1, exit_code, 0.25)
        rm.finish()
        return rm

    def test_report_writes_to_stream(self):
        stream = io.StringIO()
        reporter = MetricsReporter(config=MetricsConfig(), stream=stream)
        reporter.report(self._make_metrics())
        output = stream.getvalue()
        data = json.loads(output)
        assert data["command"] == "echo test"
        assert data["succeeded"] is True

    def test_report_disabled_produces_no_output(self):
        stream = io.StringIO()
        cfg = MetricsConfig(enabled=False)
        reporter = MetricsReporter(config=cfg, stream=stream)
        reporter.report(self._make_metrics())
        assert stream.getvalue() == ""

    def test_report_writes_to_file(self, tmp_path: Path):
        out_file = tmp_path / "metrics" / "run.json"
        reporter = MetricsReporter(config=MetricsConfig(), output_path=out_file)
        reporter.report(self._make_metrics(exit_code=1))
        assert out_file.exists()
        data = json.loads(out_file.read_text())
        assert data["succeeded"] is False
        assert data["attempt_exit_codes"] == [1]

    def test_report_creates_parent_dirs(self, tmp_path: Path):
        deep = tmp_path / "a" / "b" / "c" / "metrics.json"
        reporter = MetricsReporter(config=MetricsConfig(), output_path=deep)
        reporter.report(self._make_metrics())
        assert deep.exists()

    def test_report_failure_summary(self):
        stream = io.StringIO()
        reporter = MetricsReporter(config=MetricsConfig(), stream=stream)
        rm = RunMetrics(command="false")
        rm.record_attempt(1, 2, 0.1)
        rm.record_attempt(2, 2, 0.2)
        rm.finish()
        reporter.report(rm)
        data = json.loads(stream.getvalue())
        assert data["total_attempts"] == 2
        assert data["succeeded"] is False
        assert data["attempt_exit_codes"] == [2, 2]
