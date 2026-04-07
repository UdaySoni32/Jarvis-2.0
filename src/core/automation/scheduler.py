"""
Task scheduler for JARVIS 2.0 automation system.

Uses APScheduler for job scheduling and execution.
"""

import asyncio
from typing import Dict, List, Optional, Callable
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.job import Job

from ..logger import logger
from .schemas import (
    AutomationRule,
    ScheduleTrigger,
    ScheduleType,
    AutomationStatus,
    AutomationRun
)


class AutomationScheduler:
    """
    Manages scheduled automation tasks.
    
    Uses APScheduler to schedule and execute automation rules.
    """
    
    def __init__(self):
        """Initialize scheduler."""
        self.scheduler = AsyncIOScheduler(timezone='UTC')
        self.rules: Dict[str, AutomationRule] = {}
        self.running = False
        logger.info("Automation scheduler initialized")
    
    def start(self):
        """Start the scheduler."""
        if not self.running:
            self.scheduler.start()
            self.running = True
            logger.info("Automation scheduler started")
    
    def shutdown(self):
        """Shutdown the scheduler."""
        if self.running:
            self.scheduler.shutdown(wait=True)
            self.running = False
            logger.info("Automation scheduler shut down")
    
    def add_rule(self, rule: AutomationRule, callback: Callable) -> bool:
        """
        Add an automation rule to the scheduler.
        
        Args:
            rule: Automation rule
            callback: Function to call when triggered
            
        Returns:
            True if added successfully
        """
        try:
            if rule.trigger.schedule is None:
                logger.warning(f"Rule {rule.id} has no schedule trigger")
                return False
            
            trigger = self._create_trigger(rule.trigger.schedule)
            if trigger is None:
                logger.error(f"Failed to create trigger for rule {rule.id}")
                return False
            
            # Add job to scheduler
            job = self.scheduler.add_job(
                callback,
                trigger=trigger,
                id=rule.id,
                name=rule.name,
                replace_existing=True,
                max_instances=1,
                misfire_grace_time=60
            )
            
            self.rules[rule.id] = rule
            
            # Update next run time
            try:
                if hasattr(job, 'next_run_time') and job.next_run_time:
                    rule.next_run = job.next_run_time
            except AttributeError:
                # Fallback for different APScheduler versions
                pass
            
            logger.info(f"Added automation rule: {rule.name} (next run: {rule.next_run})")
            return True
            
        except Exception as e:
            logger.error(f"Error adding rule {rule.id}: {e}")
            return False
    
    def remove_rule(self, rule_id: str) -> bool:
        """
        Remove an automation rule.
        
        Args:
            rule_id: Rule ID
            
        Returns:
            True if removed successfully
        """
        try:
            self.scheduler.remove_job(rule_id)
            if rule_id in self.rules:
                del self.rules[rule_id]
            logger.info(f"Removed automation rule: {rule_id}")
            return True
        except Exception as e:
            logger.error(f"Error removing rule {rule_id}: {e}")
            return False
    
    def pause_rule(self, rule_id: str) -> bool:
        """Pause a rule."""
        try:
            self.scheduler.pause_job(rule_id)
            if rule_id in self.rules:
                self.rules[rule_id].status = AutomationStatus.PAUSED
            logger.info(f"Paused automation rule: {rule_id}")
            return True
        except Exception as e:
            logger.error(f"Error pausing rule {rule_id}: {e}")
            return False
    
    def resume_rule(self, rule_id: str) -> bool:
        """Resume a paused rule."""
        try:
            self.scheduler.resume_job(rule_id)
            if rule_id in self.rules:
                self.rules[rule_id].status = AutomationStatus.ACTIVE
            logger.info(f"Resumed automation rule: {rule_id}")
            return True
        except Exception as e:
            logger.error(f"Error resuming rule {rule_id}: {e}")
            return False
    
    def get_rule(self, rule_id: str) -> Optional[AutomationRule]:
        """Get a rule by ID."""
        return self.rules.get(rule_id)
    
    def list_rules(self) -> List[AutomationRule]:
        """List all rules."""
        return list(self.rules.values())
    
    def get_job_info(self, rule_id: str) -> Optional[Dict]:
        """Get job information."""
        try:
            job: Job = self.scheduler.get_job(rule_id)
            if job:
                info = {
                    "id": job.id,
                    "name": job.name,
                    "trigger": str(job.trigger)
                }
                
                # Handle different APScheduler versions
                try:
                    info["next_run_time"] = job.next_run_time
                except AttributeError:
                    info["next_run_time"] = None
                
                try:
                    info["pending"] = job.pending
                except AttributeError:
                    info["pending"] = False
                
                return info
        except Exception as e:
            logger.error(f"Error getting job info for {rule_id}: {e}")
        return None
    
    def list_jobs(self) -> List[Dict]:
        """List all scheduled jobs."""
        jobs = []
        for job in self.scheduler.get_jobs():
            job_info = {
                "id": job.id,
                "name": job.name,
                "trigger": str(job.trigger)
            }
            
            # Handle different APScheduler versions
            try:
                job_info["next_run_time"] = job.next_run_time
            except AttributeError:
                job_info["next_run_time"] = None
                
            jobs.append(job_info)
        return jobs
        return jobs
    
    def _create_trigger(self, schedule: ScheduleTrigger):
        """
        Create APScheduler trigger from schedule configuration.
        
        Args:
            schedule: Schedule configuration
            
        Returns:
            APScheduler trigger object
        """
        try:
            if schedule.type == ScheduleType.CRON:
                if not schedule.cron_expression:
                    logger.error("CRON schedule requires cron_expression")
                    return None
                return CronTrigger.from_crontab(
                    schedule.cron_expression,
                    timezone=schedule.timezone
                )
            
            elif schedule.type == ScheduleType.INTERVAL:
                kwargs = {}
                if schedule.interval_seconds:
                    kwargs['seconds'] = schedule.interval_seconds
                if schedule.interval_minutes:
                    kwargs['minutes'] = schedule.interval_minutes
                if schedule.interval_hours:
                    kwargs['hours'] = schedule.interval_hours
                
                if not kwargs:
                    logger.error("INTERVAL schedule requires at least one interval value")
                    return None
                
                return IntervalTrigger(**kwargs, timezone=schedule.timezone)
            
            elif schedule.type == ScheduleType.DATE:
                if not schedule.run_date:
                    logger.error("DATE schedule requires run_date")
                    return None
                return DateTrigger(run_date=schedule.run_date, timezone=schedule.timezone)
            
            elif schedule.type == ScheduleType.DAILY:
                if not schedule.time:
                    logger.error("DAILY schedule requires time (HH:MM)")
                    return None
                hour, minute = map(int, schedule.time.split(':'))
                return CronTrigger(
                    hour=hour,
                    minute=minute,
                    timezone=schedule.timezone
                )
            
            elif schedule.type == ScheduleType.WEEKLY:
                if not schedule.days_of_week or not schedule.time:
                    logger.error("WEEKLY schedule requires days_of_week and time")
                    return None
                hour, minute = map(int, schedule.time.split(':'))
                day_map = {
                    'mon': 0, 'tue': 1, 'wed': 2, 'thu': 3,
                    'fri': 4, 'sat': 5, 'sun': 6
                }
                days = [day_map[d.lower()] for d in schedule.days_of_week]
                return CronTrigger(
                    day_of_week=','.join(map(str, days)),
                    hour=hour,
                    minute=minute,
                    timezone=schedule.timezone
                )
            
            elif schedule.type == ScheduleType.MONTHLY:
                if not schedule.day_of_month or not schedule.time:
                    logger.error("MONTHLY schedule requires day_of_month and time")
                    return None
                hour, minute = map(int, schedule.time.split(':'))
                return CronTrigger(
                    day=schedule.day_of_month,
                    hour=hour,
                    minute=minute,
                    timezone=schedule.timezone
                )
            
            else:
                logger.error(f"Unknown schedule type: {schedule.type}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating trigger: {e}")
            return None


# Global scheduler instance
automation_scheduler = AutomationScheduler()
