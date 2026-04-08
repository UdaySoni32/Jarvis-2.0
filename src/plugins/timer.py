"""Timer and reminder tool."""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List
import threading
import time

from src.core.tools.base import BaseTool, ToolParameter
from src.core.logger import logger


class TimerManager:
    """Manages active timers."""

    def __init__(self):
        self.timers: Dict[str, Dict] = {}
        self.timer_id_counter = 0

    def create_timer(self, duration_seconds: int, label: str = "") -> str:
        """Create a new timer."""
        self.timer_id_counter += 1
        timer_id = f"timer_{self.timer_id_counter}"

        end_time = datetime.now() + timedelta(seconds=duration_seconds)

        self.timers[timer_id] = {
            "id": timer_id,
            "label": label or f"Timer {self.timer_id_counter}",
            "duration": duration_seconds,
            "end_time": end_time,
            "started": datetime.now(),
            "completed": False,
        }

        # Start timer thread
        thread = threading.Thread(
            target=self._timer_thread, args=(timer_id, duration_seconds), daemon=True
        )
        thread.start()

        logger.info(f"Started timer {timer_id}: {duration_seconds}s")
        return timer_id

    def _timer_thread(self, timer_id: str, duration: int):
        """Timer thread that waits and marks timer as complete."""
        time.sleep(duration)
        if timer_id in self.timers:
            self.timers[timer_id]["completed"] = True
            logger.info(f"Timer {timer_id} completed!")

    def get_timer(self, timer_id: str) -> Dict:
        """Get timer status."""
        return self.timers.get(timer_id, {})

    def list_timers(self) -> List[Dict]:
        """List all active timers."""
        return [
            {
                "id": t["id"],
                "label": t["label"],
                "end_time": t["end_time"].isoformat(),
                "completed": t["completed"],
                "remaining_seconds": max(
                    0, (t["end_time"] - datetime.now()).total_seconds()
                )
                if not t["completed"]
                else 0,
            }
            for t in self.timers.values()
        ]

    def cancel_timer(self, timer_id: str) -> bool:
        """Cancel a timer."""
        if timer_id in self.timers:
            del self.timers[timer_id]
            logger.info(f"Cancelled timer {timer_id}")
            return True
        return False


# Global timer manager
timer_manager = TimerManager()


class TimerTool(BaseTool):
    """Creates and manages timers and reminders."""

    def get_parameters(self) -> Dict[str, ToolParameter]:
        """Get tool parameters."""
        return {
            "action": ToolParameter(
                name="action",
                type="string",
                description="Timer action",
                required=True,
                enum=["create", "list", "status", "cancel"],
            ),
            "duration": ToolParameter(
                name="duration",
                type="number",
                description="Duration in seconds (for create action)",
                required=False,
            ),
            "label": ToolParameter(
                name="label",
                type="string",
                description="Timer label/description (for create action)",
                required=False,
            ),
            "timer_id": ToolParameter(
                name="timer_id",
                type="string",
                description="Timer ID (for status/cancel actions)",
                required=False,
            ),
        }

    async def execute(
        self,
        action: str,
        duration: int = None,
        label: str = "",
        timer_id: str = None,
    ) -> Dict:
        """
        Manage timers.

        Args:
            action: create, list, status, or cancel
            duration: Timer duration in seconds
            label: Timer label
            timer_id: Timer ID for status/cancel

        Returns:
            Timer information
        """
        if action == "create":
            if not duration:
                raise ValueError("Duration required for create action")

            timer_id = timer_manager.create_timer(duration, label)
            timer = timer_manager.get_timer(timer_id)

            return {
                "action": "created",
                "timer_id": timer_id,
                "label": timer["label"],
                "duration_seconds": duration,
                "end_time": timer["end_time"].isoformat(),
                "message": f"Timer '{timer['label']}' set for {duration} seconds",
            }

        elif action == "list":
            timers = timer_manager.list_timers()
            return {
                "action": "list",
                "timers": timers,
                "count": len(timers),
            }

        elif action == "status":
            if not timer_id:
                raise ValueError("Timer ID required for status action")

            timer = timer_manager.get_timer(timer_id)
            if not timer:
                raise ValueError(f"Timer not found: {timer_id}")

            remaining = (
                max(0, (timer["end_time"] - datetime.now()).total_seconds())
                if not timer["completed"]
                else 0
            )

            return {
                "action": "status",
                "timer_id": timer_id,
                "label": timer["label"],
                "completed": timer["completed"],
                "remaining_seconds": remaining,
                "end_time": timer["end_time"].isoformat(),
            }

        elif action == "cancel":
            if not timer_id:
                raise ValueError("Timer ID required for cancel action")

            success = timer_manager.cancel_timer(timer_id)
            if not success:
                raise ValueError(f"Timer not found: {timer_id}")

            return {
                "action": "cancelled",
                "timer_id": timer_id,
                "message": f"Timer {timer_id} cancelled",
            }

        else:
            raise ValueError(f"Unknown action: {action}")
