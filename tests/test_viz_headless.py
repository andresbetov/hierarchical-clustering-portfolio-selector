"""Contract tests for runtime diagnostics decisions (backend guard, log level)."""

import logging

import pytest

from portfolio_engine.core import logging_utils
from portfolio_engine.viz.reporting import _resolve_backend


class TestResolveBackend:
    """Pure decision function — environment permutations, no canvas involved."""

    def test_headless_linux_forces_agg(self):
        env = {"DISPLAY": ""}
        assert _resolve_backend(env, "linux") == "Agg"

    def test_display_present_defers(self):
        env = {"DISPLAY": ":0"}
        assert _resolve_backend(env, "linux") is None

    def test_explicit_mplbackend_always_wins(self):
        env = {"MPLBACKEND": "QtAgg", "DISPLAY": ""}
        assert _resolve_backend(env, "linux") is None
        env2 = {"MPLBACKEND": "TkAgg", "DISPLAY": ":0"}
        assert _resolve_backend(env2, "linux") is None

    def test_macos_native_defers_even_headless_shell(self):
        # macOS without DISPLAY still has native backends.
        assert _resolve_backend({}, "darwin") is None


class TestResolveLevel:
    """Level precedence: explicit param > LOG_LEVEL env > INFO."""

    def test_explicit_int_returns_int(self):
        assert logging_utils._resolve_level(logging.DEBUG) == logging.DEBUG

    def test_explicit_str_case_insensitive(self):
        assert logging_utils._resolve_level("warning") == logging.WARNING

    def test_env_used_when_no_param(self, monkeypatch):
        monkeypatch.setenv("LOG_LEVEL", "debug")
        assert logging_utils._resolve_level(None) == logging.DEBUG

    def test_param_beats_env(self, monkeypatch):
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        assert logging_utils._resolve_level(logging.ERROR) == logging.ERROR

    def test_invalid_env_warns_and_defaults(self, monkeypatch):
        monkeypatch.setenv("LOG_LEVEL", "VERBOSE_MODE")
        level = logging_utils._resolve_level(None)
        assert level == logging.INFO

    def test_default_is_info(self, monkeypatch):
        monkeypatch.delenv("LOG_LEVEL", raising=False)
        assert logging_utils._resolve_level(None) == logging.INFO


class TestConfigureLoggingIdempotent:
    """Package logger must stay isolated from root and deduplicated."""

    def _handler_count(self) -> int:
        pkg = logging.getLogger("portfolio_engine")
        return sum(
            1 for h in pkg.handlers if getattr(h, "_portfolio_engine_stream_handler_tag", None)
            or h.get_name() == "_portfolio_engine_stream_handler"
        )

    def test_double_call_single_handler_with_caplog_active(self):
        """caplog attaches root handlers; package config must not fight it."""
        pkg = logging.getLogger("portfolio_engine")
        before = list(pkg.handlers)

        logging_utils.configure_logging(logging.INFO)
        logging_utils.configure_logging()

        owned = [
            h for h in pkg.handlers if h.get_name() == "_portfolio_engine_stream_handler"
        ]
        assert len(owned) == 1
        assert len(pkg.handlers) - len(before) <= 1

    def test_root_logger_untouched(self):
        root_before = len(logging.getLogger().handlers)
        logging_utils.configure_logging()
        assert len(logging.getLogger().handlers) == root_before

    def test_package_propagation_disabled(self):
        logging_utils.configure_logging()
        assert logging.getLogger("portfolio_engine").propagate is False

    def test_reinvocation_with_explicit_level_updates_level(self):
        logging_utils.configure_logging(logging.INFO)
        logging_utils.configure_logging("DEBUG")
        assert logging.getLogger("portfolio_engine").level == logging.DEBUG


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
