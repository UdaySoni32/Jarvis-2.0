"""CLI package for JARVIS 2.0."""

__all__ = ["REPL", "main"]


def __getattr__(name):
    """Lazily import heavy CLI modules when accessed."""
    if name in {"REPL", "main"}:
        from .repl import REPL, main

        exports = {"REPL": REPL, "main": main}
        return exports[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
