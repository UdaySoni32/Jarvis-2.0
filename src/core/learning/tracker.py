"""
JARVIS 2.0 User Preference Tracker

Tracks and manages user preferences automatically by observing user behavior,
explicit settings, and interaction patterns. Provides intelligent preference
inference and adaptive learning capabilities.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import logging
from collections import defaultdict, Counter
import json

from .schemas import (
    UserPreferences, ResponseStyle, TimePreferences, ToolPreferences,
    PreferenceSource, ResponseTone, ResponseVerbosity, CommandUsage,
    UsageSession, CommandCategory, UsageContext
)

logger = logging.getLogger(__name__)


class PreferenceInferenceEngine:
    """Infers user preferences from behavior patterns"""
    
    def __init__(self):
        self.inference_rules = {
            'response_tone': self._infer_response_tone,
            'response_verbosity': self._infer_response_verbosity,
            'technical_level': self._infer_technical_level,
            'preferred_tools': self._infer_preferred_tools,
            'active_hours': self._infer_active_hours,
            'usage_contexts': self._infer_usage_contexts
        }
    
    def _infer_response_tone(self, command_history: List[CommandUsage]) -> Tuple[ResponseTone, float]:
        """Infer preferred response tone from user interactions"""
        tone_indicators = {
            ResponseTone.TECHNICAL: ['debug', 'analyze', 'trace', 'profile', 'benchmark'],
            ResponseTone.CASUAL: ['help', 'what', 'how', 'simple', 'quick'],
            ResponseTone.PROFESSIONAL: ['report', 'summary', 'analysis', 'generate'],
            ResponseTone.CONCISE: ['list', 'show', 'brief', 'short']
        }
        
        tone_scores = defaultdict(int)
        
        for usage in command_history[-100:]:  # Last 100 commands
            command_lower = usage.command.lower()
            for tone, indicators in tone_indicators.items():
                if any(indicator in command_lower for indicator in indicators):
                    tone_scores[tone] += 1
        
        if not tone_scores:
            return ResponseTone.FRIENDLY, 0.0
        
        best_tone = max(tone_scores, key=tone_scores.get)
        total_commands = len(command_history[-100:])
        confidence = tone_scores[best_tone] / total_commands if total_commands > 0 else 0.0
        
        return best_tone, min(confidence * 2, 1.0)  # Scale confidence
    
    def _infer_response_verbosity(self, command_history: List[CommandUsage]) -> Tuple[ResponseVerbosity, float]:
        """Infer preferred response verbosity from command complexity"""
        verbosity_indicators = {
            ResponseVerbosity.MINIMAL: ['ls', 'pwd', 'status', 'list'],
            ResponseVerbosity.BRIEF: ['help', 'info', 'show'],
            ResponseVerbosity.DETAILED: ['explain', 'analyze', 'describe', 'documentation'],
            ResponseVerbosity.COMPREHENSIVE: ['tutorial', 'guide', 'complete', 'full']
        }
        
        verbosity_scores = defaultdict(int)
        
        for usage in command_history[-50:]:  # Last 50 commands
            command_lower = usage.command.lower()
            # Check for explicit verbosity requests
            for verbosity, indicators in verbosity_indicators.items():
                if any(indicator in command_lower for indicator in indicators):
                    verbosity_scores[verbosity] += 1
            
            # Infer from command complexity
            if len(usage.arguments) > 5:
                verbosity_scores[ResponseVerbosity.DETAILED] += 1
            elif len(usage.arguments) <= 2:
                verbosity_scores[ResponseVerbosity.BRIEF] += 1
        
        if not verbosity_scores:
            return ResponseVerbosity.NORMAL, 0.0
        
        best_verbosity = max(verbosity_scores, key=verbosity_scores.get)
        total_relevant = sum(verbosity_scores.values())
        confidence = verbosity_scores[best_verbosity] / total_relevant if total_relevant > 0 else 0.0
        
        return best_verbosity, min(confidence * 1.5, 1.0)
    
    def _infer_technical_level(self, command_history: List[CommandUsage]) -> Tuple[int, float]:
        """Infer technical expertise level from command usage"""
        technical_indicators = {
            1: ['help', 'what', 'how', 'tutorial', 'guide'],  # Beginner
            2: ['list', 'show', 'info', 'basic'],             # Novice
            3: ['create', 'update', 'manage', 'configure'],    # Intermediate
            4: ['analyze', 'optimize', 'debug', 'advanced'],   # Advanced
            5: ['trace', 'profile', 'benchmark', 'custom']     # Expert
        }
        
        level_scores = defaultdict(int)
        
        for usage in command_history[-100:]:
            command_lower = usage.command.lower()
            for level, indicators in technical_indicators.items():
                if any(indicator in command_lower for indicator in indicators):
                    level_scores[level] += 1
            
            # Advanced usage patterns
            if usage.category in [CommandCategory.AUTOMATION, CommandCategory.AGENT]:
                level_scores[4] += 1
            if len(usage.arguments) > 8:
                level_scores[5] += 1
        
        if not level_scores:
            return 3, 0.0  # Default to intermediate
        
        # Weighted average technical level
        total_weight = sum(level_scores.values())
        weighted_level = sum(level * count for level, count in level_scores.items()) / total_weight
        
        # Confidence based on sample size and consistency
        confidence = min(total_weight / 50.0, 1.0)  # More confident with more data
        
        return round(weighted_level), confidence
    
    def _infer_preferred_tools(self, command_history: List[CommandUsage]) -> Tuple[Dict[str, str], float]:
        """Infer preferred tools from usage patterns"""
        tool_usage = Counter()
        category_usage = Counter()
        
        for usage in command_history[-200:]:  # Last 200 commands
            if usage.success:  # Only count successful usage
                tool_usage[usage.command] += 1
                category_usage[usage.category] += 1
        
        preferences = {}
        
        # Most used LLM models (if tracked)
        if 'llm' in [usage.command for usage in command_history[-50:]]:
            # This would need integration with LLM usage tracking
            preferences['preferred_llm_model'] = 'gpt-4'  # Default
        
        # Most used command categories
        if category_usage:
            top_category = category_usage.most_common(1)[0][0]
            if top_category == CommandCategory.TOOL:
                preferences['preferred_interaction_style'] = 'tool_focused'
            elif top_category == CommandCategory.AGENT:
                preferences['preferred_interaction_style'] = 'agent_focused'
            elif top_category == CommandCategory.LLM:
                preferences['preferred_interaction_style'] = 'llm_focused'
        
        # Programming language preferences
        code_commands = [usage for usage in command_history[-100:] 
                        if 'code' in usage.command.lower() or 'script' in usage.command.lower()]
        if code_commands:
            # Would need to analyze actual code content
            preferences['preferred_code_language'] = 'python'  # Most common
        
        confidence = min(len(command_history) / 100.0, 1.0)
        return preferences, confidence
    
    def _infer_active_hours(self, sessions: List[UsageSession]) -> Tuple[Dict[str, Any], float]:
        """Infer active hours from session timing"""
        if not sessions:
            return {}, 0.0
        
        # Collect session start hours
        start_hours = [session.start_time.hour for session in sessions]
        hour_counter = Counter(start_hours)
        
        # Find peak hours (most common start times)
        if len(hour_counter) >= 5:  # Need sufficient data
            peak_hours = [hour for hour, count in hour_counter.most_common(3)]
            
            # Infer active period
            active_start = min(peak_hours)
            active_end = max(peak_hours) + 1  # Add buffer
            
            # Check for weekend patterns
            weekend_sessions = [s for s in sessions 
                              if s.start_time.weekday() >= 5]  # Sat, Sun = 5, 6
            weekend_ratio = len(weekend_sessions) / len(sessions)
            
            preferences = {
                'active_hours_start': f"{active_start:02d}:00",
                'active_hours_end': f"{active_end:02d}:00",
                'weekend_mode': weekend_ratio > 0.3  # 30%+ weekend usage
            }
            
            confidence = min(len(sessions) / 20.0, 1.0)  # More confident with more sessions
            return preferences, confidence
        
        return {}, 0.0
    
    def _infer_usage_contexts(self, command_history: List[CommandUsage]) -> Tuple[List[UsageContext], float]:
        """Infer primary usage contexts"""
        context_counter = Counter([usage.context for usage in command_history[-100:]])
        
        if not context_counter:
            return [UsageContext.PERSONAL], 0.0
        
        # Get contexts that represent >20% of usage
        total_usage = sum(context_counter.values())
        primary_contexts = [
            context for context, count in context_counter.items()
            if count / total_usage > 0.2
        ]
        
        confidence = min(len(command_history) / 50.0, 1.0)
        return primary_contexts, confidence


class PreferenceTracker:
    """Main preference tracking system"""
    
    def __init__(self, storage_backend=None):
        self.storage = storage_backend
        self.inference_engine = PreferenceInferenceEngine()
        self.user_preferences: Dict[str, UserPreferences] = {}
        self.tracking_enabled = True
        self.auto_inference_enabled = True
        
        # Tracking thresholds
        self.min_commands_for_inference = 10
        self.inference_interval_hours = 24
        self.confidence_threshold = 0.6
        
        # Last inference timestamps
        self.last_inference: Dict[str, datetime] = {}
        
        logger.info("PreferenceTracker initialized")
    
    async def track_command_usage(self, user_id: str, command_usage: CommandUsage):
        """Track a command usage for preference learning"""
        if not self.tracking_enabled:
            return
        
        try:
            # Store command usage
            if self.storage:
                await self.storage.store_command_usage(command_usage)
            
            # Check if we should run inference
            should_infer = self._should_run_inference(user_id)
            if should_infer:
                await self._run_preference_inference(user_id)
                
        except Exception as e:
            logger.error(f"Error tracking command usage: {e}")
    
    async def track_user_feedback(self, user_id: str, command_id: str, feedback: str, rating: Optional[int] = None):
        """Track explicit user feedback on commands"""
        try:
            if self.storage:
                await self.storage.update_command_feedback(command_id, feedback, rating)
            
            # Use feedback to adjust preferences
            await self._process_user_feedback(user_id, feedback, rating)
            
        except Exception as e:
            logger.error(f"Error tracking user feedback: {e}")
    
    def set_explicit_preference(self, user_id: str, category: str, key: str, value: Any):
        """Set an explicit user preference"""
        try:
            preferences = self._get_or_create_preferences(user_id)
            preferences.update_preference(category, key, value, PreferenceSource.USER_EXPLICIT)
            
            self.user_preferences[user_id] = preferences
            
            if self.storage:
                asyncio.create_task(self.storage.store_user_preferences(preferences))
            
            logger.info(f"Set explicit preference for {user_id}: {category}.{key} = {value}")
            
        except Exception as e:
            logger.error(f"Error setting explicit preference: {e}")
    
    def get_user_preferences(self, user_id: str) -> UserPreferences:
        """Get current user preferences"""
        if user_id in self.user_preferences:
            return self.user_preferences[user_id]
        
        # Try loading from storage
        if self.storage:
            try:
                stored_prefs = asyncio.run(self.storage.load_user_preferences(user_id))
                if stored_prefs:
                    self.user_preferences[user_id] = stored_prefs
                    return stored_prefs
            except Exception as e:
                logger.error(f"Error loading preferences from storage: {e}")
        
        # Create default preferences
        return self._get_or_create_preferences(user_id)
    
    async def _run_preference_inference(self, user_id: str):
        """Run preference inference for a user"""
        try:
            if not self.storage:
                return
            
            # Get recent command history
            command_history = await self.storage.get_user_command_history(
                user_id, limit=200, days=30
            )
            
            if len(command_history) < self.min_commands_for_inference:
                return
            
            # Get user sessions for time-based inference
            sessions = await self.storage.get_user_sessions(user_id, days=30)
            
            # Run inference
            preferences = self._get_or_create_preferences(user_id)
            updated = False
            
            # Infer response tone
            tone, tone_conf = self.inference_engine._infer_response_tone(command_history)
            if tone_conf >= self.confidence_threshold:
                if preferences.response_style.tone != tone:
                    preferences.update_preference(
                        "response_style", "tone", tone, 
                        PreferenceSource.BEHAVIOR_INFERRED
                    )
                    updated = True
                    logger.info(f"Inferred response tone for {user_id}: {tone} (confidence: {tone_conf:.2f})")
            
            # Infer verbosity
            verbosity, verb_conf = self.inference_engine._infer_response_verbosity(command_history)
            if verb_conf >= self.confidence_threshold:
                if preferences.response_style.verbosity != verbosity:
                    preferences.update_preference(
                        "response_style", "verbosity", verbosity,
                        PreferenceSource.BEHAVIOR_INFERRED
                    )
                    updated = True
                    logger.info(f"Inferred verbosity for {user_id}: {verbosity} (confidence: {verb_conf:.2f})")
            
            # Infer technical level
            tech_level, tech_conf = self.inference_engine._infer_technical_level(command_history)
            if tech_conf >= self.confidence_threshold:
                if preferences.response_style.technical_level != tech_level:
                    preferences.update_preference(
                        "response_style", "technical_level", tech_level,
                        PreferenceSource.BEHAVIOR_INFERRED
                    )
                    updated = True
                    logger.info(f"Inferred technical level for {user_id}: {tech_level} (confidence: {tech_conf:.2f})")
            
            # Infer active hours
            time_prefs, time_conf = self.inference_engine._infer_active_hours(sessions)
            if time_conf >= self.confidence_threshold and time_prefs:
                for key, value in time_prefs.items():
                    preferences.update_preference(
                        "time_preferences", key, value,
                        PreferenceSource.BEHAVIOR_INFERRED
                    )
                updated = True
                logger.info(f"Inferred time preferences for {user_id}: {time_prefs}")
            
            # Save updated preferences
            if updated:
                self.user_preferences[user_id] = preferences
                await self.storage.store_user_preferences(preferences)
            
            # Update inference timestamp
            self.last_inference[user_id] = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"Error running preference inference for {user_id}: {e}")
    
    def _should_run_inference(self, user_id: str) -> bool:
        """Check if preference inference should be run"""
        if not self.auto_inference_enabled:
            return False
        
        last_run = self.last_inference.get(user_id)
        if not last_run:
            return True
        
        hours_since_last = (datetime.utcnow() - last_run).total_seconds() / 3600
        return hours_since_last >= self.inference_interval_hours
    
    async def _process_user_feedback(self, user_id: str, feedback: str, rating: Optional[int]):
        """Process user feedback to adjust preferences"""
        try:
            preferences = self._get_or_create_preferences(user_id)
            
            # Adjust preferences based on feedback
            if feedback == "too_verbose":
                current_verbosity = preferences.response_style.verbosity
                if current_verbosity != ResponseVerbosity.MINIMAL:
                    new_verbosity = {
                        ResponseVerbosity.COMPREHENSIVE: ResponseVerbosity.DETAILED,
                        ResponseVerbosity.DETAILED: ResponseVerbosity.NORMAL,
                        ResponseVerbosity.NORMAL: ResponseVerbosity.BRIEF,
                        ResponseVerbosity.BRIEF: ResponseVerbosity.MINIMAL
                    }.get(current_verbosity, ResponseVerbosity.BRIEF)
                    
                    preferences.update_preference(
                        "response_style", "verbosity", new_verbosity,
                        PreferenceSource.USER_EXPLICIT
                    )
            
            elif feedback == "too_brief":
                current_verbosity = preferences.response_style.verbosity
                if current_verbosity != ResponseVerbosity.COMPREHENSIVE:
                    new_verbosity = {
                        ResponseVerbosity.MINIMAL: ResponseVerbosity.BRIEF,
                        ResponseVerbosity.BRIEF: ResponseVerbosity.NORMAL,
                        ResponseVerbosity.NORMAL: ResponseVerbosity.DETAILED,
                        ResponseVerbosity.DETAILED: ResponseVerbosity.COMPREHENSIVE
                    }.get(current_verbosity, ResponseVerbosity.DETAILED)
                    
                    preferences.update_preference(
                        "response_style", "verbosity", new_verbosity,
                        PreferenceSource.USER_EXPLICIT
                    )
            
            elif feedback == "too_technical":
                current_level = preferences.response_style.technical_level
                if current_level > 1:
                    preferences.update_preference(
                        "response_style", "technical_level", current_level - 1,
                        PreferenceSource.USER_EXPLICIT
                    )
            
            elif feedback == "too_simple":
                current_level = preferences.response_style.technical_level
                if current_level < 5:
                    preferences.update_preference(
                        "response_style", "technical_level", current_level + 1,
                        PreferenceSource.USER_EXPLICIT
                    )
            
            # Save updated preferences
            self.user_preferences[user_id] = preferences
            if self.storage:
                await self.storage.store_user_preferences(preferences)
            
            logger.info(f"Processed feedback for {user_id}: {feedback}")
            
        except Exception as e:
            logger.error(f"Error processing user feedback: {e}")
    
    def _get_or_create_preferences(self, user_id: str) -> UserPreferences:
        """Get existing preferences or create new ones"""
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = UserPreferences(user_id=user_id)
        return self.user_preferences[user_id]
    
    def get_preference_summary(self, user_id: str) -> Dict[str, Any]:
        """Get a summary of user preferences for display"""
        preferences = self.get_user_preferences(user_id)
        
        return {
            "user_id": user_id,
            "response_style": {
                "tone": preferences.response_style.tone.value,
                "verbosity": preferences.response_style.verbosity.value,
                "technical_level": preferences.response_style.technical_level,
                "include_explanations": preferences.response_style.include_explanations,
                "use_emojis": preferences.response_style.use_emojis
            },
            "tool_preferences": {
                "preferred_llm_model": preferences.tool_preferences.preferred_llm_model,
                "automation_enabled": preferences.tool_preferences.automation_enabled,
                "suggestion_frequency": preferences.tool_preferences.suggestion_frequency
            },
            "time_preferences": {
                "timezone": preferences.time_preferences.timezone,
                "active_hours": f"{preferences.time_preferences.active_hours_start} - {preferences.time_preferences.active_hours_end}",
                "weekend_mode": preferences.time_preferences.weekend_mode
            },
            "privacy_settings": {
                "collect_usage_data": preferences.privacy_settings.collect_usage_data,
                "data_retention_days": preferences.privacy_settings.data_retention_days
            },
            "custom_preferences": len(preferences.custom_preferences),
            "last_updated": preferences.updated_at.isoformat(),
            "version": preferences.version
        }
    
    def enable_tracking(self):
        """Enable preference tracking"""
        self.tracking_enabled = True
        logger.info("Preference tracking enabled")
    
    def disable_tracking(self):
        """Disable preference tracking"""
        self.tracking_enabled = False
        logger.info("Preference tracking disabled")
    
    def enable_auto_inference(self):
        """Enable automatic preference inference"""
        self.auto_inference_enabled = True
        logger.info("Automatic preference inference enabled")
    
    def disable_auto_inference(self):
        """Disable automatic preference inference"""
        self.auto_inference_enabled = False
        logger.info("Automatic preference inference disabled")


# Export main class
__all__ = ["PreferenceTracker", "PreferenceInferenceEngine"]