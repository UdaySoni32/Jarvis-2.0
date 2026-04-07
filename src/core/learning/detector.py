"""
JARVIS 2.0 Behavior Pattern Detector

Advanced ML-based system for detecting user behavior patterns, habits,
and workflow preferences. Uses statistical analysis and simple machine
learning techniques to identify recurring patterns in user interactions.
"""

import asyncio
from datetime import datetime, timedelta, time
from typing import Dict, List, Optional, Any, Tuple, Set
import logging
from collections import defaultdict, Counter, deque
import statistics
import json
from dataclasses import dataclass
import math

from .schemas import (
    CommandUsage, UsageSession, BehaviorPattern, BehaviorPatternType,
    CommandCategory, UsageContext, UserPreferences
)

logger = logging.getLogger(__name__)


@dataclass
class PatternCandidate:
    """A potential behavior pattern that needs validation"""
    pattern_type: BehaviorPatternType
    name: str
    description: str
    evidence: List[Any]
    confidence: float
    strength: float
    pattern_data: Dict[str, Any]


class TimePatternDetector:
    """Detects time-based behavior patterns"""
    
    def detect_peak_usage_times(self, commands: List[CommandUsage]) -> List[PatternCandidate]:
        """Detect when user is most active"""
        if len(commands) < 20:  # Need sufficient data
            return []
        
        # Group by hour of day
        hour_counts = defaultdict(int)
        for cmd in commands:
            hour_counts[cmd.timestamp.hour] += 1
        
        if not hour_counts:
            return []
        
        # Find peak hours (top 3)
        sorted_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)
        total_commands = len(commands)
        
        patterns = []
        for i, (hour, count) in enumerate(sorted_hours[:3]):
            usage_percentage = (count / total_commands) * 100
            
            if usage_percentage > 15:  # At least 15% of usage
                confidence = min(usage_percentage / 30.0, 1.0)  # Max confidence at 30%
                strength = count / sorted_hours[0][1]  # Relative to peak
                
                # Determine time period name
                if 6 <= hour <= 11:
                    period_name = "Morning Peak"
                elif 12 <= hour <= 17:
                    period_name = "Afternoon Peak"
                elif 18 <= hour <= 22:
                    period_name = "Evening Peak"
                else:
                    period_name = "Late Night Peak"
                
                patterns.append(PatternCandidate(
                    pattern_type=BehaviorPatternType.TIME_BASED,
                    name=f"{period_name} at {hour:02d}:00",
                    description=f"High activity at {hour:02d}:00 ({usage_percentage:.1f}% of total usage)",
                    evidence=[f"{count} commands at hour {hour}"],
                    confidence=confidence,
                    strength=strength,
                    pattern_data={
                        "peak_hour": hour,
                        "command_count": count,
                        "usage_percentage": usage_percentage,
                        "period_name": period_name
                    }
                ))
        
        return patterns
    
    def detect_session_timing_patterns(self, sessions: List[UsageSession]) -> List[PatternCandidate]:
        """Detect patterns in session timing and duration"""
        if len(sessions) < 10:
            return []
        
        patterns = []
        
        # Session duration patterns
        completed_sessions = [s for s in sessions if s.duration_minutes is not None]
        if completed_sessions:
            durations = [s.duration_minutes for s in completed_sessions]
            avg_duration = statistics.mean(durations)
            
            # Categorize session length preference
            if avg_duration < 5:
                duration_type = "Quick Sessions"
                description = f"Prefers brief sessions (avg {avg_duration:.1f} min)"
            elif avg_duration < 15:
                duration_type = "Short Sessions"
                description = f"Prefers short sessions (avg {avg_duration:.1f} min)"
            elif avg_duration < 45:
                duration_type = "Medium Sessions"
                description = f"Prefers medium-length sessions (avg {avg_duration:.1f} min)"
            else:
                duration_type = "Long Sessions"
                description = f"Prefers extended sessions (avg {avg_duration:.1f} min)"
            
            patterns.append(PatternCandidate(
                pattern_type=BehaviorPatternType.TIME_BASED,
                name=duration_type,
                description=description,
                evidence=[f"Average duration: {avg_duration:.1f} minutes"],
                confidence=min(len(completed_sessions) / 20.0, 1.0),
                strength=0.8,
                pattern_data={
                    "average_duration_minutes": avg_duration,
                    "session_count": len(completed_sessions),
                    "duration_category": duration_type
                }
            ))
        
        # Day-of-week patterns
        weekday_counts = Counter([s.start_time.weekday() for s in sessions])
        if weekday_counts:
            # Check for weekend vs weekday preference
            weekday_sessions = sum(count for day, count in weekday_counts.items() if day < 5)  # Mon-Fri
            weekend_sessions = sum(count for day, count in weekday_counts.items() if day >= 5)  # Sat-Sun
            
            total = weekday_sessions + weekend_sessions
            if total > 0:
                weekend_ratio = weekend_sessions / total
                
                if weekend_ratio > 0.4:  # 40%+ weekend usage
                    patterns.append(PatternCandidate(
                        pattern_type=BehaviorPatternType.TIME_BASED,
                        name="Weekend Usage Pattern",
                        description=f"High weekend activity ({weekend_ratio:.1%} of sessions)",
                        evidence=[f"{weekend_sessions} weekend sessions out of {total}"],
                        confidence=min(total / 15.0, 1.0),
                        strength=weekend_ratio,
                        pattern_data={
                            "weekend_ratio": weekend_ratio,
                            "weekend_sessions": weekend_sessions,
                            "weekday_sessions": weekday_sessions
                        }
                    ))
        
        return patterns


