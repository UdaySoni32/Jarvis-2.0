"""Voice macro definitions and execution metadata."""

from dataclasses import dataclass
from typing import Dict, List, Optional

from .intent_router import AssistantMode


@dataclass(frozen=True)
class VoiceMacro:
    """Represents a named multi-step voice workflow."""

    name: str
    description: str
    steps: List[str]
    mode: AssistantMode = AssistantMode.PRODUCTIVITY


class MacroEngine:
    """Registry for built-in and user-extensible voice macros."""

    def __init__(self):
        self._macros: Dict[str, VoiceMacro] = {}
        self._register_builtin_macros()

    @staticmethod
    def normalize_name(name: str) -> str:
        """Normalize spoken macro names to canonical lookup keys."""
        return (name or "").strip().lower().replace("_", "-").replace(" ", "-")

    def _register_builtin_macros(self):
        self.register_macro(
            VoiceMacro(
                name="start-work-mode",
                description="Kick off focused work with priorities and a short execution plan.",
                steps=[
                    "Summarize my top priorities for today in 5 bullet points.",
                    "Suggest a focused 90-minute plan for the highest-priority item.",
                    "List likely blockers and one mitigation for each blocker.",
                ],
                mode=AssistantMode.PRODUCTIVITY,
            )
        )
        self.register_macro(
            VoiceMacro(
                name="incident-triage",
                description="Run a quick operations triage framework for an incident.",
                steps=[
                    "Provide a rapid triage checklist for a production incident.",
                    "List the top 3 signals to inspect first in logs and metrics.",
                    "Draft a short incident update message for stakeholders.",
                ],
                mode=AssistantMode.OPS,
            )
        )
        self.register_macro(
            VoiceMacro(
                name="code-debug-sprint",
                description="Debugging flow for code failures and quick iteration.",
                steps=[
                    "Propose a minimal debugging plan for this issue.",
                    "List likely root causes ranked by probability.",
                    "Give the smallest safe patch strategy and validation checklist.",
                ],
                mode=AssistantMode.CODING,
            )
        )

    def register_macro(self, macro: VoiceMacro):
        """Register or replace a macro definition."""
        self._macros[self.normalize_name(macro.name)] = macro

    def list_macros(self) -> List[VoiceMacro]:
        """Return all macros sorted by name."""
        return [self._macros[key] for key in sorted(self._macros.keys())]

    def get_macro(self, name: str) -> Optional[VoiceMacro]:
        """Lookup macro by spoken/written name."""
        return self._macros.get(self.normalize_name(name))

