"""
JARVIS 2.0 Learning System

An intelligent learning and personalization system that adapts to user behavior,
tracks preferences, and provides personalized responses based on usage patterns.

Components:
- UserPreferences: Track user settings and preferences
- UsageAnalytics: Monitor and analyze user behavior patterns
- BehaviorDetector: ML-based pattern detection and insights
- PersonalizationEngine: Adaptive response generation
- LearningStorage: Persistent data storage with privacy controls

Key Features:
- Automatic preference detection from user interactions
- Usage pattern analysis and behavioral insights
- Adaptive response tone and style customization
- Command suggestion based on usage history
- Privacy-focused data handling
"""

from .schemas import (
    UserProfile,
    UserPreferences, 
    ResponseStyle,
    UsageSession,
    CommandUsage,
    BehaviorPattern,
    PersonalizationSettings,
    LearningData
)

from .tracker import PreferenceTracker
from .analytics import AnalyticsEngine
from .detector import BehaviorDetector
from .engine import PersonalizationEngine
from .storage import LearningStorage
from .adapter import AdaptiveResponseGenerator

__version__ = "1.0.0"
__author__ = "JARVIS 2.0 Team"

__all__ = [
    # Data Models
    "UserProfile",
    "UserPreferences", 
    "ResponseStyle",
    "UsageSession",
    "CommandUsage", 
    "BehaviorPattern",
    "PersonalizationSettings",
    "LearningData",
    
    # Core Components
    "PreferenceTracker",
    "AnalyticsEngine", 
    "BehaviorDetector",
    "PersonalizationEngine",
    "LearningStorage",
    "AdaptiveResponseGenerator"
]

# Global instances will be initialized by CLI
preference_tracker = None
analytics_engine = None
behavior_detector = None
personalization_engine = None
learning_storage = None
adaptive_response_generator = None