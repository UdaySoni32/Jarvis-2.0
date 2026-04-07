"""
Test suite for automation system.
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.automation import (
    RuleBuilder,
    every,
    at,
    create_from_template,
    automation_engine,
    automation_scheduler,
    AutomationStatus,
    TriggerType,
    ActionType,
    ScheduleType
)


def test_rule_builder_daily():
    """Test building a daily automation rule."""
    print("Testing daily rule builder...")
    
    rule = (RuleBuilder()
        .name("Daily Backup")
        .description("Backup files every day")
        .daily("02:00")
        .command("echo 'Backup complete'")
        .build())
    
    assert rule.name == "Daily Backup"
    assert rule.trigger.trigger_type == TriggerType.SCHEDULE
    assert rule.trigger.schedule.type == ScheduleType.DAILY
    assert rule.trigger.schedule.time == "02:00"
    assert len(rule.actions) == 1
    assert rule.actions[0].action_type == ActionType.COMMAND
    print("✅ Daily rule builder test passed\n")


def test_rule_builder_interval():
    """Test building interval automation rule."""
    print("Testing interval rule builder...")
    
    rule = every(5, "minutes").name("Health Check").command("echo 'healthy'").build()
    
    assert rule.name == "Health Check"
    assert rule.trigger.trigger_type == TriggerType.SCHEDULE
    assert rule.trigger.schedule.type == ScheduleType.INTERVAL
    assert rule.trigger.schedule.interval_minutes == 5
    print("✅ Interval rule builder test passed\n")


def test_rule_builder_weekly():
    """Test building weekly automation rule."""
    print("Testing weekly rule builder...")
    
    rule = (at("09:00", ["mon", "wed", "fri"])
        .name("Weekday Task")
        .command("echo 'Good morning'")
        .build())
    
    assert rule.name == "Weekday Task"
    assert rule.trigger.trigger_type == TriggerType.SCHEDULE
    assert rule.trigger.schedule.type == ScheduleType.WEEKLY
    assert rule.trigger.schedule.days_of_week == ["mon", "wed", "fri"]
    assert rule.trigger.schedule.time == "09:00"
    print("✅ Weekly rule builder test passed\n")


def test_rule_builder_multiple_actions():
    """Test rule with multiple actions."""
    print("Testing multiple actions...")
    
    rule = (RuleBuilder()
        .name("Multi-Action Rule")
        .daily("10:00")
        .command("echo 'Step 1'")
        .notify("Task started", "Automation")
        .tool("weather", {"city": "Tokyo"})
        .build())
    
    assert len(rule.actions) == 3
    assert rule.actions[0].action_type == ActionType.COMMAND
    assert rule.actions[1].action_type == ActionType.NOTIFICATION
    assert rule.actions[2].action_type == ActionType.TOOL
    print("✅ Multiple actions test passed\n")


def test_rule_builder_cron():
    """Test cron expression rule."""
    print("Testing cron rule...")
    
    rule = (RuleBuilder()
        .name("Cron Task")
        .cron("0 */2 * * *")  # Every 2 hours
        .command("echo 'Cron task'")
        .build())
    
    assert rule.trigger.schedule.type == ScheduleType.CRON
    assert rule.trigger.schedule.cron_expression == "0 */2 * * *"
    print("✅ Cron rule test passed\n")


def test_rule_builder_tags():
    """Test rule tags and metadata."""
    print("Testing rule metadata...")
    
    rule = (RuleBuilder()
        .name("Tagged Rule")
        .tags("backup", "daily", "important")
        .max_runs(30)
        .run_on_startup(True)
        .daily("03:00")
        .command("backup.sh")
        .build())
    
    assert len(rule.tags) == 3
    assert "backup" in rule.tags
    assert rule.max_runs == 30
    assert rule.run_on_startup == True
    print("✅ Rule metadata test passed\n")


def test_action_types():
    """Test different action types."""
    print("Testing action types...")
    
    # Command action
    rule1 = (RuleBuilder()
        .name("Command Test")
        .daily("10:00")
        .command("ls -la", timeout=60)
        .build())
    assert rule1.actions[0].command == "ls -la"
    assert rule1.actions[0].timeout == 60
    print("✅ Command action")
    
    # Tool action
    rule2 = (RuleBuilder()
        .name("Tool Test")
        .daily("11:00")
        .tool("weather", {"city": "London"})
        .build())
    assert rule2.actions[0].tool_name == "weather"
    assert rule2.actions[0].tool_params["city"] == "London"
    print("✅ Tool action")
    
    # Agent action
    rule3 = (RuleBuilder()
        .name("Agent Test")
        .daily("12:00")
        .agent("research Python trends", {"depth": "detailed"})
        .build())
    assert rule3.actions[0].agent_task == "research Python trends"
    print("✅ Agent action")
    
    # LLM action
    rule4 = (RuleBuilder()
        .name("LLM Test")
        .daily("13:00")
        .llm("Summarize today's events")
        .build())
    assert rule4.actions[0].llm_prompt == "Summarize today's events"
    print("✅ LLM action")
    
    # Notification action
    rule5 = (RuleBuilder()
        .name("Notify Test")
        .daily("14:00")
        .notify("Task complete", "Success")
        .build())
    assert rule5.actions[0].notification_message == "Task complete"
    assert rule5.actions[0].notification_title == "Success"
    print("✅ Notification action")
    
    print("✅ All action types test passed\n")


def test_template_creation():
    """Test creating rules from templates."""
    print("Testing template creation...")
    
    # Daily backup template
    rule = create_from_template("daily_backup")
    assert rule is not None
    assert rule.name == "Daily Backup"
    assert rule.trigger.trigger_type == TriggerType.SCHEDULE
    print("✅ Daily backup template")
    
    # Morning briefing template
    rule2 = create_from_template("morning_briefing")
    assert rule2 is not None
    assert rule2.name == "Morning Briefing"
    print("✅ Morning briefing template")
    
    # High CPU alert template
    rule3 = create_from_template("high_cpu_alert")
    assert rule3 is not None
    assert rule3.name == "High CPU Alert"
    assert rule3.trigger.trigger_type == TriggerType.CONDITION
    print("✅ High CPU alert template")
    
    print("✅ Template creation test passed\n")


async def test_engine_add_rule():
    """Test adding rules to engine."""
    print("Testing engine rule management...")
    
    rule = (RuleBuilder()
        .name("Test Rule")
        .interval(minutes=1)
        .command("echo 'test'")
        .build())
    
    # Add rule
    success = await automation_engine.add_rule(rule)
    assert success, "Should add rule successfully"
    print("✅ Added rule to engine")
    
    # Retrieve rule
    retrieved = automation_engine.get_rule(rule.id)
    assert retrieved is not None
    assert retrieved.name == "Test Rule"
    print("✅ Retrieved rule from engine")
    
    # List rules
    rules = automation_engine.list_rules()
    assert len(rules) >= 1
    print(f"✅ Listed {len(rules)} rules")
    
    # Remove rule
    success = await automation_engine.remove_rule(rule.id)
    assert success, "Should remove rule successfully"
    print("✅ Removed rule from engine")
    
    print("✅ Engine rule management test passed\n")


async def test_engine_pause_resume():
    """Test pausing and resuming rules."""
    print("Testing rule pause/resume...")
    
    rule = (RuleBuilder()
        .name("Pausable Rule")
        .interval(minutes=5)
        .command("echo 'pausable'")
        .build())
    
    await automation_engine.add_rule(rule)
    
    # Pause
    success = await automation_engine.pause_rule(rule.id)
    assert success
    assert automation_engine.get_rule(rule.id).status == AutomationStatus.PAUSED
    print("✅ Paused rule")
    
    # Resume
    success = await automation_engine.resume_rule(rule.id)
    assert success
    assert automation_engine.get_rule(rule.id).status == AutomationStatus.ACTIVE
    print("✅ Resumed rule")
    
    # Cleanup
    await automation_engine.remove_rule(rule.id)
    
    print("✅ Pause/resume test passed\n")


async def test_action_execution():
    """Test executing a simple automation rule."""
    print("Testing rule execution...")
    
    rule = (RuleBuilder()
        .name("Execution Test")
        .interval(seconds=1)  # Would run every second if scheduled
        .command("echo 'Hello from automation'")
        .build())
    
    # Add rule (but don't start scheduler)
    await automation_engine.add_rule(rule)
    
    # Manually execute
    result = await automation_engine.execute_rule(rule.id)
    
    assert result["success"], "Execution should succeed"
    assert rule.run_count == 1, "Run count should be 1"
    assert rule.last_run is not None, "Last run should be set"
    print("✅ Rule executed successfully")
    print(f"  Run count: {rule.run_count}")
    print(f"  Last run: {rule.last_run}")
    
    # Check recent runs
    runs = automation_engine.get_recent_runs(limit=5)
    assert len(runs) >= 1
    print(f"✅ Found {len(runs)} recent runs")
    
    # Cleanup
    await automation_engine.remove_rule(rule.id)
    
    print("✅ Rule execution test passed\n")


def test_schedule_type_validation():
    """Test schedule type validation."""
    print("Testing schedule validation...")
    
    # Valid daily schedule
    try:
        rule = (RuleBuilder()
            .name("Valid Daily")
            .daily("10:00")
            .command("test")
            .build())
        print("✅ Valid daily schedule")
    except Exception as e:
        print(f"❌ Daily schedule failed: {e}")
        raise
    
    # Valid interval schedule
    try:
        rule = (RuleBuilder()
            .name("Valid Interval")
            .interval(minutes=30)
            .command("test")
            .build())
        print("✅ Valid interval schedule")
    except Exception as e:
        print(f"❌ Interval schedule failed: {e}")
        raise
    
    # Valid cron schedule
    try:
        rule = (RuleBuilder()
            .name("Valid Cron")
            .cron("0 9 * * *")
            .command("test")
            .build())
        print("✅ Valid cron schedule")
    except Exception as e:
        print(f"❌ Cron schedule failed: {e}")
        raise
    
    print("✅ Schedule validation test passed\n")


async def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("AUTOMATION SYSTEM TEST SUITE")
    print("=" * 60)
    print()
    
    try:
        # Synchronous tests
        test_rule_builder_daily()
        test_rule_builder_interval()
        test_rule_builder_weekly()
        test_rule_builder_multiple_actions()
        test_rule_builder_cron()
        test_rule_builder_tags()
        test_action_types()
        test_template_creation()
        test_schedule_type_validation()
        
        # Asynchronous tests
        await test_engine_add_rule()
        await test_engine_pause_resume()
        await test_action_execution()
        
        print("=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print()
        print("Note: Scheduler integration requires LLM/tools for full testing.")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
