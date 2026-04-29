"""Tests for retryctl.output module."""
import pytest
from retryctl.output import CapturedOutput, OutputConfig, OutputFormatter


class TestOutputConfig:
    def test_defaults(self):
        cfg = OutputConfig()
        assert cfg.max_lines == 50
        assert cfg.max_line_length == 200
        assert cfg.include_stderr is True
        assert cfg.prefix == "  "

    def test_custom_values(self):
        cfg = OutputConfig(max_lines=10, max_line_length=80, include_stderr=False, prefix="> ")
        assert cfg.max_lines == 10
        assert cfg.max_line_length == 80
        assert cfg.include_stderr is False
        assert cfg.prefix == "> "


class TestCapturedOutput:
    def test_combined_with_stderr(self):
        c = CapturedOutput(stdout="out", stderr="err")
        assert c.combined(include_stderr=True) == "out\nerr"

    def test_combined_without_stderr(self):
        c = CapturedOutput(stdout="out", stderr="err")
        assert c.combined(include_stderr=False) == "out"

    def test_combined_empty_stderr_omitted(self):
        c = CapturedOutput(stdout="out", stderr="")
        assert c.combined() == "out"

    def test_is_empty_true(self):
        assert CapturedOutput().is_empty() is True

    def test_is_empty_false(self):
        assert CapturedOutput(stdout="x").is_empty() is False


class TestOutputFormatter:
    def _make(self, **kwargs) -> OutputFormatter:
        return OutputFormatter(OutputConfig(**kwargs))

    def test_empty_output_message(self):
        fmt = self._make()
        result = fmt.format(CapturedOutput(attempt=2))
        assert result == "[attempt 2] (no output)"

    def test_header_contains_attempt(self):
        fmt = self._make()
        result = fmt.format(CapturedOutput(stdout="hello", attempt=3))
        assert result.startswith("[attempt 3] output:")

    def test_prefix_applied(self):
        fmt = self._make(prefix=">> ")
        result = fmt.format(CapturedOutput(stdout="line"))
        assert ">> line" in result

    def test_line_truncation(self):
        fmt = self._make(max_line_length=5)
        result = fmt.format(CapturedOutput(stdout="toolongline"))
        assert "toolo ..." in result

    def test_max_lines_truncation(self):
        many_lines = "\n".join(str(i) for i in range(100))
        fmt = self._make(max_lines=10)
        result = fmt.format(CapturedOutput(stdout=many_lines))
        assert "(truncated)" in result

    def test_no_truncation_footer_when_within_limit(self):
        fmt = self._make(max_lines=50)
        result = fmt.format(CapturedOutput(stdout="only one line"))
        assert "(truncated)" not in result

    def test_stderr_excluded_when_configured(self):
        fmt = self._make(include_stderr=False)
        result = fmt.format(CapturedOutput(stdout="out", stderr="err"))
        assert "err" not in result
