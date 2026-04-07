"""
Rule builder for creating automation rules easily.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

from .schemas import (
    AutomationRule,
    Trigger,
    TriggerType,
    ScheduleTrigger,
    ScheduleType,
    EventTrigger,
    ConditionTrigger,
    Action,
    ActionType,
    AutomationStatus,
    AUTOMATION_TEMPLATES
)


class RuleBuilder:
    """
    Fluent interface for building automation rules.
    
    Example:
        rule = (RuleBuilder()
            .name("Daily Backup")
            .daily("02:00")
            .command("backup.sh")
            .build())
    """
    
    def __init__(self):
        """Initialize rule builder."""
        self._id = str(uuid.uuid4())
        self._name = ""
        self._description = ""
        self._trigger: Optional[Trigger] = None
        self._actions: List[Action] = []
        self._status = AutomationStatus.ACTIVE
        self._enabled = True
        self._tags: List[str] = []
        self._max_runs: Optional[int] = None
        self._run_on_startup = False
    
    def id(self, rule_id: str) -> 'RuleBuilder':
        """Set rule ID."""
        self._id = rule_id
        return self
    
    def name(self, name: str) -> 'RuleBuilder':
        """Set rule name."""
        self._name = name
        return self
    
    def description(self, desc: str) -> 'RuleBuilder':
        """Set rule description."""
        self._description = desc
        return self
    
    def tags(self, *tags: str) -> 'RuleBuilder':
        """Add tags."""
        self._tags.extend(tags)
        return self
    
    def max_runs(self, count: int) -> 'RuleBuilder':
        """Set maximum runs."""
        self._max_runs = count
        return self
    
    def run_on_startup(self, enabled: bool = True) -> 'RuleBuilder':
        """Set run on startup."""
        self._run_on_startup = enabled
        return self
    
    # Trigger builders
    
    def cron(self, expression: str, timezone: str = "UTC") -> 'RuleBuilder':
        """Add cron trigger."""
        self._trigger = Trigger(
            trigger_type=TriggerType.SCHEDULE,
            schedule=ScheduleTrigger(
                type=ScheduleType.CRON,
                cron_expression=expression,
                timezone=timezone
            )
        )
        return self
    
    def interval(
        self,
        seconds: Optional[int] = None,
        minutes: Optional[int] = None,
        hours: Optional[int] = None,
        timezone: str = "UTC"
    ) -> 'RuleBuilder':
        """Add interval trigger."""
        self._trigger = Trigger(
            trigger_type=TriggerType.SCHEDULE,
            schedule=ScheduleTrigger(
                type=ScheduleType.INTERVAL,
                interval_seconds=seconds,
                interval_minutes=minutes,
                interval_hours=hours,
                timezone=timezone
            )
        )
        return self
    
    def daily(self, time: str, timezone: str = "UTC") -> 'RuleBuilder':
        """Add daily trigger (time in HH:MM format)."""
        self._trigger = Trigger(
            trigger_type=TriggerType.SCHEDULE,
            schedule=ScheduleTrigger(
                type=ScheduleType.DAILY,
                time=time,
                timezone=timezone
            )
        )
        return self
    
    def weekly(
        self,
        days: List[str],
        time: str,
        timezone: str = "UTC"
    ) -> 'RuleBuilder':
        """Add weekly trigger."""
        self._trigger = Trigger(
            trigger_type=TriggerType.SCHEDULE,
            schedule=ScheduleTrigger(
                type=ScheduleType.WEEKLY,
                days_of_week=days,
                time=time,
                timezone=timezone
            )
        )
        return self
    
    def monthly(
        self,
        day: int,
        time: str,
        timezone: str = "UTC"
    ) -> 'RuleBuilder':
        """Add monthly trigger."""
        self._trigger = Trigger(
            trigger_type=TriggerType.SCHEDULE,
            schedule=ScheduleTrigger(
                type=ScheduleType.MONTHLY,
                day_of_month=day,
                time=time,
                timezone=timezone
            )
        )
        return self
    
    def on_event(
        self,
        event_type: str,
        event_data: Optional[Dict[str, Any]] = None
    ) -> 'RuleBuilder':
        """Add event trigger."""
        self._trigger = Trigger(
            trigger_type=TriggerType.EVENT,
            event=EventTrigger(
                event_type=event_type,
                event_data=event_data or {}
            )
        )
        return self
    
    def on_file_change(
        self,
        path: str,
        pattern: Optional[str] = None
    ) -> 'RuleBuilder':
        """Add file change trigger."""
        self._trigger = Trigger(
            trigger_type=TriggerType.EVENT,
            event=EventTrigger(
                event_type="file_changed",
                watch_path=path,
                watch_pattern=pattern
            )
        )
        return self
    
    def on_condition(
        self,
        condition_type: str,
        operator: str,
        threshold: Any,
        check_interval: int = 60
    ) -> 'RuleBuilder':
        """Add condition trigger."""
        self._trigger = Trigger(
            trigger_type=TriggerType.CONDITION,
            condition=ConditionTrigger(
                condition_type=condition_type,
                operator=operator,
                threshold=threshold,
                check_interval=check_interval
            )
        )
        return self
    
    # Action builders
    
    def command(
        self,
        command: str,
        timeout: int = 300,
        retry_count: int = 0
    ) -> 'RuleBuilder':
        """Add command action."""
        self._actions.append(Action(
            action_type=ActionType.COMMAND,
            command=command,
            timeout=timeout,
            retry_count=retry_count
        ))
        return self
    
    def tool(
        self,
        tool_name: str,
        params: Optional[Dict[str, Any]] = None,
        timeout: int = 300
    ) -> 'RuleBuilder':
        """Add tool action."""
        self._actions.append(Action(
            action_type=ActionType.TOOL,
            tool_name=tool_name,
            tool_params=params or {},
            timeout=timeout
        ))
        return self
    
    def agent(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        timeout: int = 300
    ) -> 'RuleBuilder':
        """Add agent action."""
        self._actions.append(Action(
            action_type=ActionType.AGENT,
            agent_task=task,
            agent_context=context or {},
            timeout=timeout
        ))
        return self
    
    def llm(
        self,
        prompt: str,
        timeout: int = 300
    ) -> 'RuleBuilder':
        """Add LLM action."""
        self._actions.append(Action(
            action_type=ActionType.LLM,
            llm_prompt=prompt,
            timeout=timeout
        ))
        return self
    
    def notify(
        self,
        message: str,
        title: Optional[str] = None
    ) -> 'RuleBuilder':
        """Add notification action."""
        self._actions.append(Action(
            action_type=ActionType.NOTIFICATION,
            notification_message=message,
            notification_title=title or "JARVIS Automation"
        ))
        return self
    
    def webhook(
        self,
        url: str,
        method: str = "POST",
        data: Optional[Dict[str, Any]] = None,
        timeout: int = 30
    ) -> 'RuleBuilder':
        """Add webhook action."""
        self._actions.append(Action(
            action_type=ActionType.WEBHOOK,
            webhook_url=url,
            webhook_method=method,
            webhook_data=data or {},
            timeout=timeout
        ))
        return self
    
    def script(
        self,
        code: Optional[str] = None,
        file: Optional[str] = None,
        timeout: int = 300
    ) -> 'RuleBuilder':
        """Add script action."""
        self._actions.append(Action(
            action_type=ActionType.SCRIPT,
            script_code=code,
            script_file=file,
            timeout=timeout
        ))
        return self
    
    def build(self) -> AutomationRule:
        """Build the automation rule."""
        if not self._name:
            raise ValueError("Rule name is required")
        if not self._trigger:
            raise ValueError("Rule trigger is required")
        if not self._actions:
            raise ValueError("At least one action is required")
        
        return AutomationRule(
            id=self._id,
            name=self._name,
            description=self._description,
            trigger=self._trigger,
            actions=self._actions,
            status=self._status,
            enabled=self._enabled,
            tags=self._tags,
            max_runs=self._max_runs,
            run_on_startup=self._run_on_startup
        )


def create_from_template(template_name: str, **overrides) -> Optional[AutomationRule]:
    """
    Create a rule from a template.
    
    Args:
        template_name: Template name
        **overrides: Template overrides
        
    Returns:
        Automation rule or None if template not found
    """
    if template_name not in AUTOMATION_TEMPLATES:
        return None
    
    template = AUTOMATION_TEMPLATES[template_name].copy()
    template.update(overrides)
    
    # Generate ID if not provided
    if 'id' not in template:
        template['id'] = str(uuid.uuid4())
    
    # Parse trigger
    trigger_data = template['trigger']
    trigger = Trigger(**trigger_data)
    
    # Parse actions
    actions = [Action(**action_data) for action_data in template['actions']]
    
    return AutomationRule(
        id=template['id'],
        name=template['name'],
        description=template.get('description', ''),
        trigger=trigger,
        actions=actions
    )


# Helper functions for common patterns

def every(interval_value: int, unit: str = "minutes") -> RuleBuilder:
    """
    Create rule that runs every X time units.
    
    Example:
        rule = every(5, "minutes").command("echo hello").build()
    """
    builder = RuleBuilder()
    
    if unit in ["second", "seconds"]:
        builder.interval(seconds=interval_value)
    elif unit in ["minute", "minutes"]:
        builder.interval(minutes=interval_value)
    elif unit in ["hour", "hours"]:
        builder.interval(hours=interval_value)
    else:
        raise ValueError(f"Unknown unit: {unit}")
    
    return builder


def at(time: str, days: Optional[List[str]] = None) -> RuleBuilder:
    """
    Create rule that runs at specific time.
    
    Examples:
        # Daily at 9 AM
        rule = at("09:00").command("echo morning").build()
        
        # Weekdays at 9 AM
        rule = at("09:00", ["mon", "tue", "wed", "thu", "fri"]).command("work").build()
    """
    builder = RuleBuilder()
    
    if days:
        builder.weekly(days, time)
    else:
        builder.daily(time)
    
    return builder
