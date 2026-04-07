"""
JARVIS 2.0 Usage Analytics Engine

Advanced analytics system for tracking user behavior, command usage patterns,
performance metrics, and generating actionable insights for personalization
and system optimization.
"""

import asyncio
from datetime import datetime, timedelta, time
from typing import Dict, List, Optional, Any, Tuple, Set
import logging
from collections import defaultdict, Counter, deque
import statistics
import json
from dataclasses import dataclass
import numpy as np

from .schemas import (
    CommandUsage, UsageSession, CommandCategory, UsageContext,
    BehaviorPatternType, LearningData, ResponseTone, ResponseVerbosity
)

logger = logging.getLogger(__name__)


@dataclass
class UsageMetrics:
    """Container for usage metrics and statistics"""
    total_commands: int = 0
    total_sessions: int = 0
    avg_session_duration: float = 0.0
    success_rate: float = 0.0
    avg_response_time: float = 0.0
    peak_usage_hour: int = 12
    most_used_command: str = ""
    most_used_category: CommandCategory = CommandCategory.SYSTEM
    command_diversity: float = 0.0  # Number of unique commands / total commands


@dataclass
class TrendAnalysis:
    """Container for trend analysis results"""
    usage_trend: str  # "increasing", "decreasing", "stable"
    performance_trend: str
    error_trend: str
    trend_strength: float  # 0.0 to 1.0
    period_days: int
    confidence: float


@dataclass
class CommandInsight:
    """Individual command performance insight"""
    command: str
    usage_count: int
    success_rate: float
    avg_execution_time: float
    error_patterns: List[str]
    usage_contexts: List[UsageContext]
    time_patterns: Dict[int, int]  # hour -> count
    recommendation: Optional[str] = None