class CommandSequenceDetector:
    """Detects command sequence and workflow patterns"""
    
    def detect_command_chains(self, commands: List[CommandUsage], min_chain_length: int = 3) -> List[PatternCandidate]:
        """Detect frequently used command sequences"""
        if len(commands) < min_chain_length * 5:  # Need enough data
            return []
        
        # Group commands by session and sort by timestamp
        session_commands = defaultdict(list)
        for cmd in commands:
            session_commands[cmd.session_id].append(cmd)
        
        # Sort commands within each session
        for session_id in session_commands:
            session_commands[session_id].sort(key=lambda x: x.timestamp)
        
        # Extract command sequences
        sequences = []
        for session_id, session_cmds in session_commands.items():
            if len(session_cmds) >= min_chain_length:
                for i in range(len(session_cmds) - min_chain_length + 1):
                    sequence = tuple([cmd.command for cmd in session_cmds[i:i + min_chain_length]])
                    sequences.append(sequence)
        
        # Count sequence frequency
        sequence_counts = Counter(sequences)
        patterns = []
        
        for sequence, count in sequence_counts.most_common(10):
            if count >= 3:  # Occurred at least 3 times
                confidence = min(count / 10.0, 1.0)  # Max confidence at 10 occurrences
                strength = count / sequence_counts.most_common(1)[0][1]  # Relative to most common
                
                patterns.append(PatternCandidate(
                    pattern_type=BehaviorPatternType.COMMAND_SEQUENCE,
                    name=f"Command Chain: {' → '.join(sequence)}",
                    description=f"Frequently used sequence of {len(sequence)} commands (used {count} times)",
                    evidence=[f"Sequence: {' → '.join(sequence)}", f"Frequency: {count} times"],
                    confidence=confidence,
                    strength=strength,
                    pattern_data={
                        "sequence": list(sequence),
                        "frequency": count,
                        "sequence_length": len(sequence)
                    }
                ))
        
        return patterns
    
    def detect_workflow_patterns(self, commands: List[CommandUsage]) -> List[PatternCandidate]:
        """Detect higher-level workflow patterns"""
        patterns = []
        
        # Group by context
        context_commands = defaultdict(list)
        for cmd in commands:
            context_commands[cmd.context].append(cmd)
        
        for context, context_cmds in context_commands.items():
            if len(context_cmds) < 10:  # Need sufficient data
                continue
            
            # Analyze command categories within context
            category_counts = Counter([cmd.category for cmd in context_cmds])
            
            # Determine workflow type
            workflow_type = None
            description = ""
            
            if category_counts[CommandCategory.TOOL] > len(context_cmds) * 0.6:
                workflow_type = "Tool-Centric Workflow"
                description = f"Heavy tool usage in {context.value} context"
            elif category_counts[CommandCategory.AGENT] > len(context_cmds) * 0.4:
                workflow_type = "Agent-Assisted Workflow"
                description = f"Frequent agent delegation in {context.value} context"
            elif category_counts[CommandCategory.LLM] > len(context_cmds) * 0.5:
                workflow_type = "LLM-Driven Workflow"
                description = f"AI-first approach in {context.value} context"
            
            if workflow_type:
                patterns.append(PatternCandidate(
                    pattern_type=BehaviorPatternType.WORKFLOW,
                    name=f"{workflow_type} ({context.value.title()})",
                    description=description,
                    evidence=[f"{len(context_cmds)} commands in {context.value} context"],
                    confidence=min(len(context_cmds) / 50.0, 1.0),
                    strength=0.7,
                    pattern_data={
                        "context": context.value,
                        "command_count": len(context_cmds),
                        "category_distribution": dict(category_counts),
                        "workflow_type": workflow_type
                    }
                ))
        
        return patterns


