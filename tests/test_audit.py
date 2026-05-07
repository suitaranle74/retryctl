"""Tests for retryctl.audit."""

from __future__ import annotations

import io
import json
import pytest

from retryctl.audit import AuditConfig, AuditEvent, AuditLogger


class TestAuditConfig:
    def test_defaults(self):
        cfg = AuditConfig()
        assert cfg.enabled is False
        assert cfg.output_file is None
        assert cfg.include_output is False
        assert cfg.include_env is False

    def test_from_dict_full(self):
        cfg = AuditConfig.from_dict(
            {"enabled": True, "output_file": "/tmp/audit.log",
             "include_output": True, "include_env": True}
        )
        assert cfg.enabled is True
        assert cfg.output_file == "/tmp/audit.log"
        assert cfg.include_output is True
        assert cfg.include_env is True

    def test_from_dict_partial(self):
        cfg = AuditConfig.from_dict({"enabled": True})
        assert cfg.enabled is True
        assert cfg.output_file is None

    def test_from_dict_empty(self):
        cfg = AuditConfig.from_dict({})
        assert cfg.enabled is False


class TestAuditEvent:
    def _make(self, **kwargs):
        defaults = dict(event="attempt", command="echo hi", attempt=1)
        defaults.update(kwargs)
        return AuditEvent(**defaults)

    def test_to_json_round_trip(self):
        ev = self._make(exit_code=0, elapsed=0.5)
        raw = ev.to_json()
        data = json.loads(raw)
        assert data["event"] == "attempt"
        assert data["exit_code"] == 0

    def test_from_json_round_trip(self):
        ev = self._make(exit_code=1)
        ev2 = AuditEvent.from_json(ev.to_json())
        assert ev2.command == ev.command
        assert ev2.exit_code == 1

    def test_timestamp_auto_set(self):
        ev = self._make()
        assert ev.timestamp > 0


class TestAuditLogger:
    def _make(self, **kwargs):
        cfg = AuditConfig(enabled=True, **kwargs)
        stream = io.StringIO()
        return AuditLogger(cfg, stream=stream), stream

    def test_disabled_produces_no_output(self):
        cfg = AuditConfig(enabled=False)
        stream = io.StringIO()
        logger = AuditLogger(cfg, stream=stream)
        logger.log(AuditEvent(event="attempt", command="ls", attempt=1))
        assert stream.getvalue() == ""

    def test_enabled_writes_json_line(self):
        logger, stream = self._make()
        logger.log(AuditEvent(event="attempt", command="ls", attempt=1, exit_code=0))
        line = stream.getvalue().strip()
        data = json.loads(line)
        assert data["event"] == "attempt"
        assert data["exit_code"] == 0

    def test_include_output_false_strips_stdout(self):
        logger, stream = self._make(include_output=False)
        logger.log(AuditEvent(event="attempt", command="ls", attempt=1,
                              stdout="hello", stderr="err"))
        data = json.loads(stream.getvalue().strip())
        assert data["stdout"] is None
        assert data["stderr"] is None

    def test_include_output_true_preserves_stdout(self):
        logger, stream = self._make(include_output=True)
        logger.log(AuditEvent(event="attempt", command="ls", attempt=1, stdout="hello"))
        data = json.loads(stream.getvalue().strip())
        assert data["stdout"] == "hello"

    def test_context_manager_closes(self):
        logger, _ = self._make()
        with logger as l:
            assert l is logger
        # no error on double close
        logger.close()
