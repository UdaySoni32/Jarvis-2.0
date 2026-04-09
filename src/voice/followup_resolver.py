"""Natural follow-up command resolver for voice conversations."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class FollowupResolution:
    """Result of resolving a follow-up utterance."""

    original_input: str
    resolved_input: str
    is_followup: bool
    reason: Optional[str] = None


class FollowupResolver:
    """Resolve contextual follow-up phrases into explicit requests."""

    def resolve(
        self,
        user_input: str,
        last_user_input: Optional[str],
        last_response: Optional[str],
    ) -> FollowupResolution:
        normalized = (user_input or "").strip().lower()
        original = user_input

        if normalized.startswith("do the same for ") and last_user_input:
            target = user_input.strip()[len("do the same for "):].strip()
            base = last_user_input
            if " for " in base.lower():
                split_idx = base.lower().rfind(" for ")
                base = base[:split_idx]
            return FollowupResolution(
                original_input=original,
                resolved_input=f"{base} for {target}",
                is_followup=True,
                reason="same_for",
            )

        if normalized in {"do the same", "same again", "repeat that"} and last_user_input:
            return FollowupResolution(
                original_input=original,
                resolved_input=last_user_input,
                is_followup=True,
                reason="repeat_last_request",
            )

        if normalized in {"make it shorter", "shorter", "summarize that"} and last_response:
            return FollowupResolution(
                original_input=original,
                resolved_input=(
                    "Rewrite the following response to be shorter and clearer:\n\n"
                    f"{last_response}"
                ),
                is_followup=True,
                reason="shorten_last_response",
            )

        if normalized in {"expand on that", "go deeper", "more detail"} and last_response:
            return FollowupResolution(
                original_input=original,
                resolved_input=(
                    "Expand the following response with more details, examples, and practical steps:\n\n"
                    f"{last_response}"
                ),
                is_followup=True,
                reason="expand_last_response",
            )

        if normalized.startswith("send it to ") and last_response:
            recipient = user_input.strip()[len("send it to "):].strip()
            return FollowupResolution(
                original_input=original,
                resolved_input=(
                    f"Draft a concise message to {recipient} using this content:\n\n{last_response}"
                ),
                is_followup=True,
                reason="send_last_response",
            )

        return FollowupResolution(
            original_input=original,
            resolved_input=original,
            is_followup=False,
            reason=None,
        )