class PreferencePatternDetector:
    """Detects user preference patterns"""
    
    def detect_tool_preferences(self, commands: List[CommandUsage]) -> List[PatternCandidate]:
        """Detect tool and feature preferences"""
        if len(commands) < 20:
            return []
        
        patterns = []
        
        # Command usage frequency
        command_counts = Counter([cmd.command for cmd in commands])
        total_commands = len(commands)
        
        for command, count in command_counts.most_common(10):
            usage_percentage = (count / total_commands) * 100
            
            if usage_percentage > 10:  # Command represents >10% of usage
                confidence = min(usage_percentage / 25.0, 1.0)
                strength = count / command_counts.most_common(1)[0][1]
                
                patterns.append(PatternCandidate(
                    pattern_type=BehaviorPatternType.TOOL_PREFERENCE,
                    name=f"Preferred Command: {command}",
                    description=f"Heavy usage of '{command}' command ({usage_percentage:.1f}% of total)",
                    evidence=[f"{count} uses out of {total_commands} total commands"],
                    confidence=confidence,
                    strength=strength,
                    pattern_data={
                        "command": command,
                        "usage_count": count,
                        "usage_percentage": usage_percentage
                    }
                ))
        
        # Category preferences
        category_counts = Counter([cmd.category for cmd in commands])
        
        for category, count in category_counts.most_common(3):
            usage_percentage = (count / total_commands) * 100
            
            if usage_percentage > 20:  # Category represents >20% of usage
                patterns.append(PatternCandidate(
                    pattern_type=BehaviorPatternType.TOOL_PREFERENCE,
                    name=f"Preferred Category: {category.value.title()}",
                    description=f"Strong preference for {category.value} commands ({usage_percentage:.1f}%)",
                    evidence=[f"{count} {category.value} commands"],
                    confidence=min(usage_percentage / 40.0, 1.0),
                    strength=count / category_counts.most_common(1)[0][1],
                    pattern_data={
                        "category": category.value,
                        "usage_count": count,
                        "usage_percentage": usage_percentage
                    }
                ))
        
        return patterns
    
    def detect_response_style_patterns(self, commands: List[CommandUsage]) -> List[PatternCandidate]:
        """Detect response style preferences from command patterns"""
        patterns = []
        
        # Analyze command complexity as indicator of technical level
        complex_commands = 0
        simple_commands = 0
        
        for cmd in commands:
            # Complex command indicators
            if (len(cmd.arguments) > 5 or 
                cmd.category in [CommandCategory.AUTOMATION, CommandCategory.AGENT] or
                any(word in cmd.command.lower() for word in ['analyze', 'debug', 'trace', 'profile'])):
                complex_commands += 1
            else:
                simple_commands += 1
        
        total = complex_commands + simple_commands
        if total > 10:
            complexity_ratio = complex_commands / total
            
            if complexity_ratio > 0.6:
                tech_level = "High Technical Preference"
                description = "Prefers complex, technical commands and features"
            elif complexity_ratio < 0.3:
                tech_level = "Simple Interface Preference"
                description = "Prefers straightforward, simple commands"
            else:
                tech_level = "Balanced Technical Approach"
                description = "Uses mix of simple and complex commands"
            
            patterns.append(PatternCandidate(
                pattern_type=BehaviorPatternType.RESPONSE_STYLE,
                name=tech_level,
                description=description,
                evidence=[f"{complex_commands} complex vs {simple_commands} simple commands"],
                confidence=min(total / 30.0, 1.0),
                strength=abs(complexity_ratio - 0.5) * 2,  # Distance from balanced
                pattern_data={
                    "complexity_ratio": complexity_ratio,
                    "complex_commands": complex_commands,
                    "simple_commands": simple_commands,
                    "technical_level_category": tech_level
                }
            ))
        
        return patterns