class UsageAnalyzer:
    """Core analytics engine for processing usage data"""
    
    def __init__(self):
        self.analysis_cache = {}
        self.cache_ttl = timedelta(hours=1)
        self.last_cache_clear = datetime.utcnow()
    
    def analyze_command_usage(self, commands: List[CommandUsage], days: int = 30) -> List[CommandInsight]:
        """Analyze command usage patterns and performance"""
        if not commands:
            return []
        
        # Group commands by name
        command_groups = defaultdict(list)
        for cmd in commands:
            command_groups[cmd.command].append(cmd)
        
        insights = []
        
        for command_name, cmd_list in command_groups.items():
            # Calculate metrics
            total_usage = len(cmd_list)
            successful_commands = [cmd for cmd in cmd_list if cmd.success]
            success_rate = len(successful_commands) / total_usage if total_usage > 0 else 0
            
            # Average execution time
            execution_times = [cmd.execution_time_ms for cmd in cmd_list if cmd.execution_time_ms > 0]
            avg_execution = statistics.mean(execution_times) if execution_times else 0
            
            # Error patterns
            error_commands = [cmd for cmd in cmd_list if not cmd.success and cmd.error_message]
            error_patterns = Counter([cmd.error_message for cmd in error_commands]).most_common(3)
            error_list = [error for error, count in error_patterns]
            
            # Usage contexts
            contexts = [cmd.context for cmd in cmd_list]
            context_counter = Counter(contexts)
            primary_contexts = [ctx for ctx, count in context_counter.most_common(3)]
            
            # Time patterns (hour of day)
            time_patterns = defaultdict(int)
            for cmd in cmd_list:
                hour = cmd.timestamp.hour
                time_patterns[hour] += 1
            
            # Generate recommendation
            recommendation = self._generate_command_recommendation(
                command_name, success_rate, avg_execution, error_list, primary_contexts
            )
            
            insights.append(CommandInsight(
                command=command_name,
                usage_count=total_usage,
                success_rate=success_rate,
                avg_execution_time=avg_execution,
                error_patterns=error_list,
                usage_contexts=primary_contexts,
                time_patterns=dict(time_patterns),
                recommendation=recommendation
            ))
        
        # Sort by usage count
        insights.sort(key=lambda x: x.usage_count, reverse=True)
        return insights
    
    def analyze_session_patterns(self, sessions: List[UsageSession]) -> Dict[str, Any]:
        """Analyze user session patterns and behaviors"""
        if not sessions:
            return {}
        
        # Session duration analysis
        completed_sessions = [s for s in sessions if s.end_time is not None]
        if completed_sessions:
            durations = [s.duration_minutes for s in completed_sessions if s.duration_minutes]
            avg_duration = statistics.mean(durations) if durations else 0
            median_duration = statistics.median(durations) if durations else 0
        else:
            avg_duration = median_duration = 0
        
        # Time-of-day analysis
        start_hours = [s.start_time.hour for s in sessions]
        hour_distribution = Counter(start_hours)
        peak_hours = [hour for hour, count in hour_distribution.most_common(3)]
        
        # Day-of-week analysis
        weekdays = [s.start_time.weekday() for s in sessions]
        weekday_distribution = Counter(weekdays)
        
        # Context analysis
        all_contexts = []
        for session in sessions:
            all_contexts.extend(session.contexts_used)
        context_distribution = Counter(all_contexts)
        
        # Success rate trends
        recent_sessions = sorted(sessions, key=lambda x: x.start_time)[-30:]  # Last 30 sessions
        success_rates = [s.success_rate for s in recent_sessions]
        
        # Command diversity analysis
        total_commands = sum(s.total_commands for s in sessions)
        if total_commands > 0:
            avg_commands_per_session = total_commands / len(sessions)
        else:
            avg_commands_per_session = 0
        
        return {
            "total_sessions": len(sessions),
            "avg_session_duration_minutes": avg_duration,
            "median_session_duration_minutes": median_duration,
            "peak_usage_hours": peak_hours,
            "weekday_distribution": dict(weekday_distribution),
            "context_distribution": dict(context_distribution),
            "avg_commands_per_session": avg_commands_per_session,
            "recent_success_rate_trend": success_rates,
            "most_active_day": max(weekday_distribution, key=weekday_distribution.get) if weekday_distribution else 0
        }
    
    def analyze_performance_trends(self, commands: List[CommandUsage], days: int = 30) -> TrendAnalysis:
        """Analyze performance trends over time"""
        if len(commands) < 10:  # Need minimum data
            return TrendAnalysis(
                usage_trend="insufficient_data",
                performance_trend="insufficient_data", 
                error_trend="insufficient_data",
                trend_strength=0.0,
                period_days=days,
                confidence=0.0
            )
        
        # Sort commands by timestamp
        sorted_commands = sorted(commands, key=lambda x: x.timestamp)
        
        # Split into time buckets (daily)
        daily_buckets = defaultdict(list)
        for cmd in sorted_commands:
            day_key = cmd.timestamp.date()
            daily_buckets[day_key].append(cmd)
        
        # Extract metrics per day
        daily_usage = []
        daily_success_rates = []
        daily_avg_times = []
        
        for day in sorted(daily_buckets.keys()):
            day_commands = daily_buckets[day]
            
            # Usage count
            daily_usage.append(len(day_commands))
            
            # Success rate
            successful = len([cmd for cmd in day_commands if cmd.success])
            success_rate = successful / len(day_commands) if day_commands else 0
            daily_success_rates.append(success_rate)
            
            # Average execution time
            exec_times = [cmd.execution_time_ms for cmd in day_commands if cmd.execution_time_ms > 0]
            avg_time = statistics.mean(exec_times) if exec_times else 0
            daily_avg_times.append(avg_time)
        
        # Calculate trends
        usage_trend, usage_strength = self._calculate_trend(daily_usage)
        performance_trend, perf_strength = self._calculate_trend(daily_avg_times, invert=True)
        error_trend, error_strength = self._calculate_trend([1-rate for rate in daily_success_rates])
        
        # Overall trend strength and confidence
        trend_strength = (usage_strength + perf_strength + error_strength) / 3
        confidence = min(len(daily_buckets) / 7.0, 1.0)  # More confident with more days
        
        return TrendAnalysis(
            usage_trend=usage_trend,
            performance_trend=performance_trend,
            error_trend=error_trend,
            trend_strength=trend_strength,
            period_days=len(daily_buckets),
            confidence=confidence
        )
    
    def analyze_error_patterns(self, commands: List[CommandUsage]) -> Dict[str, Any]:
        """Analyze error patterns and failure modes"""
        failed_commands = [cmd for cmd in commands if not cmd.success and cmd.error_message]
        
        if not failed_commands:
            return {"error_rate": 0.0, "patterns": [], "recommendations": []}
        
        error_rate = len(failed_commands) / len(commands)
        
        # Common error messages
        error_counter = Counter([cmd.error_message for cmd in failed_commands])
        common_errors = error_counter.most_common(10)
        
        # Error patterns by command
        command_errors = defaultdict(list)
        for cmd in failed_commands:
            command_errors[cmd.command].append(cmd.error_message)
        
        # Error patterns by time
        error_times = [cmd.timestamp.hour for cmd in failed_commands]
        error_hour_distribution = Counter(error_times)
        
        # Generate recommendations
        recommendations = []
        for error_msg, count in common_errors[:3]:
            if "timeout" in error_msg.lower():
                recommendations.append("Consider increasing timeout values for long-running operations")
            elif "permission" in error_msg.lower():
                recommendations.append("Check file/directory permissions for frequently failing operations")
            elif "not found" in error_msg.lower():
                recommendations.append("Validate file paths and command availability before execution")
        
        return {
            "error_rate": error_rate,
            "total_errors": len(failed_commands),
            "common_errors": common_errors,
            "error_by_command": dict(command_errors),
            "error_hour_distribution": dict(error_hour_distribution),
            "recommendations": recommendations
        }
    
    def _calculate_trend(self, values: List[float], invert: bool = False) -> Tuple[str, float]:
        """Calculate trend direction and strength from time series data"""
        if len(values) < 3:
            return "insufficient_data", 0.0
        
        # Simple linear regression
        n = len(values)
        x = list(range(n))
        y = values if not invert else [-v for v in values]
        
        # Calculate slope
        x_mean = statistics.mean(x)
        y_mean = statistics.mean(y)
        
        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return "stable", 0.0
        
        slope = numerator / denominator
        
        # Determine trend direction and strength
        trend_strength = abs(slope) / (max(y) - min(y)) if max(y) != min(y) else 0
        trend_strength = min(trend_strength, 1.0)
        
        if abs(slope) < 0.01:  # Very small slope
            return "stable", trend_strength
        elif slope > 0:
            return "increasing", trend_strength
        else:
            return "decreasing", trend_strength
    
    def _generate_command_recommendation(self, command: str, success_rate: float, 
                                       avg_time: float, errors: List[str], 
                                       contexts: List[UsageContext]) -> Optional[str]:
        """Generate recommendations based on command analysis"""
        recommendations = []
        
        if success_rate < 0.8:
            recommendations.append(f"Low success rate ({success_rate:.1%}). Review command usage patterns.")
        
        if avg_time > 30000:  # > 30 seconds
            recommendations.append("High execution time. Consider optimization or async execution.")
        
        if errors:
            common_error_types = set()
            for error in errors:
                error_lower = error.lower()
                if "timeout" in error_lower:
                    common_error_types.add("timeout")
                elif "permission" in error_lower:
                    common_error_types.add("permission")
                elif "not found" in error_lower:
                    common_error_types.add("not_found")
            
            if common_error_types:
                recommendations.append(f"Common error types: {', '.join(common_error_types)}")
        
        return "; ".join(recommendations) if recommendations else None


