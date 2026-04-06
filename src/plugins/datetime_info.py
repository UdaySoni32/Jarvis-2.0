"""Date and time tool."""

from datetime import datetime, timedelta
from typing import Dict
import calendar

from core.tools.base import BaseTool, ToolParameter


class DateTimeTool(BaseTool):
    """Gets current date, time, and calendar information."""

    def get_parameters(self) -> Dict[str, ToolParameter]:
        """Get tool parameters."""
        return {
            "info_type": ToolParameter(
                name="info_type",
                type="string",
                description="Type of date/time info to get",
                required=False,
                default="current",
                enum=["current", "date", "time", "calendar", "timezone"],
            ),
            "format": ToolParameter(
                name="format",
                type="string",
                description="Date/time format (default: human-readable)",
                required=False,
                default="human",
                enum=["human", "iso", "unix"],
            ),
        }

    async def execute(self, info_type: str = "current", format: str = "human") -> Dict:
        """
        Get date/time information.

        Args:
            info_type: Type of info (current, date, time, calendar, timezone)
            format: Output format (human, iso, unix)

        Returns:
            Date/time information
        """
        now = datetime.now()
        result = {}

        if info_type in ["current", "date", "time"]:
            if format == "iso":
                result["datetime"] = now.isoformat()
                result["date"] = now.date().isoformat()
                result["time"] = now.time().isoformat()
            elif format == "unix":
                result["timestamp"] = int(now.timestamp())
            else:  # human
                result["datetime"] = now.strftime("%A, %B %d, %Y at %I:%M:%S %p")
                result["date"] = now.strftime("%A, %B %d, %Y")
                result["time"] = now.strftime("%I:%M:%S %p")
                result["day_of_week"] = now.strftime("%A")
                result["month"] = now.strftime("%B")
                result["year"] = now.year

        if info_type == "calendar":
            # Get calendar for current month
            cal = calendar.monthcalendar(now.year, now.month)
            month_name = calendar.month_name[now.month]
            result["month"] = month_name
            result["year"] = now.year
            result["current_day"] = now.day
            result["calendar"] = cal
            result["month_name"] = f"{month_name} {now.year}"

        if info_type == "timezone":
            result["timezone"] = now.astimezone().tzname()
            result["utc_offset"] = now.astimezone().strftime("%z")

        # Add helpful context
        result["weekday_number"] = now.weekday()  # 0=Monday
        result["day_of_year"] = now.timetuple().tm_yday
        result["week_number"] = now.isocalendar()[1]

        return result
