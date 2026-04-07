"""
Automation rules and schemas for JARVIS 2.0.

Defines the structure for automation rules, triggers, and actions.
"""

from typing import Dict, List, Any, Optional, Union
from datetime import datetime, time
from enum import Enum
from pydantic import BaseModel, Field


class TriggerType(Enum):
    """Types of automation triggers."""
    SCHEDULE = "schedule"  # Time-based (cron, interval)
    EVENT = "event"  # Event-based (file change, system event)
    WEBHOOK = "webhook"  # HTTP webhook
    MANUAL = "manual"  # Manually triggered
    CONDITION = "condition"  # Condition-based


class ScheduleType(Enum):
    """Types of schedules."""
    CRON = "cron"  # Cron expression
    INTERVAL = "interval"  # Run every X seconds/minutes/hours
    DATE = "date"  # Run at specific date/time
    DAILY = "daily"  # Run daily at specific time
    WEEKLY = "weekly"  # Run weekly on specific days
    MONTHLY = "monthly"  # Run monthly on specific day


class ActionType(Enum):
    """Types of actions."""
    COMMAND = "command"  # Execute shell command
    TOOL = "tool"  # Use JARVIS tool
    AGENT = "agent"  # Delegate to agent
    LLM = "llm"  # LLM query
    WEBHOOK = "webhook"  # HTTP request
    NOTIFICATION = "notification"  # Send notification
    SCRIPT = "script"  # Execute Python script


class AutomationStatus(Enum):
    """Automation rule status."""
    ACTIVE = "active"
    PAUSED = "paused"
    DISABLED = "disabled"
    ERROR = "error"


class ScheduleTrigger(BaseModel):
    """Schedule-based trigger configuration."""
    type: ScheduleType
    
    # For CRON
    cron_expression: Optional[str] = None
    
    # For INTERVAL
    interval_seconds: Optional[int] = None
    interval_minutes: Optional[int] = None
    interval_hours: Optional[int] = None
    
    # For DATE
    run_date: Optional[datetime] = None
    
    # For DAILY
    time: Optional[str] = None  # HH:MM format
    
    # For WEEKLY
    days_of_week: Optional[List[str]] = None  # ["mon", "wed", "fri"]
    
    # For MONTHLY
    day_of_month: Optional[int] = None
    
    # Timezone
    timezone: Optional[str] = "UTC"


class EventTrigger(BaseModel):
    """Event-based trigger configuration."""
    event_type: str  # file_changed, system_startup, etc.
    event_data: Optional[Dict[str, Any]] = {}
    
    # File watching
    watch_path: Optional[str] = None
    watch_pattern: Optional[str] = None  # Glob pattern
    
    # System events
    system_event: Optional[str] = None  # startup, shutdown, etc.


class ConditionTrigger(BaseModel):
    """Condition-based trigger."""
    condition_type: str  # cpu_usage, memory_usage, disk_space, etc.
    operator: str  # gt, lt, eq, gte, lte
    threshold: Union[int, float, str]
    check_interval: int = 60  # Seconds between checks


class Trigger(BaseModel):
    """Automation trigger."""
    trigger_type: TriggerType
    schedule: Optional[ScheduleTrigger] = None
    event: Optional[EventTrigger] = None
    condition: Optional[ConditionTrigger] = None
    webhook_path: Optional[str] = None


class Action(BaseModel):
    """Automation action."""
    action_type: ActionType
    
    # Command action
    command: Optional[str] = None
    
    # Tool action
    tool_name: Optional[str] = None
    tool_params: Optional[Dict[str, Any]] = {}
    
    # Agent action
    agent_task: Optional[str] = None
    agent_context: Optional[Dict[str, Any]] = {}
    
    # LLM action
    llm_prompt: Optional[str] = None
    
    # Webhook action
    webhook_url: Optional[str] = None
    webhook_method: Optional[str] = "POST"
    webhook_data: Optional[Dict[str, Any]] = {}
    
    # Notification action
    notification_message: Optional[str] = None
    notification_title: Optional[str] = None
    
    # Script action
    script_code: Optional[str] = None
    script_file: Optional[str] = None
    
    # Action behavior
    timeout: Optional[int] = 300  # Seconds
    retry_count: Optional[int] = 0
    retry_delay: Optional[int] = 60  # Seconds


class AutomationRule(BaseModel):
    """Complete automation rule."""
    id: str
    name: str
    description: Optional[str] = ""
    
    # Trigger configuration
    trigger: Trigger
    
    # Actions to execute
    actions: List[Action]
    
    # Rule metadata
    status: AutomationStatus = AutomationStatus.ACTIVE
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    
    # Options
    enabled: bool = True
    max_runs: Optional[int] = None  # Limit total runs
    run_on_startup: bool = False
    
    # Tags for organization
    tags: List[str] = []
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AutomationRun(BaseModel):
    """Record of an automation execution."""
    rule_id: str
    rule_name: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str  # success, failed, running
    actions_executed: int = 0
    actions_failed: int = 0
    error: Optional[str] = None
    output: Optional[Dict[str, Any]] = {}
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Pre-defined automation templates
AUTOMATION_TEMPLATES = {
    "daily_backup": {
        "name": "Daily Backup",
        "description": "Backup important files daily",
        "trigger": {
            "trigger_type": "schedule",
            "schedule": {
                "type": "daily",
                "time": "02:00"
            }
        },
        "actions": [
            {
                "action_type": "command",
                "command": "tar -czf backup-$(date +%Y%m%d).tar.gz /path/to/files"
            }
        ]
    },
    "morning_briefing": {
        "name": "Morning Briefing",
        "description": "Get daily briefing every morning",
        "trigger": {
            "trigger_type": "schedule",
            "schedule": {
                "type": "daily",
                "time": "08:00"
            }
        },
        "actions": [
            {
                "action_type": "agent",
                "agent_task": "Research today's news and give me a briefing"
            }
        ]
    },
    "high_cpu_alert": {
        "name": "High CPU Alert",
        "description": "Alert when CPU usage is high",
        "trigger": {
            "trigger_type": "condition",
            "condition": {
                "condition_type": "cpu_usage",
                "operator": "gt",
                "threshold": 80,
                "check_interval": 300
            }
        },
        "actions": [
            {
                "action_type": "notification",
                "notification_title": "High CPU Usage",
                "notification_message": "CPU usage is above 80%"
            }
        ]
    },
    "file_watcher": {
        "name": "File Watcher",
        "description": "Watch for file changes and process them",
        "trigger": {
            "trigger_type": "event",
            "event": {
                "event_type": "file_changed",
                "watch_path": "/path/to/watch",
                "watch_pattern": "*.txt"
            }
        },
        "actions": [
            {
                "action_type": "tool",
                "tool_name": "file_operations",
                "tool_params": {
                    "operation": "read"
                }
            }
        ]
    }
}
