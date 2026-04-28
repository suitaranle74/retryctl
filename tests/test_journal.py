"""Tests for retryctl.journal."""
from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from retryctl.journal import AttemptRecord, Journal


COMMAND = ["echo", "hello"]


# ---------------------------------------------------------------------------
# AttemptRecord
# ---------------------------------------------------------------------------
class TestAttemptRecord:
    def test_succeeded_on_zero(self):
        rec = AttemptRecord(attempt=1, exit_code=0, duration_s=0.1)
        assert rec.succeeded() is True

    def test_failed_on_nonzero(self):
        rec = AttemptRecord(attempt=1, exit_code=1, duration_s=0.1)
        assert rec.succeeded() is False

    def test_timestamp_auto_set(self):
        before = time.time()
        rec = AttemptRecord(attempt=1, exit_code=0, duration_s=0.0)
        assert rec.timestamp >= before


# ---------------------------------------------------------------------------
# Journal
# ---------------------------------------------------------------------------
class TestJournal:
    def _make(self) -> Journal:
        return Journal(command=COMMAND)

    def test_empty_journal_not_succeeded(self):
        j = self._make()
        assert j.succeeded() is False

    def test_record_appends(self):
        j = self._make()
        j.record(attempt=1, exit_code=0, duration_s=0.5)
        assert j.total_attempts() == 1

    def test_succeeded_after_zero_exit(self):
        j = self._make()
        j.record(attempt=1, exit_code=1, duration_s=0.1)
        j.record(attempt=2, exit_code=0, duration_s=0.2)
        assert j.succeeded() is True

    def test_not_succeeded_if_last_failed(self):
        j = self._make()
        j.record(attempt=1, exit_code=0, duration_s=0.1)
        j.record(attempt=2, exit_code=2, duration_s=0.1)
        assert j.succeeded() is False

    def test_total_duration(self):
        j = self._make()
        j.record(attempt=1, exit_code=1, duration_s=1.0)
        j.record(attempt=2, exit_code=0, duration_s=2.5)
        assert j.total_duration_s() == pytest.approx(3.5)


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------
class TestJournalPersistence:
    def test_save_and_load_round_trip(self, tmp_path):
        j = Journal(command=COMMAND)
        j.record(attempt=1, exit_code=1, duration_s=0.3)
        j.record(attempt=2, exit_code=0, duration_s=0.7)

        dest = tmp_path / "run.json"
        j.save(dest)

        loaded = Journal.load(dest)
        assert loaded.command == COMMAND
        assert loaded.total_attempts() == 2
        assert loaded.succeeded() is True
        assert loaded.total_duration_s() == pytest.approx(1.0)

    def test_save_creates_parent_dirs(self, tmp_path):
        j = Journal(command=COMMAND)
        j.record(attempt=1, exit_code=0, duration_s=0.1)
        dest = tmp_path / "nested" / "deep" / "run.json"
        j.save(dest)
        assert dest.exists()

    def test_saved_json_structure(self, tmp_path):
        j = Journal(command=COMMAND)
        j.record(attempt=1, exit_code=0, duration_s=0.2)
        dest = tmp_path / "run.json"
        j.save(dest)
        data = json.loads(dest.read_text())
        assert "command" in data
        assert "attempts" in data
        assert data["total_attempts"] == 1
        assert data["succeeded"] is True
