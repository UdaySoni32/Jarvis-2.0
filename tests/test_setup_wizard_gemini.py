"""Regression checks for Gemini setup wizard behavior."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.cli import setup_wizard


def test_needs_setup_when_gemini_selected_but_key_missing(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("DEFAULT_LLM=gemini\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    assert setup_wizard.needs_setup() is True


def test_needs_setup_false_when_gemini_selected_and_key_present(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "DEFAULT_LLM=gemini\nGEMINI_API_KEY=gemini_test_key\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    assert setup_wizard.needs_setup() is False
