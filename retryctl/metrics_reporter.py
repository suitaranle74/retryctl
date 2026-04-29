"""Formats and outputs run metrics to stdout or a file."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional, TextIO

from retryctl.metrics import MetricsConfig, RunMetrics


class MetricsReporter:
    def __init__(
        self,
        config: MetricsConfig,
        output_path: Optional[Path] = None,
        stream: Optional[TextIO] = None,
    ) -> None:
        self._config = config
        self._output_path = output_path
        self._stream = stream or sys.stderr

    def report(self, metrics: RunMetrics) -> None:
        if not self._config.enabled:
            return
        summary = metrics.summary(self._config)
        payload = json.dumps(summary, indent=2)
        if self._output_path is not None:
            self._write_file(payload)
        else:
            self._stream.write(payload + "\n")
            self._stream.flush()

    def _write_file(self, payload: str) -> None:
        assert self._output_path is not None
        self._output_path.parent.mkdir(parents=True, exist_ok=True)
        with self._output_path.open("w", encoding="utf-8") as fh:
            fh.write(payload + "\n")
