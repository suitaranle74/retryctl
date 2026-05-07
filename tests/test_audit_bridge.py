"""Tests for retryctl.audit_bridge."""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from retryctl.audit import AuditConfig
from retryctl.audit_bridge import audit_config_from_file


class TestAuditConfigFromFile:
    def _make(self, **kwargs):
        fc = MagicMock()
        fc.audit_enabled = kwargs.get("audit_enabled", None)
        fc.audit_output_file = kwargs.get("audit_output_file", None)
        fc.audit_include_output = kwargs.get("audit_include_output", None)
        fc.audit_include_env = kwargs.get("audit_include_env", None)
        return fc

    def test_defaults_produce_disabled_audit(self):
        fc = self._make()
        cfg = audit_config_from_file(fc)
        assert isinstance(cfg, AuditConfig)
        assert cfg.enabled is False

    def test_enabled_forwarded(self):
        fc = self._make(audit_enabled=True)
        cfg = audit_config_from_file(fc)
        assert cfg.enabled is True

    def test_output_file_forwarded(self):
        fc = self._make(audit_output_file="/var/log/audit.jsonl")
        cfg = audit_config_from_file(fc)
        assert cfg.output_file == "/var/log/audit.jsonl"

    def test_include_output_forwarded(self):
        fc = self._make(audit_include_output=True)
        cfg = audit_config_from_file(fc)
        assert cfg.include_output is True

    def test_include_env_forwarded(self):
        fc = self._make(audit_include_env=True)
        cfg = audit_config_from_file(fc)
        assert cfg.include_env is True

    def test_none_fields_use_defaults(self):
        fc = self._make(audit_enabled=True)
        cfg = audit_config_from_file(fc)
        assert cfg.output_file is None
        assert cfg.include_output is False
        assert cfg.include_env is False