class AnalyticsEngine:
    """Main analytics engine for JARVIS usage data"""
    
    def __init__(self, storage_backend=None):
        self.storage = storage_backend
        self.analyzer = UsageAnalyzer()
        self.analytics_enabled = True
        
        # Real-time analytics buffers
        self.recent_commands: deque = deque(maxlen=1000)
        self.active_sessions: Dict[str, UsageSession] = {}
        
        # Analytics cache
        self.metrics_cache = {}
        self.cache_ttl_minutes = 30
        
        # Configuration
        self.min_data_points = 10
        self.trend_analysis_days = 30
        self.insight_generation_interval = timedelta(hours=6)
        
        logger.info("AnalyticsEngine initialized")
    
    async def record_command_usage(self, command_usage: CommandUsage):
        """Record a command usage event"""
        if not self.analytics_enabled:
            return
        
        try:
            # Add to real-time buffer
            self.recent_commands.append(command_usage)
            
            # Update active session if exists
            if command_usage.session_id in self.active_sessions:
                session = self.active_sessions[command_usage.session_id]
                session.add_command(command_usage)
            
            # Store persistently
            if self.storage:
                await self.storage.store_command_usage(command_usage)
            
            # Trigger real-time insights if needed
            await self._check_real_time_insights()
            
        except Exception as e:
            logger.error(f"Error recording command usage: {e}")
    
    async def start_session(self, session: UsageSession):
        """Start tracking a new user session"""
        self.active_sessions[session.session_id] = session
        
        if self.storage:
            await self.storage.store_usage_session(session)
    
    async def end_session(self, session_id: str):
        """End a user session and finalize analytics"""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session.end_session()
            
            if self.storage:
                await self.storage.update_usage_session(session)
            
            del self.active_sessions[session_id]
    
    async def get_user_metrics(self, user_id: str, days: int = 30) -> UsageMetrics:
        """Get comprehensive usage metrics for a user"""
        cache_key = f"metrics_{user_id}_{days}"
        
        # Check cache
        if self._is_cache_valid(cache_key):
            return self.metrics_cache[cache_key]['data']
        
        try:
            if not self.storage:
                return UsageMetrics()
            
            # Get user data
            commands = await self.storage.get_user_command_history(user_id, days=days)
            sessions = await self.storage.get_user_sessions(user_id, days=days)
            
            if not commands:
                return UsageMetrics()
            
            # Calculate metrics
            total_commands = len(commands)
            total_sessions = len(sessions)
            
            # Success rate
            successful_commands = len([cmd for cmd in commands if cmd.success])
            success_rate = successful_commands / total_commands if total_commands > 0 else 0
            
            # Average response time
            response_times = [cmd.execution_time_ms for cmd in commands if cmd.execution_time_ms > 0]
            avg_response_time = statistics.mean(response_times) if response_times else 0
            
            # Session duration
            completed_sessions = [s for s in sessions if s.duration_minutes is not None]
            avg_session_duration = statistics.mean([s.duration_minutes for s in completed_sessions]) if completed_sessions else 0
            
            # Peak usage hour
            command_hours = [cmd.timestamp.hour for cmd in commands]
            peak_usage_hour = Counter(command_hours).most_common(1)[0][0] if command_hours else 12
            
            # Most used command and category
            command_counter = Counter([cmd.command for cmd in commands])
            most_used_command = command_counter.most_common(1)[0][0] if command_counter else ""
            
            category_counter = Counter([cmd.category for cmd in commands])
            most_used_category = category_counter.most_common(1)[0][0] if category_counter else CommandCategory.SYSTEM
            
            # Command diversity
            unique_commands = len(set([cmd.command for cmd in commands]))
            command_diversity = unique_commands / total_commands if total_commands > 0 else 0
            
            metrics = UsageMetrics(
                total_commands=total_commands,
                total_sessions=total_sessions,
                avg_session_duration=avg_session_duration,
                success_rate=success_rate,
                avg_response_time=avg_response_time,
                peak_usage_hour=peak_usage_hour,
                most_used_command=most_used_command,
                most_used_category=most_used_category,
                command_diversity=command_diversity
            )
            
            # Cache result
            self.metrics_cache[cache_key] = {
                'data': metrics,
                'timestamp': datetime.utcnow()
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error generating user metrics: {e}")
            return UsageMetrics()
    
    async def get_command_insights(self, user_id: str, days: int = 30) -> List[CommandInsight]:
        """Get detailed command usage insights"""
        cache_key = f"insights_{user_id}_{days}"
        
        if self._is_cache_valid(cache_key):
            return self.metrics_cache[cache_key]['data']
        
        try:
            if not self.storage:
                return []
            
            commands = await self.storage.get_user_command_history(user_id, days=days)
            insights = self.analyzer.analyze_command_usage(commands, days)
            
            # Cache result
            self.metrics_cache[cache_key] = {
                'data': insights,
                'timestamp': datetime.utcnow()
            }
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating command insights: {e}")
            return []
    
    async def get_trend_analysis(self, user_id: str, days: int = 30) -> TrendAnalysis:
        """Get trend analysis for user behavior"""
        try:
            if not self.storage:
                return TrendAnalysis(
                    usage_trend="no_data",
                    performance_trend="no_data",
                    error_trend="no_data",
                    trend_strength=0.0,
                    period_days=0,
                    confidence=0.0
                )
            
            commands = await self.storage.get_user_command_history(user_id, days=days)
            return self.analyzer.analyze_performance_trends(commands, days)
            
        except Exception as e:
            logger.error(f"Error generating trend analysis: {e}")
            return TrendAnalysis(
                usage_trend="error",
                performance_trend="error", 
                error_trend="error",
                trend_strength=0.0,
                period_days=0,
                confidence=0.0
            )
    
    async def get_session_patterns(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get session usage patterns"""
        try:
            if not self.storage:
                return {}
            
            sessions = await self.storage.get_user_sessions(user_id, days=days)
            return self.analyzer.analyze_session_patterns(sessions)
            
        except Exception as e:
            logger.error(f"Error analyzing session patterns: {e}")
            return {}
    
    async def get_error_analysis(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get error pattern analysis"""
        try:
            if not self.storage:
                return {"error_rate": 0.0, "patterns": []}
            
            commands = await self.storage.get_user_command_history(user_id, days=days)
            return self.analyzer.analyze_error_patterns(commands)
            
        except Exception as e:
            logger.error(f"Error analyzing error patterns: {e}")
            return {"error_rate": 0.0, "patterns": []}
    
    async def generate_learning_data(self, user_id: str, days: int = 30) -> LearningData:
        """Generate comprehensive learning data for ML/personalization"""
        try:
            # Get all analytics data
            metrics = await self.get_user_metrics(user_id, days)
            insights = await self.get_command_insights(user_id, days)
            session_patterns = await self.get_session_patterns(user_id, days)
            error_analysis = await self.get_error_analysis(user_id, days)
            
            # Extract command analytics
            most_used_commands = [
                {"command": insight.command, "count": insight.usage_count, "success_rate": insight.success_rate}
                for insight in insights[:10]
            ]
            
            command_categories = Counter()
            for insight in insights:
                # Would need to determine category from command
                command_categories["general"] += insight.usage_count
            
            # Peak usage hours
            peak_hours = []
            if self.storage:
                commands = await self.storage.get_user_command_history(user_id, days=days)
                hour_counter = Counter([cmd.timestamp.hour for cmd in commands])
                peak_hours = [hour for hour, count in hour_counter.most_common(3)]
            
            # Pattern analytics (would be populated by behavior detector)
            active_patterns_count = 0
            pattern_types_distribution = {}
            confidence_scores = {}
            
            # Personalization effectiveness (would be tracked separately)
            suggestion_acceptance_rate = 0.0
            personalization_satisfaction_score = 0.0
            adaptation_accuracy = 0.0
            
            return LearningData(
                user_id=user_id,
                total_sessions=metrics.total_sessions,
                total_commands=metrics.total_commands,
                average_session_duration_minutes=metrics.avg_session_duration,
                success_rate=metrics.success_rate,
                most_used_commands=most_used_commands,
                command_categories_distribution=dict(command_categories),
                peak_usage_hours=peak_hours,
                active_patterns_count=active_patterns_count,
                pattern_types_distribution=pattern_types_distribution,
                confidence_scores=confidence_scores,
                suggestion_acceptance_rate=suggestion_acceptance_rate,
                personalization_satisfaction_score=personalization_satisfaction_score,
                adaptation_accuracy=adaptation_accuracy,
                data_period_start=datetime.utcnow() - timedelta(days=days),
                data_period_end=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error generating learning data: {e}")
            return LearningData(
                user_id=user_id,
                data_period_start=datetime.utcnow(),
                data_period_end=datetime.utcnow()
            )
    
    async def _check_real_time_insights(self):
        """Check if real-time insights should be generated"""
        # Simple real-time anomaly detection
        if len(self.recent_commands) < 10:
            return
        
        recent_errors = [cmd for cmd in list(self.recent_commands)[-10:] if not cmd.success]
        if len(recent_errors) >= 5:  # 50% error rate in last 10 commands
            logger.warning(f"High error rate detected: {len(recent_errors)}/10 commands failed")
        
        # Check for performance issues
        recent_times = [cmd.execution_time_ms for cmd in list(self.recent_commands)[-10:] 
                       if cmd.execution_time_ms > 0]
        if recent_times:
            avg_time = statistics.mean(recent_times)
            if avg_time > 60000:  # > 1 minute average
                logger.warning(f"Performance degradation detected: avg {avg_time/1000:.1f}s execution time")
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid"""
        if cache_key not in self.metrics_cache:
            return False
        
        cache_age = datetime.utcnow() - self.metrics_cache[cache_key]['timestamp']
        return cache_age < timedelta(minutes=self.cache_ttl_minutes)
    
    def get_real_time_stats(self) -> Dict[str, Any]:
        """Get real-time statistics from recent commands"""
        if not self.recent_commands:
            return {}
        
        recent = list(self.recent_commands)
        
        return {
            "recent_command_count": len(recent),
            "recent_success_rate": len([cmd for cmd in recent if cmd.success]) / len(recent),
            "recent_avg_execution_time": statistics.mean([cmd.execution_time_ms for cmd in recent if cmd.execution_time_ms > 0]) if recent else 0,
            "active_sessions": len(self.active_sessions),
            "most_recent_command": recent[-1].command if recent else None,
            "most_recent_success": recent[-1].success if recent else None
        }
    
    def clear_cache(self):
        """Clear analytics cache"""
        self.metrics_cache.clear()
        logger.info("Analytics cache cleared")
    
    def enable_analytics(self):
        """Enable analytics collection"""
        self.analytics_enabled = True
        logger.info("Analytics enabled")
    
    def disable_analytics(self):
        """Disable analytics collection"""
        self.analytics_enabled = False
        logger.info("Analytics disabled")


# Export main classes
__all__ = [
    "AnalyticsEngine", "UsageAnalyzer", "UsageMetrics", 
    "TrendAnalysis", "CommandInsight"
]