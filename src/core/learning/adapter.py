"""
JARVIS 2.0 Adaptive Response Generator

Advanced response adaptation system that generates context-aware, personalized
responses based on user preferences, behavior patterns, and interaction history.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import logging
import random
from collections import defaultdict

from .schemas import (
    UserProfile, UserPreferences, BehaviorPattern, BehaviorPatternType,
    ResponseStyle, ResponseTone, ResponseVerbosity, UsageContext
)

logger = logging.getLogger(__name__)


class AdaptiveResponseGenerator:
    """Main adaptive response generation system"""
    
    def __init__(self, personalization_engine=None):
        self.personalization_engine = personalization_engine
        
        # Response templates and patterns
        self.response_templates = self._initialize_response_templates()
        self.context_modifiers = self._initialize_context_modifiers()
        self.pattern_adaptations = self._initialize_pattern_adaptations()
        
        # Adaptation cache
        self.adaptation_cache: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self.cache_ttl = timedelta(minutes=15)
        
        # Configuration
        self.adaptation_enabled = True
        self.learning_rate = 0.1  # How quickly to adapt to new patterns
        
        logger.info("AdaptiveResponseGenerator initialized")
    
    def _initialize_response_templates(self) -> Dict[str, Dict[str, List[str]]]:
        """Initialize response templates for different scenarios"""
        return {
            "success": {
                ResponseTone.CASUAL: [
                    "Great! {result}",
                    "Done! {result}",
                    "Nice! {result}"
                ],
                ResponseTone.PROFESSIONAL: [
                    "Task completed successfully. {result}",
                    "Operation completed. {result}",
                    "Successfully executed. {result}"
                ],
                ResponseTone.FRIENDLY: [
                    "All done! {result}",
                    "Perfect! {result}",
                    "Excellent work! {result}"
                ],
                ResponseTone.TECHNICAL: [
                    "Process executed successfully. {result}",
                    "Operation terminated with exit code 0. {result}",
                    "Execution completed. {result}"
                ],
                ResponseTone.CONCISE: [
                    "Done. {result}",
                    "Complete. {result}",
                    "✓ {result}"
                ]
            },
            "error": {
                ResponseTone.CASUAL: [
                    "Oops! {error}",
                    "Hmm, that didn't work. {error}",
                    "Something went wrong. {error}"
                ],
                ResponseTone.PROFESSIONAL: [
                    "An error occurred: {error}",
                    "Unable to complete operation: {error}",
                    "Execution failed: {error}"
                ],
                ResponseTone.FRIENDLY: [
                    "Sorry about that! {error}",
                    "Let me help fix this. {error}",
                    "I encountered an issue: {error}"
                ],
                ResponseTone.TECHNICAL: [
                    "Error detected: {error}",
                    "Exception thrown: {error}",
                    "Failure condition met: {error}"
                ],
                ResponseTone.CONCISE: [
                    "Error: {error}",
                    "Failed: {error}",
                    "✗ {error}"
                ]
            },
            "help": {
                ResponseTone.CASUAL: [
                    "Here's how you can {action}:",
                    "Let me show you how to {action}:",
                    "You can {action} like this:"
                ],
                ResponseTone.PROFESSIONAL: [
                    "To {action}, please follow these steps:",
                    "The procedure to {action} is as follows:",
                    "Here are the instructions to {action}:"
                ],
                ResponseTone.FRIENDLY: [
                    "I'd be happy to help you {action}!",
                    "Sure thing! Here's how to {action}:",
                    "Let me walk you through how to {action}:"
                ],
                ResponseTone.TECHNICAL: [
                    "Command syntax for {action}:",
                    "Technical documentation for {action}:",
                    "API reference for {action}:"
                ],
                ResponseTone.CONCISE: [
                    "To {action}:",
                    "{action}:",
                    "Usage:"
                ]
            },
            "suggestion": {
                ResponseTone.CASUAL: [
                    "Hey, you might want to try {suggestion}",
                    "Have you considered {suggestion}?",
                    "Maybe try {suggestion}?"
                ],
                ResponseTone.PROFESSIONAL: [
                    "I recommend {suggestion}",
                    "Consider implementing {suggestion}",
                    "You may benefit from {suggestion}"
                ],
                ResponseTone.FRIENDLY: [
                    "Here's a helpful tip: {suggestion}",
                    "You might like this: {suggestion}",
                    "I have a suggestion for you: {suggestion}"
                ],
                ResponseTone.TECHNICAL: [
                    "Optimization suggestion: {suggestion}",
                    "Performance recommendation: {suggestion}",
                    "System advisory: {suggestion}"
                ],
                ResponseTone.CONCISE: [
                    "Try: {suggestion}",
                    "Suggestion: {suggestion}",
                    "→ {suggestion}"
                ]
            }
        }
    
    def _initialize_context_modifiers(self) -> Dict[UsageContext, Dict[str, str]]:
        """Initialize context-specific response modifiers"""
        return {
            UsageContext.WORK: {
                "prefix": "",
                "suffix": "",
                "emphasis": "efficiency and accuracy",
                "avoid": ["casual language", "emojis", "humor"]
            },
            UsageContext.PERSONAL: {
                "prefix": "",
                "suffix": "",
                "emphasis": "helpfulness and clarity",
                "avoid": ["overly formal language"]
            },
            UsageContext.LEARNING: {
                "prefix": "",
                "suffix": " Would you like more details or examples?",
                "emphasis": "education and explanation",
                "avoid": ["assumptions about prior knowledge"]
            },
            UsageContext.AUTOMATION: {
                "prefix": "",
                "suffix": "",
                "emphasis": "precision and reliability",
                "avoid": ["ambiguous instructions"]
            },
            UsageContext.TROUBLESHOOTING: {
                "prefix": "",
                "suffix": " Let me know if you need additional help.",
                "emphasis": "problem-solving and support",
                "avoid": ["dismissive tone"]
            }
        }
    
    def _initialize_pattern_adaptations(self) -> Dict[BehaviorPatternType, Dict[str, Any]]:
        """Initialize adaptations based on behavior patterns"""
        return {
            BehaviorPatternType.TIME_BASED: {
                "morning": {"greeting": "Good morning!", "energy": "high"},
                "afternoon": {"greeting": "Good afternoon!", "energy": "moderate"},
                "evening": {"greeting": "Good evening!", "energy": "calm"},
                "late_night": {"greeting": "Working late?", "energy": "supportive"}
            },
            BehaviorPatternType.COMMAND_SEQUENCE: {
                "workflow_oriented": {
                    "suggest_automation": True,
                    "offer_shortcuts": True,
                    "emphasize_efficiency": True
                }
            },
            BehaviorPatternType.TOOL_PREFERENCE: {
                "power_user": {
                    "provide_advanced_options": True,
                    "show_technical_details": True,
                    "suggest_optimizations": True
                },
                "casual_user": {
                    "simplify_explanations": True,
                    "provide_examples": True,
                    "offer_guided_help": True
                }
            },
            BehaviorPatternType.ERROR_PATTERN: {
                "frequent_errors": {
                    "provide_extra_validation": True,
                    "suggest_error_prevention": True,
                    "offer_debugging_help": True
                }
            },
            BehaviorPatternType.USAGE_FREQUENCY: {
                "heavy_user": {
                    "suggest_advanced_features": True,
                    "provide_shortcuts": True,
                    "offer_customization": True
                },
                "light_user": {
                    "provide_gentle_guidance": True,
                    "explain_basics": True,
                    "encourage_exploration": True
                }
            }
        }
    
    async def generate_adaptive_response(self, user_id: str, base_response: str,
                                       response_type: str = "general",
                                       context: Optional[str] = None,
                                       command: Optional[str] = None) -> str:
        """Generate an adaptive response based on user profile and patterns"""
        
        if not self.adaptation_enabled:
            return base_response
        
        try:
            # Get user profile
            if self.personalization_engine:
                user_profile = await self.personalization_engine.get_user_profile(user_id)
            else:
                logger.warning("No personalization engine available")
                return base_response
            
            # Check cache
            cache_key = f"{user_id}_{response_type}_{hash(base_response)}"
            if self._is_cached_response_valid(cache_key):
                cached_adaptation = self.adaptation_cache[user_id][cache_key]
                return self._apply_cached_adaptation(base_response, cached_adaptation)
            
            # Generate adaptive response
            adapted_response = await self._adapt_response(
                base_response, user_profile, response_type, context, command
            )
            
            # Cache the adaptation
            self._cache_adaptation(user_id, cache_key, base_response, adapted_response)
            
            return adapted_response
            
        except Exception as e:
            logger.error(f"Error generating adaptive response: {e}")
            return base_response
    
    async def _adapt_response(self, base_response: str, user_profile: UserProfile,
                            response_type: str, context: Optional[str],
                            command: Optional[str]) -> str:
        """Core response adaptation logic"""
        
        # Start with base response
        adapted_response = base_response
        
        # Apply preference-based adaptations
        adapted_response = self._apply_preference_adaptations(
            adapted_response, user_profile.preferences, response_type
        )
        
        # Apply pattern-based adaptations
        adapted_response = self._apply_pattern_adaptations(
            adapted_response, user_profile.behavior_patterns, response_type
        )
        
        # Apply context-based adaptations
        if context:
            adapted_response = self._apply_context_adaptations(
                adapted_response, context, user_profile.preferences
            )
        
        # Apply command-specific adaptations
        if command:
            adapted_response = self._apply_command_adaptations(
                adapted_response, command, user_profile
            )
        
        # Apply time-based adaptations
        adapted_response = self._apply_time_adaptations(
            adapted_response, user_profile
        )
        
        return adapted_response
    
    def _apply_preference_adaptations(self, response: str, preferences: UserPreferences,
                                    response_type: str) -> str:
        """Apply adaptations based on user preferences"""
        
        style = preferences.response_style
        
        # Apply tone-based templates if available
        if response_type in self.response_templates:
            templates = self.response_templates[response_type].get(style.tone, [])
            if templates and "{" in templates[0]:  # Template expects formatting
                # Don't apply template to avoid double-formatting
                pass
            else:
                # Apply tone prefix/suffix
                tone_modifier = self._get_tone_modifier(style.tone, response_type)
                if tone_modifier:
                    response = f"{tone_modifier} {response}"
        
        # Apply verbosity adjustments
        if style.verbosity == ResponseVerbosity.MINIMAL:
            response = self._minimize_response(response)
        elif style.verbosity == ResponseVerbosity.COMPREHENSIVE:
            response = self._expand_response(response, style.technical_level)
        
        # Apply technical level adjustments
        if style.technical_level <= 2:
            response = self._simplify_response(response)
        elif style.technical_level >= 4:
            response = self._enhance_technical_response(response)
        
        # Apply formatting preferences
        if style.use_emojis and response_type in ["success", "error"]:
            response = self._add_contextual_emoji(response, response_type)
        
        return response
    
    def _apply_pattern_adaptations(self, response: str, patterns: List[BehaviorPattern],
                                 response_type: str) -> str:
        """Apply adaptations based on detected behavior patterns"""
        
        for pattern in patterns:
            if not pattern.is_active or pattern.confidence_score < 0.6:
                continue
            
            pattern_type = pattern.pattern_type
            
            if pattern_type == BehaviorPatternType.TOOL_PREFERENCE:
                # Adapt for power users vs casual users
                usage_percentage = pattern.pattern_data.get("usage_percentage", 0)
                if usage_percentage > 30:  # Power user
                    response = self._adapt_for_power_user(response)
                else:
                    response = self._adapt_for_casual_user(response)
            
            elif pattern_type == BehaviorPatternType.ERROR_PATTERN:
                # Add extra guidance for users with frequent errors
                error_rate = pattern.pattern_data.get("error_rate", 0)
                if error_rate > 0.2 and response_type == "help":
                    response += "\n\n💡 Tip: Double-check the command syntax before running."
            
            elif pattern_type == BehaviorPatternType.USAGE_FREQUENCY:
                # Adapt for usage intensity
                intensity = pattern.pattern_data.get("intensity_category", "")
                if intensity == "Power User" and response_type == "success":
                    response += " ⚡"  # Power user indicator
                elif intensity == "Light User" and response_type == "help":
                    response += "\n\nFeel free to ask if you need more guidance!"
            
            elif pattern_type == BehaviorPatternType.COMMAND_SEQUENCE:
                # Suggest workflow improvements
                frequency = pattern.pattern_data.get("frequency", 0)
                if frequency >= 3 and response_type == "success":
                    response += f"\n\n🔄 I notice you use this sequence often. Want to automate it?"
        
        return response
    
    def _apply_context_adaptations(self, response: str, context: str,
                                 preferences: UserPreferences) -> str:
        """Apply context-specific adaptations"""
        
        context_lower = context.lower()
        
        # Work context - more formal and efficient
        if "work" in context_lower or "professional" in context_lower:
            response = self._make_more_professional(response)
        
        # Learning context - more educational
        elif "learn" in context_lower or "tutorial" in context_lower:
            response = self._make_more_educational(response)
        
        # Error/troubleshooting context - more supportive
        elif "error" in context_lower or "problem" in context_lower:
            response = self._make_more_supportive(response)
        
        # Automation context - more precise
        elif "automation" in context_lower or "script" in context_lower:
            response = self._make_more_precise(response)
        
        return response
    
    def _apply_command_adaptations(self, response: str, command: str,
                                 user_profile: UserProfile) -> str:
        """Apply command-specific adaptations"""
        
        command_lower = command.lower()
        
        # Help commands - provide more guidance
        if command_lower.startswith("help"):
            if user_profile.preferences.response_style.technical_level <= 2:
                response += "\n\n📚 New to this command? Try the tutorial mode for step-by-step guidance."
        
        # Tool commands - suggest related tools
        elif "tool" in command_lower:
            response += f"\n\n🔧 Related tools you might find useful: explore the tools menu for more options."
        
        # Automation commands - suggest templates
        elif "automation" in command_lower or "schedule" in command_lower:
            response += f"\n\n⚙️ Check out automation templates for quick setup of common tasks."
        
        return response
    
    def _apply_time_adaptations(self, response: str, user_profile: UserProfile) -> str:
        """Apply time-of-day based adaptations"""
        
        current_hour = datetime.now().hour
        
        # Find time-based patterns
        time_patterns = [p for p in user_profile.behavior_patterns 
                        if p.pattern_type == BehaviorPatternType.TIME_BASED]
        
        for pattern in time_patterns:
            peak_hour = pattern.pattern_data.get("peak_hour")
            if peak_hour and abs(current_hour - peak_hour) <= 1:
                # User is in their peak time
                if "Good" not in response:  # Avoid double greetings
                    time_greeting = self._get_time_greeting(current_hour)
                    response = f"{time_greeting} {response}"
                break
        
        return response
    
    def _get_tone_modifier(self, tone: ResponseTone, response_type: str) -> Optional[str]:
        """Get tone-specific modifier for response"""
        modifiers = {
            ResponseTone.CASUAL: {"success": "Nice!", "error": "Oops,", "help": "Hey,"},
            ResponseTone.PROFESSIONAL: {"success": "", "error": "", "help": ""},
            ResponseTone.FRIENDLY: {"success": "Great!", "error": "Sorry,", "help": "Sure!"},
            ResponseTone.TECHNICAL: {"success": "", "error": "Error:", "help": "Info:"},
            ResponseTone.CONCISE: {"success": "", "error": "", "help": ""}
        }
        
        return modifiers.get(tone, {}).get(response_type)
    
    def _minimize_response(self, response: str) -> str:
        """Minimize response for concise preference"""
        # Keep only the first sentence or main point
        sentences = response.split('.')
        if len(sentences) > 1:
            return sentences[0] + '.'
        return response[:100] + '...' if len(response) > 100 else response
    
    def _expand_response(self, response: str, technical_level: int) -> str:
        """Expand response for comprehensive preference"""
        expansions = []
        
        if "completed" in response.lower():
            expansions.append("You can view the results or run additional commands as needed.")
        
        if "error" in response.lower():
            expansions.append("Check the error details above and try the suggested solutions.")
            if technical_level <= 2:
                expansions.append("Don't hesitate to ask for help if you're unsure about next steps.")
        
        if expansions:
            response += " " + " ".join(expansions)
        
        return response
    
    def _simplify_response(self, response: str) -> str:
        """Simplify response for beginner users"""
        # Replace technical terms with simpler ones
        replacements = {
            "execute": "run",
            "initialize": "start", 
            "terminate": "stop",
            "parameter": "setting",
            "configuration": "setup",
            "implementation": "way to do it"
        }
        
        for technical, simple in replacements.items():
            response = response.replace(technical, simple)
        
        return response
    
    def _enhance_technical_response(self, response: str) -> str:
        """Enhance response with technical details"""
        if "completed" in response.lower() and "exit code" not in response.lower():
            response += " (Exit code: 0)"
        
        if "failed" in response.lower() and "status" not in response.lower():
            response += " (Check system status for details)"
        
        return response
    
    def _add_contextual_emoji(self, response: str, response_type: str) -> str:
        """Add contextual emoji based on response type"""
        emoji_map = {
            "success": "✅",
            "error": "❌",
            "help": "💡",
            "suggestion": "💡"
        }
        
        emoji = emoji_map.get(response_type)
        if emoji and emoji not in response:
            return f"{emoji} {response}"
        
        return response
    
    def _adapt_for_power_user(self, response: str) -> str:
        """Adapt response for power users"""
        if "help" in response.lower() and "advanced" not in response.lower():
            response += "\n\n⚡ Pro tip: Use advanced flags for more control."
        
        return response
    
    def _adapt_for_casual_user(self, response: str) -> str:
        """Adapt response for casual users"""
        if not any(phrase in response.lower() for phrase in ["help", "tip", "guide"]):
            response += "\n\n💡 Need help? Just ask!"
        
        return response
    
    def _make_more_professional(self, response: str) -> str:
        """Make response more professional"""
        # Remove casual language and emojis
        casual_replacements = {
            "Hey": "",
            "!": ".",
            "Nice!": "Completed successfully.",
            "Oops": "Error occurred"
        }
        
        for casual, formal in casual_replacements.items():
            response = response.replace(casual, formal)
        
        # Remove emojis
        import re
        response = re.sub(r'[^\w\s.,!?-]', '', response)
        
        return response
    
    def _make_more_educational(self, response: str) -> str:
        """Make response more educational"""
        if not any(phrase in response.lower() for phrase in ["learn", "understand", "example"]):
            response += "\n\n📚 Would you like to learn more about how this works?"
        
        return response
    
    def _make_more_supportive(self, response: str) -> str:
        """Make response more supportive for errors"""
        if "error" in response.lower() and "help" not in response.lower():
            response += "\n\n🤝 Don't worry, I'm here to help you resolve this."
        
        return response
    
    def _make_more_precise(self, response: str) -> str:
        """Make response more precise for automation context"""
        if "automation" in response.lower():
            response += "\n\n🎯 Ensure parameters are exact for reliable automation."
        
        return response
    
    def _get_time_greeting(self, hour: int) -> str:
        """Get appropriate time-based greeting"""
        if 5 <= hour < 12:
            return "Good morning!"
        elif 12 <= hour < 17:
            return "Good afternoon!"
        elif 17 <= hour < 22:
            return "Good evening!"
        else:
            return "Working late tonight?"
    
    def _is_cached_response_valid(self, cache_key: str) -> bool:
        """Check if cached response is still valid"""
        # Implementation would check cache TTL
        return False  # Simplified for now
    
    def _apply_cached_adaptation(self, base_response: str, cached_adaptation: Dict[str, Any]) -> str:
        """Apply cached adaptation to response"""
        # Implementation would apply cached adaptation rules
        return base_response  # Simplified for now
    
    def _cache_adaptation(self, user_id: str, cache_key: str, base_response: str, adapted_response: str):
        """Cache the adaptation for future use"""
        adaptation_diff = {
            "base_length": len(base_response),
            "adapted_length": len(adapted_response),
            "modifications": self._extract_modifications(base_response, adapted_response),
            "timestamp": datetime.utcnow()
        }
        
        self.adaptation_cache[user_id][cache_key] = adaptation_diff
    
    def _extract_modifications(self, base: str, adapted: str) -> Dict[str, Any]:
        """Extract what modifications were made"""
        return {
            "length_change": len(adapted) - len(base),
            "added_emoji": "✅" in adapted and "✅" not in base,
            "added_tip": "💡" in adapted and "💡" not in base,
            "tone_change": base != adapted
        }
    
    def enable_adaptation(self):
        """Enable response adaptation"""
        self.adaptation_enabled = True
        logger.info("Response adaptation enabled")
    
    def disable_adaptation(self):
        """Disable response adaptation"""
        self.adaptation_enabled = False
        logger.info("Response adaptation disabled")
    
    def set_learning_rate(self, rate: float):
        """Set adaptation learning rate"""
        self.learning_rate = max(0.0, min(1.0, rate))
        logger.info(f"Adaptation learning rate set to {rate}")
    
    def clear_adaptation_cache(self, user_id: Optional[str] = None):
        """Clear adaptation cache"""
        if user_id:
            self.adaptation_cache.pop(user_id, None)
        else:
            self.adaptation_cache.clear()
        
        logger.info(f"Cleared adaptation cache for {'all users' if not user_id else user_id}")
    
    def get_adaptation_stats(self) -> Dict[str, Any]:
        """Get adaptation system statistics"""
        total_cached_adaptations = sum(len(user_cache) for user_cache in self.adaptation_cache.values())
        
        return {
            "adaptation_enabled": self.adaptation_enabled,
            "learning_rate": self.learning_rate,
            "cached_users": len(self.adaptation_cache),
            "total_cached_adaptations": total_cached_adaptations,
            "cache_ttl_minutes": self.cache_ttl.total_seconds() / 60
        }


# Export main class
__all__ = ["AdaptiveResponseGenerator"]