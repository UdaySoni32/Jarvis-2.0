"""
JARVIS 2.0 Personalization Engine

Advanced personalization system that adapts JARVIS behavior based on user
preferences, detected patterns, and interaction history. Provides context-aware
responses and proactive assistance tailored to individual users.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
import logging
from collections import defaultdict, deque
import json
import random

from .schemas import (
    UserProfile, UserPreferences, BehaviorPattern, BehaviorPatternType,
    ResponseStyle, ResponseTone, ResponseVerbosity, PersonalizationSettings,
    CommandCategory, UsageContext, PreferenceSource
)

logger = logging.getLogger(__name__)


class ResponsePersonalizer:
    """Personalizes response content and style based on user preferences"""
    
    def __init__(self):
        self.tone_templates = {
            ResponseTone.CASUAL: {
                "greeting": ["Hey!", "Hi there!", "What's up?"],
                "confirmation": ["Got it!", "Sure thing!", "No problem!"],
                "error": ["Oops!", "Hmm, that didn't work.", "Something went wrong."],
                "success": ["Nice!", "All done!", "Perfect!"]
            },
            ResponseTone.PROFESSIONAL: {
                "greeting": ["Hello.", "Good morning.", "Greetings."],
                "confirmation": ["Understood.", "Confirmed.", "Acknowledged."],
                "error": ["An error occurred.", "Unable to complete request.", "Processing failed."],
                "success": ["Task completed successfully.", "Operation successful.", "Completed."]
            },
            ResponseTone.FRIENDLY: {
                "greeting": ["Hello!", "Hi!", "Good to see you!"],
                "confirmation": ["Absolutely!", "Will do!", "Happy to help!"],
                "error": ["Sorry about that!", "Let me help fix this.", "Encountered an issue."],
                "success": ["Great job!", "All set!", "Successfully completed!"]
            },
            ResponseTone.TECHNICAL: {
                "greeting": ["System ready.", "Interface active.", "Ready for commands."],
                "confirmation": ["Command queued.", "Processing initiated.", "Parameters accepted."],
                "error": ["Error code detected.", "Exception thrown.", "Failure condition met."],
                "success": ["Execution complete.", "Process terminated successfully.", "Exit code 0."]
            },
            ResponseTone.CONCISE: {
                "greeting": ["Ready."],
                "confirmation": ["OK."],
                "error": ["Error."],
                "success": ["Done."]
            }
        }
    
    def personalize_response(self, base_response: str, user_preferences: UserPreferences,
                           response_type: str = "general") -> str:
        """Personalize a response based on user preferences"""
        try:
            style = user_preferences.response_style
            
            # Apply tone personalization
            if response_type in self.tone_templates.get(style.tone, {}):
                tone_options = self.tone_templates[style.tone][response_type]
                tone_prefix = random.choice(tone_options)
                base_response = f"{tone_prefix} {base_response}"
            
            # Apply verbosity adjustments
            if style.verbosity == ResponseVerbosity.MINIMAL:
                # Strip extra explanations, keep core info
                sentences = base_response.split('. ')
                base_response = sentences[0] + ('.' if len(sentences) > 1 else '')
            elif style.verbosity == ResponseVerbosity.DETAILED:
                # Add helpful context
                if not style.include_explanations:
                    pass  # Keep as is
                else:
                    base_response += self._add_helpful_context(base_response, style.technical_level)
            elif style.verbosity == ResponseVerbosity.COMPREHENSIVE:
                # Add examples and detailed explanations
                base_response += self._add_comprehensive_details(base_response, style.technical_level)
            
            # Apply technical level adjustments
            if style.technical_level <= 2:  # Beginner/Novice
                base_response = self._simplify_technical_language(base_response)
            elif style.technical_level >= 4:  # Advanced/Expert
                base_response = self._add_technical_details(base_response)
            
            # Add examples if requested
            if style.include_examples and "example" not in base_response.lower():
                base_response += self._generate_relevant_example(base_response)
            
            # Add emojis if enabled
            if style.use_emojis:
                base_response = self._add_contextual_emojis(base_response, response_type)
            
            return base_response.strip()
            
        except Exception as e:
            logger.error(f"Error personalizing response: {e}")
            return base_response
    
    def _add_helpful_context(self, response: str, tech_level: int) -> str:
        """Add helpful context based on technical level"""
        if tech_level <= 2:
            return f"\n\nTip: You can ask for more help or examples if needed!"
        elif tech_level >= 4:
            return f"\n\nFor more advanced options, try using additional parameters or flags."
        else:
            return f"\n\nLet me know if you need more details or have questions!"
    
    def _add_comprehensive_details(self, response: str, tech_level: int) -> str:
        """Add comprehensive details and examples"""
        additions = []
        
        if "command" in response.lower():
            additions.append("\n\nRelated commands you might find useful:")
            additions.append("• Use 'help <command>' for detailed information")
            additions.append("• Try 'history' to see recent commands")
        
        if "error" in response.lower():
            additions.append("\n\nTroubleshooting steps:")
            additions.append("• Check the command syntax")
            additions.append("• Verify required parameters are provided")
            additions.append("• Use 'debug' mode for more information")
        
        return "".join(additions)
    
    def _simplify_technical_language(self, response: str) -> str:
        """Simplify technical language for beginners"""
        replacements = {
            "execute": "run",
            "initialize": "start",
            "terminate": "stop",
            "parameter": "setting",
            "configuration": "setup",
            "authentication": "login",
            "implementation": "way to do it"
        }
        
        for technical, simple in replacements.items():
            response = response.replace(technical, simple)
        
        return response
    
    def _add_technical_details(self, response: str) -> str:
        """Add technical details for advanced users"""
        if "completed" in response.lower():
            return response + " (Process executed with exit status 0)"
        elif "failed" in response.lower():
            return response + " (Check system logs for detailed error information)"
        else:
            return response
    
    def _generate_relevant_example(self, response: str) -> str:
        """Generate relevant example based on response content"""
        if "command" in response.lower():
            return f"\n\nExample: jarvis help tools"
        elif "search" in response.lower():
            return f"\n\nExample: search for 'python tutorial'"
        elif "create" in response.lower():
            return f"\n\nExample: create file example.txt"
        else:
            return ""
    
    def _add_contextual_emojis(self, response: str, response_type: str) -> str:
        """Add contextual emojis based on response type"""
        emoji_map = {
            "success": "✅",
            "error": "❌", 
            "general": "💡",
            "greeting": "👋",
            "confirmation": "👍"
        }
        
        emoji = emoji_map.get(response_type, "")
        if emoji and not any(e in response for e in ["✅", "❌", "💡", "👋", "👍"]):
            return f"{emoji} {response}"
        
        return response


class SuggestionEngine:
    """Generates personalized suggestions and proactive assistance"""
    
    def __init__(self):
        self.suggestion_patterns = {
            BehaviorPatternType.COMMAND_SEQUENCE: self._suggest_workflow_automation,
            BehaviorPatternType.TIME_BASED: self._suggest_time_based_automation,
            BehaviorPatternType.TOOL_PREFERENCE: self._suggest_advanced_features,
            BehaviorPatternType.ERROR_PATTERN: self._suggest_error_prevention,
            BehaviorPatternType.USAGE_FREQUENCY: self._suggest_efficiency_improvements
        }
        
        self.suggestion_cache = {}
        self.cache_ttl = timedelta(hours=2)
    
    def generate_suggestions(self, user_profile: UserProfile, 
                           context: Optional[str] = None) -> List[Dict[str, Any]]:
        """Generate personalized suggestions based on user profile"""
        suggestions = []
        
        try:
            # Check if suggestions are enabled
            if not user_profile.personalization_settings.auto_suggestions:
                return suggestions
            
            # Generate pattern-based suggestions
            for pattern in user_profile.get_active_patterns():
                if pattern.pattern_type in self.suggestion_patterns:
                    pattern_suggestions = self.suggestion_patterns[pattern.pattern_type](pattern, user_profile)
                    suggestions.extend(pattern_suggestions)
            
            # Generate context-aware suggestions
            if context:
                context_suggestions = self._generate_contextual_suggestions(context, user_profile)
                suggestions.extend(context_suggestions)
            
            # Generate preference-based suggestions
            preference_suggestions = self._generate_preference_suggestions(user_profile)
            suggestions.extend(preference_suggestions)
            
            # Filter and rank suggestions
            suggestions = self._rank_and_filter_suggestions(suggestions, user_profile)
            
            # Limit suggestions based on user settings
            max_suggestions = user_profile.personalization_settings.suggestion_frequency_limit
            suggestions = suggestions[:max_suggestions]
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error generating suggestions: {e}")
            return []
    
    def _suggest_workflow_automation(self, pattern: BehaviorPattern, 
                                   user_profile: UserProfile) -> List[Dict[str, Any]]:
        """Suggest automation for command sequences"""
        suggestions = []
        
        if pattern.pattern_data.get("frequency", 0) >= 3:
            sequence = pattern.pattern_data.get("sequence", [])
            
            suggestions.append({
                "type": "automation",
                "priority": "high",
                "title": f"Automate '{pattern.pattern_name}' Workflow",
                "description": f"Create automation rule for your frequent command sequence: {' → '.join(sequence[:3])}",
                "action": "create_automation_rule",
                "data": {
                    "sequence": sequence,
                    "pattern_id": pattern.pattern_id
                },
                "benefits": ["Save time", "Reduce repetition", "Minimize errors"]
            })
        
        return suggestions
    
    def _suggest_time_based_automation(self, pattern: BehaviorPattern,
                                     user_profile: UserProfile) -> List[Dict[str, Any]]:
        """Suggest time-based automation"""
        suggestions = []
        
        if pattern.pattern_type == BehaviorPatternType.TIME_BASED:
            peak_hour = pattern.pattern_data.get("peak_hour")
            if peak_hour is not None:
                suggestions.append({
                    "type": "scheduling",
                    "priority": "medium",
                    "title": f"Schedule Regular Tasks for {peak_hour:02d}:00",
                    "description": f"Set up automated tasks during your peak activity time",
                    "action": "create_scheduled_automation",
                    "data": {
                        "preferred_hour": peak_hour,
                        "pattern_id": pattern.pattern_id
                    },
                    "benefits": ["Optimize productivity", "Consistent routine", "Automated maintenance"]
                })
        
        return suggestions
    
    def _suggest_advanced_features(self, pattern: BehaviorPattern,
                                 user_profile: UserProfile) -> List[Dict[str, Any]]:
        """Suggest advanced features based on tool preferences"""
        suggestions = []
        
        if pattern.pattern_type == BehaviorPatternType.TOOL_PREFERENCE:
            command = pattern.pattern_data.get("command")
            usage_percentage = pattern.pattern_data.get("usage_percentage", 0)
            
            if usage_percentage > 20:  # Heavy user of this command
                suggestions.append({
                    "type": "feature",
                    "priority": "medium",
                    "title": f"Advanced {command} Features",
                    "description": f"Since you use '{command}' frequently, explore advanced options and shortcuts",
                    "action": "show_advanced_help",
                    "data": {
                        "command": command,
                        "pattern_id": pattern.pattern_id
                    },
                    "benefits": ["Increased efficiency", "More capabilities", "Expert-level usage"]
                })
        
        return suggestions
    
    def _suggest_error_prevention(self, pattern: BehaviorPattern,
                                user_profile: UserProfile) -> List[Dict[str, Any]]:
        """Suggest error prevention measures"""
        suggestions = []
        
        if pattern.pattern_type == BehaviorPatternType.ERROR_PATTERN:
            error_type = pattern.pattern_data.get("error_type")
            error_rate = pattern.pattern_data.get("error_rate", 0)
            
            if error_rate > 0.15:  # >15% error rate
                suggestion_map = {
                    "timeout": {
                        "title": "Reduce Timeout Errors",
                        "description": "Configure longer timeouts for operations or use async execution",
                        "action": "configure_timeouts"
                    },
                    "permission": {
                        "title": "Fix Permission Issues", 
                        "description": "Set up proper file permissions or use elevated privileges",
                        "action": "check_permissions"
                    },
                    "not_found": {
                        "title": "Prevent 'Not Found' Errors",
                        "description": "Add validation checks before executing commands",
                        "action": "enable_validation"
                    }
                }
                
                if error_type in suggestion_map:
                    suggestion = suggestion_map[error_type]
                    suggestions.append({
                        "type": "improvement",
                        "priority": "high",
                        "title": suggestion["title"],
                        "description": suggestion["description"],
                        "action": suggestion["action"],
                        "data": {
                            "error_type": error_type,
                            "pattern_id": pattern.pattern_id
                        },
                        "benefits": ["Reduce errors", "Smoother experience", "Less frustration"]
                    })
        
        return suggestions
    
    def _suggest_efficiency_improvements(self, pattern: BehaviorPattern,
                                       user_profile: UserProfile) -> List[Dict[str, Any]]:
        """Suggest efficiency improvements based on usage patterns"""
        suggestions = []
        
        if pattern.pattern_type == BehaviorPatternType.USAGE_FREQUENCY:
            intensity = pattern.pattern_data.get("intensity_category")
            avg_commands = pattern.pattern_data.get("avg_commands_per_session", 0)
            
            if intensity == "Power User" and avg_commands > 30:
                suggestions.append({
                    "type": "efficiency",
                    "priority": "medium", 
                    "title": "Power User Shortcuts",
                    "description": "Enable keyboard shortcuts and command aliases for your most-used commands",
                    "action": "setup_shortcuts",
                    "data": {
                        "intensity": intensity,
                        "pattern_id": pattern.pattern_id
                    },
                    "benefits": ["Faster execution", "Reduced typing", "Power user features"]
                })
        
        return suggestions
    
    def _generate_contextual_suggestions(self, context: str, 
                                       user_profile: UserProfile) -> List[Dict[str, Any]]:
        """Generate suggestions based on current context"""
        suggestions = []
        
        context_lower = context.lower()
        
        if "error" in context_lower:
            suggestions.append({
                "type": "help",
                "priority": "high",
                "title": "Troubleshooting Assistant",
                "description": "Get help diagnosing and fixing this error",
                "action": "debug_error",
                "data": {"context": context},
                "benefits": ["Quick resolution", "Learn from errors", "Prevent recurrence"]
            })
        
        if "slow" in context_lower or "performance" in context_lower:
            suggestions.append({
                "type": "optimization",
                "priority": "medium",
                "title": "Performance Optimization",
                "description": "Analyze and improve system performance",
                "action": "optimize_performance",
                "data": {"context": context},
                "benefits": ["Faster execution", "Better resource usage", "Improved experience"]
            })
        
        return suggestions
    
    def _generate_preference_suggestions(self, user_profile: UserProfile) -> List[Dict[str, Any]]:
        """Generate suggestions based on user preferences"""
        suggestions = []
        
        preferences = user_profile.preferences
        
        # Suggest based on response style preferences
        if preferences.response_style.technical_level >= 4:
            suggestions.append({
                "type": "feature",
                "priority": "low",
                "title": "Advanced API Access",
                "description": "Enable direct API access for advanced integrations",
                "action": "enable_api_access",
                "data": {"technical_level": preferences.response_style.technical_level},
                "benefits": ["Advanced control", "Custom integrations", "Programmatic access"]
            })
        
        # Suggest based on automation preferences
        if preferences.tool_preferences.automation_enabled:
            suggestions.append({
                "type": "automation",
                "priority": "low",
                "title": "Smart Automation Templates",
                "description": "Explore pre-built automation templates for common tasks",
                "action": "browse_automation_templates",
                "data": {"automation_enabled": True},
                "benefits": ["Quick setup", "Best practices", "Time saving"]
            })
        
        return suggestions
    
    def _rank_and_filter_suggestions(self, suggestions: List[Dict[str, Any]], 
                                   user_profile: UserProfile) -> List[Dict[str, Any]]:
        """Rank and filter suggestions based on relevance and user preferences"""
        if not suggestions:
            return []
        
        # Priority ranking
        priority_weights = {"high": 3, "medium": 2, "low": 1}
        
        # Sort by priority and add relevance scoring
        for suggestion in suggestions:
            priority_score = priority_weights.get(suggestion.get("priority", "low"), 1)
            
            # Add relevance based on user technical level
            tech_level = user_profile.preferences.response_style.technical_level
            if suggestion["type"] == "feature" and tech_level >= 4:
                priority_score += 1
            elif suggestion["type"] == "help" and tech_level <= 2:
                priority_score += 1
            
            suggestion["_score"] = priority_score
        
        # Sort by score
        suggestions.sort(key=lambda x: x.get("_score", 0), reverse=True)
        
        # Remove duplicates
        seen_titles = set()
        unique_suggestions = []
        for suggestion in suggestions:
            if suggestion["title"] not in seen_titles:
                seen_titles.add(suggestion["title"])
                unique_suggestions.append(suggestion)
        
        # Remove scoring field
        for suggestion in unique_suggestions:
            suggestion.pop("_score", None)
        
        return unique_suggestions


class ContextManager:
    """Manages context awareness and session continuity"""
    
    def __init__(self):
        self.user_contexts: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self.session_histories: Dict[str, deque] = defaultdict(lambda: deque(maxlen=50))
        self.context_ttl = timedelta(hours=2)
    
    def update_user_context(self, user_id: str, context_key: str, context_value: Any):
        """Update user context information"""
        self.user_contexts[user_id][context_key] = {
            "value": context_value,
            "timestamp": datetime.utcnow()
        }
    
    def get_user_context(self, user_id: str, context_key: str) -> Optional[Any]:
        """Get user context information"""
        context_data = self.user_contexts[user_id].get(context_key)
        
        if context_data:
            # Check if context is still valid
            if datetime.utcnow() - context_data["timestamp"] < self.context_ttl:
                return context_data["value"]
            else:
                # Remove expired context
                del self.user_contexts[user_id][context_key]
        
        return None
    
    def add_to_session_history(self, user_id: str, interaction: Dict[str, Any]):
        """Add interaction to session history"""
        interaction["timestamp"] = datetime.utcnow()
        self.session_histories[user_id].append(interaction)
    
    def get_session_context(self, user_id: str, lookback: int = 5) -> List[Dict[str, Any]]:
        """Get recent session context"""
        history = list(self.session_histories[user_id])
        return history[-lookback:] if history else []
    
    def should_provide_context_hint(self, user_id: str, current_command: str) -> Optional[str]:
        """Determine if a context hint should be provided"""
        recent_context = self.get_session_context(user_id, 3)
        
        if len(recent_context) >= 2:
            # Check for related commands
            recent_commands = [ctx.get("command", "") for ctx in recent_context]
            
            if current_command in recent_commands:
                return f"You recently used '{current_command}'. Building on previous work?"
            
            # Check for error patterns
            recent_errors = [ctx for ctx in recent_context if not ctx.get("success", True)]
            if len(recent_errors) >= 2:
                return "I notice some recent errors. Would you like troubleshooting help?"
        
        return None


class PersonalizationEngine:
    """Main personalization engine coordinating all personalization components"""
    
    def __init__(self, storage_backend=None):
        self.storage = storage_backend
        
        # Core components
        self.response_personalizer = ResponsePersonalizer()
        self.suggestion_engine = SuggestionEngine()
        self.context_manager = ContextManager()
        
        # User profiles cache
        self.user_profiles: Dict[str, UserProfile] = {}
        self.profile_cache_ttl = timedelta(minutes=30)
        self.last_profile_load: Dict[str, datetime] = {}
        
        # Personalization state
        self.personalization_enabled = True
        self.learning_enabled = True
        
        logger.info("PersonalizationEngine initialized")
    
    async def get_user_profile(self, user_id: str) -> UserProfile:
        """Get or create user profile"""
        try:
            # Check cache
            if (user_id in self.user_profiles and 
                user_id in self.last_profile_load and
                datetime.utcnow() - self.last_profile_load[user_id] < self.profile_cache_ttl):
                return self.user_profiles[user_id]
            
            # Try loading from storage
            if self.storage:
                stored_profile = await self.storage.load_user_profile(user_id)
                if stored_profile:
                    self.user_profiles[user_id] = stored_profile
                    self.last_profile_load[user_id] = datetime.utcnow()
                    return stored_profile
            
            # Create new profile
            from .schemas import create_default_user_profile
            profile = create_default_user_profile(user_id)
            
            # Store and cache
            self.user_profiles[user_id] = profile
            self.last_profile_load[user_id] = datetime.utcnow()
            
            if self.storage:
                await self.storage.store_user_profile(profile)
            
            return profile
            
        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
            from .schemas import create_default_user_profile
            return create_default_user_profile(user_id)
    
    async def personalize_response(self, user_id: str, response: str, 
                                 response_type: str = "general") -> str:
        """Personalize a response for a specific user"""
        if not self.personalization_enabled:
            return response
        
        try:
            profile = await self.get_user_profile(user_id)
            
            if not profile.personalization_settings.response_personalization:
                return response
            
            # Apply response personalization
            personalized_response = self.response_personalizer.personalize_response(
                response, profile.preferences, response_type
            )
            
            # Add context hints if appropriate
            context_hint = self.context_manager.should_provide_context_hint(user_id, response)
            if context_hint:
                personalized_response += f"\n\n💡 {context_hint}"
            
            return personalized_response
            
        except Exception as e:
            logger.error(f"Error personalizing response: {e}")
            return response
    
    async def get_personalized_suggestions(self, user_id: str, 
                                         context: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get personalized suggestions for a user"""
        if not self.personalization_enabled:
            return []
        
        try:
            profile = await self.get_user_profile(user_id)
            
            if not profile.personalization_settings.suggestion_personalization:
                return []
            
            suggestions = self.suggestion_engine.generate_suggestions(profile, context)
            return suggestions
            
        except Exception as e:
            logger.error(f"Error generating personalized suggestions: {e}")
            return []
    
    async def record_user_interaction(self, user_id: str, command: str, 
                                    success: bool, context: Optional[str] = None):
        """Record user interaction for learning and context"""
        try:
            # Update context
            self.context_manager.add_to_session_history(user_id, {
                "command": command,
                "success": success,
                "context": context
            })
            
            # Update user activity
            profile = await self.get_user_profile(user_id)
            profile.update_activity()
            
            # Store updated profile
            if self.storage:
                await self.storage.store_user_profile(profile)
                
        except Exception as e:
            logger.error(f"Error recording user interaction: {e}")
    
    async def update_user_preferences(self, user_id: str, preferences: UserPreferences):
        """Update user preferences"""
        try:
            profile = await self.get_user_profile(user_id)
            profile.preferences = preferences
            
            # Update cache
            self.user_profiles[user_id] = profile
            
            # Store updated profile
            if self.storage:
                await self.storage.store_user_profile(profile)
                
            logger.info(f"Updated preferences for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error updating user preferences: {e}")
    
    async def add_behavior_pattern(self, user_id: str, pattern: BehaviorPattern):
        """Add a behavior pattern to user profile"""
        try:
            profile = await self.get_user_profile(user_id)
            profile.add_behavior_pattern(pattern)
            
            # Update cache
            self.user_profiles[user_id] = profile
            
            # Store updated profile
            if self.storage:
                await self.storage.store_user_profile(profile)
                
        except Exception as e:
            logger.error(f"Error adding behavior pattern: {e}")
    
    def enable_personalization(self):
        """Enable personalization features"""
        self.personalization_enabled = True
        logger.info("Personalization enabled")
    
    def disable_personalization(self):
        """Disable personalization features"""
        self.personalization_enabled = False
        logger.info("Personalization disabled")
    
    def enable_learning(self):
        """Enable learning from user interactions"""
        self.learning_enabled = True
        logger.info("Learning enabled")
    
    def disable_learning(self):
        """Disable learning from user interactions"""
        self.learning_enabled = False
        logger.info("Learning disabled")
    
    def clear_user_cache(self, user_id: Optional[str] = None):
        """Clear user profile cache"""
        if user_id:
            self.user_profiles.pop(user_id, None)
            self.last_profile_load.pop(user_id, None)
        else:
            self.user_profiles.clear()
            self.last_profile_load.clear()
        
        logger.info(f"Cleared profile cache for {'all users' if not user_id else user_id}")
    
    def get_personalization_stats(self) -> Dict[str, Any]:
        """Get personalization system statistics"""
        return {
            "personalization_enabled": self.personalization_enabled,
            "learning_enabled": self.learning_enabled,
            "cached_profiles": len(self.user_profiles),
            "active_contexts": len(self.context_manager.user_contexts),
            "session_histories": len(self.context_manager.session_histories)
        }


# Export main classes
__all__ = [
    "PersonalizationEngine", "ResponsePersonalizer", 
    "SuggestionEngine", "ContextManager"
]