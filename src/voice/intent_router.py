"""
Voice Intent Router for JARVIS.

Routes spoken requests into high-level assistant modes so responses can be
tailored for coding, ops, productivity, research, or general conversation.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple


class AssistantMode(str, Enum):
    """Supported high-level assistant modes."""

    GENERAL = "general"
    CODING = "coding"
    OPS = "ops"
    PRODUCTIVITY = "productivity"
    RESEARCH = "research"


@dataclass(frozen=True)
class IntentRoute:
    """Result of intent routing."""

    mode: AssistantMode
    confidence: float
    matched_keywords: List[str]
    source: str  # "auto" or "manual"


class IntentRouter:
    """Keyword-based intent router for voice requests."""

    MODE_KEYWORDS: Dict[AssistantMode, Tuple[str, ...]] = {
        AssistantMode.CODING: (
            "code",
            "python",
            "javascript",
            "typescript",
            "debug",
            "fix bug",
            "test",
            "refactor",
            "function",
            "class",
            "api",
            "terminal",
            "stack trace",
        ),
        AssistantMode.OPS: (
            "deploy",
            "server",
            "docker",
            "kubernetes",
            "cpu",
            "memory",
            "disk",
            "incident",
            "monitoring",
            "logs",
            "uptime",
            "restart",
        ),
        AssistantMode.PRODUCTIVITY: (
            "calendar",
            "meeting",
            "email",
            "reminder",
            "todo",
            "task",
            "schedule",
            "plan",
            "follow up",
        ),
        AssistantMode.RESEARCH: (
            "research",
            "summarize",
            "compare",
            "analyze",
            "deep dive",
            "pros and cons",
            "best option",
            "find sources",
        ),
    }

    MODE_PROMPTS: Dict[AssistantMode, str] = {
        AssistantMode.GENERAL: (
            "Mode: general assistant. Keep responses concise, clear, and practical."
        ),
        AssistantMode.CODING: (
            "Mode: coding assistant. Prioritize correctness, debugging steps, and implementation details."
        ),
        AssistantMode.OPS: (
            "Mode: operations assistant. Prioritize reliability, observability, and safe operational actions."
        ),
        AssistantMode.PRODUCTIVITY: (
            "Mode: productivity assistant. Prioritize actionable plans, prioritization, and concise task outcomes."
        ),
        AssistantMode.RESEARCH: (
            "Mode: research assistant. Prioritize structured comparison, tradeoffs, and evidence-driven summaries."
        ),
    }

    def __init__(self, default_mode: AssistantMode = AssistantMode.GENERAL):
        self.default_mode = default_mode

    def classify(self, text: str) -> IntentRoute:
        """Classify free-form text into an assistant mode."""
        normalized = (text or "").strip().lower()
        if not normalized:
            return IntentRoute(
                mode=self.default_mode,
                confidence=0.0,
                matched_keywords=[],
                source="auto",
            )

        best_mode = self.default_mode
        best_score = 0
        best_matches: List[str] = []

        for mode, keywords in self.MODE_KEYWORDS.items():
            matches = [keyword for keyword in keywords if keyword in normalized]
            score = len(matches)
            if score > best_score:
                best_mode = mode
                best_score = score
                best_matches = matches

        if best_score == 0:
            return IntentRoute(
                mode=self.default_mode,
                confidence=0.2,
                matched_keywords=[],
                source="auto",
            )

        confidence = min(1.0, 0.35 + (0.15 * best_score))
        return IntentRoute(
            mode=best_mode,
            confidence=confidence,
            matched_keywords=best_matches,
            source="auto",
        )

    def mode_prompt(self, mode: AssistantMode) -> str:
        """Return system prompt fragment for a selected mode."""
        return self.MODE_PROMPTS.get(mode, self.MODE_PROMPTS[self.default_mode])

    def route_input(
        self,
        text: str,
        explicit_mode: Optional[AssistantMode] = None,
    ) -> Tuple[str, IntentRoute]:
        """
        Route user input and produce a mode-scoped prompt.

        Returns:
            Tuple of (routed_prompt, route_result)
        """
        if explicit_mode is not None:
            route = IntentRoute(
                mode=explicit_mode,
                confidence=1.0,
                matched_keywords=[],
                source="manual",
            )
        else:
            route = self.classify(text)

        routed_prompt = f"{self.mode_prompt(route.mode)}\n\nUser request: {text}"
        return routed_prompt, route