class ErrorPatternDetector:
    """Detects error and failure patterns"""
    
    def detect_error_patterns(self, commands: List[CommandUsage]) -> List[PatternCandidate]:
        """Detect patterns in user errors and failures"""
        failed_commands = [cmd for cmd in commands if not cmd.success]
        
        if len(failed_commands) < 5:  # Need some failures to detect patterns
            return []
        
        patterns = []
        total_commands = len(commands)
        error_rate = len(failed_commands) / total_commands
        
        # Overall error rate pattern
        if error_rate > 0.2:  # >20% error rate
            severity = "High Error Rate"
            description = f"Frequent command failures ({error_rate:.1%})"
        elif error_rate > 0.1:  # >10% error rate
            severity = "Moderate Error Rate" 
            description = f"Occasional command failures ({error_rate:.1%})"
        else:
            severity = "Low Error Rate"
            description = f"Rare command failures ({error_rate:.1%})"
        
        patterns.append(PatternCandidate(
            pattern_type=BehaviorPatternType.ERROR_PATTERN,
            name=severity,
            description=description,
            evidence=[f"{len(failed_commands)} failures out of {total_commands} commands"],
            confidence=min(total_commands / 50.0, 1.0),
            strength=error_rate,
            pattern_data={
                "error_rate": error_rate,
                "failed_commands": len(failed_commands),
                "total_commands": total_commands,
                "severity": severity
            }
        ))
        
        # Specific error type patterns
        error_messages = [cmd.error_message for cmd in failed_commands if cmd.error_message]
        if error_messages:
            error_types = defaultdict(int)
            
            for error_msg in error_messages:
                error_lower = error_msg.lower()
                if "timeout" in error_lower:
                    error_types["timeout"] += 1
                elif "permission" in error_lower or "access" in error_lower:
                    error_types["permission"] += 1
                elif "not found" in error_lower:
                    error_types["not_found"] += 1
                elif "syntax" in error_lower or "invalid" in error_lower:
                    error_types["syntax"] += 1
                else:
                    error_types["other"] += 1
            
            for error_type, count in error_types.items():
                if count >= 3:  # At least 3 occurrences
                    patterns.append(PatternCandidate(
                        pattern_type=BehaviorPatternType.ERROR_PATTERN,
                        name=f"Recurring {error_type.title()} Errors",
                        description=f"Pattern of {error_type} errors ({count} occurrences)",
                        evidence=[f"{count} {error_type} errors"],
                        confidence=min(count / 10.0, 1.0),
                        strength=count / len(failed_commands),
                        pattern_data={
                            "error_type": error_type,
                            "occurrence_count": count,
                            "error_frequency": count / len(failed_commands)
                        }
                    ))
        
        return patterns


class UsageFrequencyDetector:
    """Detects usage frequency and intensity patterns"""
    
    def detect_usage_intensity_patterns(self, sessions: List[UsageSession]) -> List[PatternCandidate]:
        """Detect overall usage intensity patterns"""
        if len(sessions) < 5:
            return []
        
        patterns = []
        
        # Calculate usage metrics
        total_commands = sum(s.total_commands for s in sessions)
        avg_commands_per_session = total_commands / len(sessions) if sessions else 0
        
        # Session frequency (sessions per week)
        if sessions:
            date_range = max(s.start_time for s in sessions) - min(s.start_time for s in sessions)
            weeks = max(date_range.days / 7, 1)
            sessions_per_week = len(sessions) / weeks
        else:
            sessions_per_week = 0
        
        # Determine usage intensity
        if avg_commands_per_session > 50 and sessions_per_week > 5:
            intensity = "Power User"
            description = f"High-intensity usage ({avg_commands_per_session:.1f} cmds/session, {sessions_per_week:.1f} sessions/week)"
        elif avg_commands_per_session > 20 and sessions_per_week > 3:
            intensity = "Regular User"
            description = f"Consistent regular usage ({avg_commands_per_session:.1f} cmds/session, {sessions_per_week:.1f} sessions/week)"
        elif avg_commands_per_session > 10:
            intensity = "Moderate User"
            description = f"Moderate usage pattern ({avg_commands_per_session:.1f} cmds/session, {sessions_per_week:.1f} sessions/week)"
        else:
            intensity = "Light User"
            description = f"Light usage pattern ({avg_commands_per_session:.1f} cmds/session, {sessions_per_week:.1f} sessions/week)"
        
        patterns.append(PatternCandidate(
            pattern_type=BehaviorPatternType.USAGE_FREQUENCY,
            name=intensity,
            description=description,
            evidence=[f"{total_commands} total commands in {len(sessions)} sessions"],
            confidence=min(len(sessions) / 10.0, 1.0),
            strength=min((avg_commands_per_session + sessions_per_week) / 20, 1.0),
            pattern_data={
                "intensity_category": intensity,
                "avg_commands_per_session": avg_commands_per_session,
                "sessions_per_week": sessions_per_week,
                "total_commands": total_commands,
                "total_sessions": len(sessions)
            }
        ))
        
        return patterns


