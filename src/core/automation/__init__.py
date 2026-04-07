"""
Automation system for JARVIS 2.0.

Provides task scheduling, event triggers, and automation execution.
"""

from .schemas import (
    AutomationRule,
    Action,
    Trigger,
    TriggerType,
    ScheduleType,
    ActionType,
    AutomationStatus,
    ScheduleTrigger,
    EventTrigger,
    ConditionTrigger,
    AutomationRun,
    AUTOMATION_TEMPLATES
)
from .scheduler import automation_scheduler, AutomationScheduler
from .engine import automation_engine, AutomationEngine
from .builder import RuleBuilder, create_from_template, every, at

__all__ = [
    # Schemas
    "AutomationRule",
    "Action",
    "Trigger",
    "TriggerType",
    "ScheduleType",
    "ActionType",
    "AutomationStatus",
    "ScheduleTrigger",
    "EventTrigger",
    "ConditionTrigger",
    "AutomationRun",
    "AUTOMATION_TEMPLATES",
    
    # Scheduler
    "automation_scheduler",
    "AutomationScheduler",
    
    # Engine
    "automation_engine",
    "AutomationEngine",
    
    # Builder
    "RuleBuilder",
    "create_from_template",
    "every",
    "at",
]
