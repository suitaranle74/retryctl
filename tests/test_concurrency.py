"""Tests for retryctl.concurrency."""
import threading
import time
import pytest

from retryctl.concurrency import ConcurrencyConfig, ConcurrencyLimiter


# ---------------------------------------------------------------------------
# ConcurrencyConfig
# ---------------------------------------------------------------------------

class TestConcurrencyConfig:
    def test_defaults(self):
        cfg = ConcurrencyConfig()
        assert cfg.enabled is False
        assert cfg.max_concurrent == 1
        assert cfg.timeout is None

    def test_custom_values(self):
        cfg = ConcurrencyConfig(enabled=True, max_concurrent=4, timeout=2.5)
        assert cfg.enabled is True
        assert cfg.max_concurrent == 4
        assert cfg.timeout == 2.5

    def test_from_dict_full(self):
        cfg = ConcurrencyConfig.from_dict(
            {"enabled": True, "max_concurrent": 3, "timeout": 1.0}
        )
        assert cfg.enabled is True
        assert cfg.max_concurrent == 3
        assert cfg.timeout == 1.0

    def test_from_dict_ignores_unknown_keys(self):
        cfg = ConcurrencyConfig.from_dict({"enabled": True, "bogus": "value"})
        assert cfg.enabled is True
        assert not hasattr(cfg, "bogus")


# ---------------------------------------------------------------------------
# ConcurrencyLimiter — disabled
# ---------------------------------------------------------------------------

class TestConcurrencyLimiterDisabled:
    def _make(self, **kw) -> ConcurrencyLimiter:
        return ConcurrencyLimiter(ConcurrencyConfig(**kw))

    def test_acquire_always_true_when_disabled(self):
        limiter = self._make(enabled=False)
        assert limiter.acquire() is True

    def test_available_is_none_when_disabled(self):
        limiter = self._make(enabled=False)
        assert limiter.available is None

    def test_context_manager_no_error_when_disabled(self):
        limiter = self._make(enabled=False)
        with limiter:
            pass  # should not raise


# ---------------------------------------------------------------------------
# ConcurrencyLimiter — enabled
# ---------------------------------------------------------------------------

class TestConcurrencyLimiterEnabled:
    def _make(self, max_concurrent=2, timeout=None) -> ConcurrencyLimiter:
        return ConcurrencyLimiter(
            ConcurrencyConfig(enabled=True, max_concurrent=max_concurrent, timeout=timeout)
        )

    def test_available_starts_at_max(self):
        limiter = self._make(max_concurrent=3)
        assert limiter.available == 3

    def test_acquire_decrements_available(self):
        limiter = self._make(max_concurrent=2)
        limiter.acquire()
        assert limiter.available == 1

    def test_release_restores_slot(self):
        limiter = self._make(max_concurrent=1)
        limiter.acquire()
        limiter.release()
        assert limiter.available == 1

    def test_context_manager_releases_on_exit(self):
        limiter = self._make(max_concurrent=1)
        with limiter:
            assert limiter.available == 0
        assert limiter.available == 1

    def test_timeout_returns_false_when_slots_exhausted(self):
        limiter = self._make(max_concurrent=1, timeout=0.05)
        limiter.acquire()  # exhaust the single slot
        result = limiter.acquire()  # should time out
        assert result is False
        limiter.release()  # clean up

    def test_context_manager_raises_on_timeout(self):
        limiter = self._make(max_concurrent=1, timeout=0.05)
        limiter.acquire()
        with pytest.raises(TimeoutError):
            with limiter:
                pass
        limiter.release()

    def test_concurrent_threads_respect_limit(self):
        limiter = self._make(max_concurrent=2)
        active: list[int] = []
        errors: list[str] = []
        lock = threading.Lock()

        def worker():
            with limiter:
                with lock:
                    active.append(1)
                    if sum(active) > 2:
                        errors.append("exceeded max_concurrent")
                time.sleep(0.02)
                with lock:
                    active.pop()

        threads = [threading.Thread(target=worker) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == [], errors