class BehaviorDetector:
    """Main behavior pattern detection system"""
    
    def __init__(self, storage_backend=None):
        self.storage = storage_backend
        
        # Pattern detectors
        self.time_detector = TimePatternDetector()
        self.sequence_detector = CommandSequenceDetector()
        self.preference_detector = PreferencePatternDetector()
        self.error_detector = ErrorPatternDetector()
        self.frequency_detector = UsageFrequencyDetector()
        
        # Detection configuration
        self.min_confidence_threshold = 0.5
        self.min_strength_threshold = 0.3
        self.max_patterns_per_type = 5
        
        # Pattern validation
        self.detected_patterns: Dict[str, List[BehaviorPattern]] = defaultdict(list)
        self.pattern_validation_history = defaultdict(list)
        
        logger.info("BehaviorDetector initialized")
    
    async def detect_user_patterns(self, user_id: str, days: int = 30) -> List[BehaviorPattern]:
        """Detect all behavior patterns for a user"""
        try:
            if not self.storage:
                logger.warning("No storage backend available for pattern detection")
                return []
            
            # Get user data
            commands = await self.storage.get_user_command_history(user_id, days=days)
            sessions = await self.storage.get_user_sessions(user_id, days=days)
            
            if len(commands) < 10:  # Need minimum data
                logger.info(f"Insufficient data for pattern detection: {len(commands)} commands")
                return []
            
            # Detect patterns using all detectors
            pattern_candidates = []
            
            # Time-based patterns
            pattern_candidates.extend(self.time_detector.detect_peak_usage_times(commands))
            pattern_candidates.extend(self.time_detector.detect_session_timing_patterns(sessions))
            
            # Command sequence patterns
            pattern_candidates.extend(self.sequence_detector.detect_command_chains(commands))
            pattern_candidates.extend(self.sequence_detector.detect_workflow_patterns(commands))
            
            # Preference patterns
            pattern_candidates.extend(self.preference_detector.detect_tool_preferences(commands))
            pattern_candidates.extend(self.preference_detector.detect_response_style_patterns(commands))
            
            # Error patterns
            pattern_candidates.extend(self.error_detector.detect_error_patterns(commands))
            
            # Usage frequency patterns
            pattern_candidates.extend(self.frequency_detector.detect_usage_intensity_patterns(sessions))
            
            # Filter and validate patterns
            validated_patterns = self._validate_patterns(user_id, pattern_candidates)
            
            # Convert to BehaviorPattern objects
            behavior_patterns = []
            for candidate in validated_patterns:
                pattern = BehaviorPattern(
                    user_id=user_id,
                    pattern_type=candidate.pattern_type,
                    pattern_name=candidate.name,
                    description=candidate.description,
                    confidence_score=candidate.confidence,
                    strength=candidate.strength,
                    pattern_data=candidate.pattern_data,
                    examples=candidate.evidence[:3]  # First 3 evidence items
                )
                behavior_patterns.append(pattern)
            
            # Store patterns
            self.detected_patterns[user_id] = behavior_patterns
            
            # Save to storage
            if self.storage:
                for pattern in behavior_patterns:
                    await self.storage.store_behavior_pattern(pattern)
            
            logger.info(f"Detected {len(behavior_patterns)} patterns for user {user_id}")
            return behavior_patterns
            
        except Exception as e:
            logger.error(f"Error detecting patterns for user {user_id}: {e}")
            return []
    
    def _validate_patterns(self, user_id: str, candidates: List[PatternCandidate]) -> List[PatternCandidate]:
        """Validate pattern candidates based on thresholds and history"""
        validated = []
        
        # Group by pattern type
        patterns_by_type = defaultdict(list)
        for candidate in candidates:
            patterns_by_type[candidate.pattern_type].append(candidate)
        
        # Validate each type
        for pattern_type, type_candidates in patterns_by_type.items():
            # Sort by confidence and strength
            type_candidates.sort(key=lambda x: (x.confidence * x.strength), reverse=True)
            
            # Take top patterns for each type
            for candidate in type_candidates[:self.max_patterns_per_type]:
                if (candidate.confidence >= self.min_confidence_threshold and 
                    candidate.strength >= self.min_strength_threshold):
                    
                    # Check against history to avoid duplicates
                    if not self._is_duplicate_pattern(user_id, candidate):
                        validated.append(candidate)
        
        return validated
    
    def _is_duplicate_pattern(self, user_id: str, candidate: PatternCandidate) -> bool:
        """Check if pattern is duplicate of existing pattern"""
        existing_patterns = self.detected_patterns.get(user_id, [])
        
        for existing in existing_patterns:
            if (existing.pattern_type == candidate.pattern_type and
                existing.pattern_name == candidate.name):
                return True
        
        return False
    
    async def update_pattern_validation(self, user_id: str, pattern_id: str, is_valid: bool):
        """Update pattern validation based on user feedback"""
        try:
            # Record validation
            self.pattern_validation_history[user_id].append({
                'pattern_id': pattern_id,
                'is_valid': is_valid,
                'timestamp': datetime.utcnow()
            })
            
            # Update pattern status if stored
            if self.storage:
                await self.storage.update_pattern_validation(pattern_id, is_valid)
                
            logger.info(f"Updated pattern {pattern_id} validation: {is_valid}")
            
        except Exception as e:
            logger.error(f"Error updating pattern validation: {e}")
    
    def get_user_patterns(self, user_id: str, pattern_type: Optional[BehaviorPatternType] = None) -> List[BehaviorPattern]:
        """Get detected patterns for a user"""
        patterns = self.detected_patterns.get(user_id, [])
        
        if pattern_type:
            patterns = [p for p in patterns if p.pattern_type == pattern_type]
        
        # Sort by strength and confidence
        patterns.sort(key=lambda x: (x.confidence_score * x.strength), reverse=True)
        return patterns
    
    def get_pattern_summary(self, user_id: str) -> Dict[str, Any]:
        """Get summary of detected patterns for a user"""
        patterns = self.detected_patterns.get(user_id, [])
        
        if not patterns:
            return {"total_patterns": 0, "pattern_types": {}}
        
        # Count by type
        type_counts = Counter([p.pattern_type.value for p in patterns])
        
        # Get top patterns
        top_patterns = sorted(patterns, key=lambda x: x.confidence_score, reverse=True)[:5]
        
        # Calculate average confidence
        avg_confidence = statistics.mean([p.confidence_score for p in patterns])
        
        return {
            "total_patterns": len(patterns),
            "pattern_types": dict(type_counts),
            "average_confidence": avg_confidence,
            "top_patterns": [
                {
                    "name": p.pattern_name,
                    "type": p.pattern_type.value,
                    "confidence": p.confidence_score,
                    "description": p.description
                } for p in top_patterns
            ],
            "last_detection": max(p.first_observed for p in patterns) if patterns else None
        }
    
    async def refresh_patterns(self, user_id: str, days: int = 30) -> int:
        """Refresh patterns for a user (re-run detection)"""
        # Clear existing patterns
        if user_id in self.detected_patterns:
            del self.detected_patterns[user_id]
        
        # Re-detect patterns
        new_patterns = await self.detect_user_patterns(user_id, days)
        
        return len(new_patterns)
    
    def set_detection_thresholds(self, confidence_threshold: float, strength_threshold: float):
        """Update detection thresholds"""
        self.min_confidence_threshold = max(0.0, min(1.0, confidence_threshold))
        self.min_strength_threshold = max(0.0, min(1.0, strength_threshold))
        
        logger.info(f"Updated detection thresholds: confidence={confidence_threshold}, strength={strength_threshold}")
    
    def get_detection_stats(self) -> Dict[str, Any]:
        """Get statistics about pattern detection"""
        total_patterns = sum(len(patterns) for patterns in self.detected_patterns.values())
        total_users = len(self.detected_patterns)
        
        if total_users == 0:
            return {"total_users": 0, "total_patterns": 0}
        
        avg_patterns_per_user = total_patterns / total_users
        
        # Count patterns by type
        all_patterns = []
        for patterns in self.detected_patterns.values():
            all_patterns.extend(patterns)
        
        type_distribution = Counter([p.pattern_type.value for p in all_patterns])
        
        return {
            "total_users": total_users,
            "total_patterns": total_patterns,
            "avg_patterns_per_user": avg_patterns_per_user,
            "pattern_type_distribution": dict(type_distribution),
            "confidence_threshold": self.min_confidence_threshold,
            "strength_threshold": self.min_strength_threshold
        }


# Export main class
__all__ = ["BehaviorDetector", "PatternCandidate"]