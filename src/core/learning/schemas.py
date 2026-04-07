"""
JARVIS 2.0 Learning System Schemas

Comprehensive data models for user learning, preference tracking,
behavior analysis, and personalization features.
"""

from datetime import datetime, time
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, validator
import uuid


class ResponseTone(str, Enum):
    """Response tone preferences"""
    CASUAL = "casual"
    PROFESSIONAL = "professional"
    FRIENDLY = "friendly"
    CONCISE = "concise"
    DETAILED = "detailed"
    TECHNICAL = "technical"
    HUMOROUS = "humorous"


class ResponseVerbosity(str, Enum):
    """Response verbosity levels"""
    MINIMAL = "minimal"
    BRIEF = "brief"
    NORMAL = "normal"
    DETAILED = "detailed"
    COMPREHENSIVE = "comprehensive"


class PreferenceSource(str, Enum):
    """How a preference was determined"""
    USER_EXPLICIT = "user_explicit"  # User directly set
    BEHAVIOR_INFERRED = "behavior_inferred"  # Learned from behavior
    PATTERN_DETECTED = "pattern_detected"  # ML pattern detection
    DEFAULT = "default"  # System default


class UsageContext(str, Enum):
    """Context in which command was used"""
    WORK = "work"
    PERSONAL = "personal"
    LEARNING = "learning"
    AUTOMATION = "automation"
    TROUBLESHOOTING = "troubleshooting"
    EXPLORATION = "exploration"


class CommandCategory(str, Enum):
    """Categories of commands for analytics"""
    TOOL = "tool"
    AGENT = "agent" 
    AUTOMATION = "automation"
    LLM = "llm"
    SYSTEM = "system"
    FILE = "file"
    SEARCH = "search"
    HELP = "help"


class BehaviorPatternType(str, Enum):
    """Types of detected behavior patterns"""
    TIME_BASED = "time_based"
    COMMAND_SEQUENCE = "command_sequence"
    TOOL_PREFERENCE = "tool_preference"
    RESPONSE_STYLE = "response_style"
    USAGE_FREQUENCY = "usage_frequency"
    ERROR_PATTERN = "error_pattern"
    WORKFLOW = "workflow"


class LearningStatus(str, Enum):
    """Status of learning system components"""
    ACTIVE = "active"
    DISABLED = "disabled"
    LEARNING = "learning"
    ANALYZING = "analyzing"


class ResponseStyle(BaseModel):
    """User's preferred response style"""
    tone: ResponseTone = ResponseTone.FRIENDLY
    verbosity: ResponseVerbosity = ResponseVerbosity.NORMAL
    include_explanations: bool = True
    include_examples: bool = True
    use_emojis: bool = False
    technical_level: int = Field(default=3, ge=1, le=5)  # 1=beginner, 5=expert
    
    class Config:
        frozen = True


class TimePreferences(BaseModel):
    """User's time-based preferences"""
    timezone: str = "UTC"
    active_hours_start: time = time(9, 0)  # 9 AM
    active_hours_end: time = time(17, 0)   # 5 PM
    preferred_reminder_time: time = time(10, 0)  # 10 AM
    weekend_mode: bool = False  # Different behavior on weekends
    
    class Config:
        frozen = True


class ToolPreferences(BaseModel):
    """Preferences for specific tools and features"""
    preferred_llm_model: str = "gpt-4"
    preferred_code_language: Optional[str] = None
    preferred_search_engine: str = "google"
    automation_enabled: bool = True
    agent_delegation_threshold: int = Field(default=3, ge=1, le=5)
    suggestion_frequency: int = Field(default=3, ge=1, le=5)
    
    class Config:
        frozen = True


class PrivacySettings(BaseModel):
    """User privacy and data collection preferences"""
    collect_usage_data: bool = True
    collect_command_history: bool = True
    collect_error_data: bool = True
    share_analytics: bool = False
    data_retention_days: int = Field(default=90, ge=1, le=365)
    anonymize_data: bool = True
    
    class Config:
        frozen = True


class UserPreferences(BaseModel):
    """Complete user preference profile"""
    user_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    response_style: ResponseStyle = Field(default_factory=ResponseStyle)
    time_preferences: TimePreferences = Field(default_factory=TimePreferences) 
    tool_preferences: ToolPreferences = Field(default_factory=ToolPreferences)
    privacy_settings: PrivacySettings = Field(default_factory=PrivacySettings)
    
    # Custom preferences (user-defined key-value pairs)
    custom_preferences: Dict[str, Any] = Field(default_factory=dict)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    version: str = "1.0.0"
    
    def update_preference(self, category: str, key: str, value: Any, source: PreferenceSource = PreferenceSource.USER_EXPLICIT):
        """Update a specific preference"""
        self.updated_at = datetime.utcnow()
        
        if category == "response_style":
            if hasattr(self.response_style, key):
                # Create new response_style with updated field
                data = self.response_style.dict()
                data[key] = value
                self.response_style = ResponseStyle(**data)
        elif category == "custom":
            self.custom_preferences[key] = {
                "value": value,
                "source": source.value,
                "updated_at": self.updated_at.isoformat()
            }


class CommandUsage(BaseModel):
    """Individual command usage record"""
    command_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    command: str
    category: CommandCategory
    arguments: Dict[str, Any] = Field(default_factory=dict)
    
    # Execution details
    success: bool
    execution_time_ms: float
    error_message: Optional[str] = None
    
    # Context
    context: UsageContext = UsageContext.PERSONAL
    session_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # User interaction
    user_feedback: Optional[str] = None  # "helpful", "not_helpful", etc.
    user_rating: Optional[int] = Field(None, ge=1, le=5)
    
    class Config:
        frozen = True


class UsageSession(BaseModel):
    """User session tracking"""
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    
    # Session statistics
    total_commands: int = 0
    successful_commands: int = 0
    failed_commands: int = 0
    total_execution_time_ms: float = 0
    
    # Session context
    primary_context: UsageContext = UsageContext.PERSONAL
    contexts_used: List[UsageContext] = Field(default_factory=list)
    
    # Session metadata
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    location: Optional[str] = None
    
    def add_command(self, command_usage: CommandUsage):
        """Add a command to this session"""
        self.total_commands += 1
        if command_usage.success:
            self.successful_commands += 1
        else:
            self.failed_commands += 1
        self.total_execution_time_ms += command_usage.execution_time_ms
        
        if command_usage.context not in self.contexts_used:
            self.contexts_used.append(command_usage.context)
    
    def end_session(self):
        """Mark session as ended"""
        self.end_time = datetime.utcnow()
    
    @property
    def duration_minutes(self) -> Optional[float]:
        """Session duration in minutes"""
        if not self.end_time:
            return None
        return (self.end_time - self.start_time).total_seconds() / 60
    
    @property
    def success_rate(self) -> float:
        """Command success rate percentage"""
        if self.total_commands == 0:
            return 0.0
        return (self.successful_commands / self.total_commands) * 100


class BehaviorPattern(BaseModel):
    """Detected behavior pattern"""
    pattern_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    pattern_type: BehaviorPatternType
    
    # Pattern details
    pattern_name: str
    description: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    strength: float = Field(ge=0.0, le=1.0)  # How strong/consistent the pattern is
    
    # Pattern data
    pattern_data: Dict[str, Any] = Field(default_factory=dict)
    examples: List[str] = Field(default_factory=list)
    
    # Time information
    first_observed: datetime = Field(default_factory=datetime.utcnow)
    last_observed: datetime = Field(default_factory=datetime.utcnow)
    observation_count: int = 1
    
    # Pattern lifecycle
    is_active: bool = True
    last_verified: datetime = Field(default_factory=datetime.utcnow)
    
    def update_observation(self, new_data: Dict[str, Any] = None):
        """Update pattern with new observation"""
        self.last_observed = datetime.utcnow()
        self.observation_count += 1
        
        if new_data:
            self.pattern_data.update(new_data)
    
    class Config:
        frozen = False


class PersonalizationSettings(BaseModel):
    """Settings for personalization engine"""
    user_id: str
    
    # Personalization levels
    response_personalization: bool = True
    suggestion_personalization: bool = True
    automation_personalization: bool = True
    interface_personalization: bool = True
    
    # Learning aggressiveness
    learning_rate: float = Field(default=0.1, ge=0.0, le=1.0)
    adaptation_sensitivity: float = Field(default=0.5, ge=0.0, le=1.0)
    
    # Feature flags
    auto_suggestions: bool = True
    proactive_help: bool = True
    context_awareness: bool = True
    predictive_actions: bool = False
    
    # Thresholds
    pattern_confidence_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    suggestion_frequency_limit: int = Field(default=5, ge=0, le=20)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        frozen = False


class UserProfile(BaseModel):
    """Complete user profile with all learning data"""
    user_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: Optional[str] = None
    email: Optional[str] = None
    
    # Core preferences and settings
    preferences: UserPreferences = Field(default_factory=UserPreferences)
    personalization_settings: PersonalizationSettings
    
    # Analytics and patterns
    behavior_patterns: List[BehaviorPattern] = Field(default_factory=list)
    usage_stats: Dict[str, Any] = Field(default_factory=dict)
    
    # Profile metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_active: datetime = Field(default_factory=datetime.utcnow)
    total_sessions: int = 0
    total_commands: int = 0
    
    # Profile status
    status: LearningStatus = LearningStatus.ACTIVE
    version: str = "1.0.0"
    
    def __init__(self, **data):
        # Auto-create personalization_settings if not provided
        if 'personalization_settings' not in data:
            user_id = data.get('user_id', str(uuid.uuid4()))
            data['personalization_settings'] = PersonalizationSettings(user_id=user_id)
        super().__init__(**data)
    
    def add_behavior_pattern(self, pattern: BehaviorPattern):
        """Add a new behavior pattern"""
        self.behavior_patterns.append(pattern)
        self.preferences.updated_at = datetime.utcnow()
    
    def get_active_patterns(self) -> List[BehaviorPattern]:
        """Get all active behavior patterns"""
        return [p for p in self.behavior_patterns if p.is_active]
    
    def update_activity(self):
        """Update last activity timestamp"""
        self.last_active = datetime.utcnow()
    
    class Config:
        frozen = False


class LearningData(BaseModel):
    """Aggregated learning data for analytics and insights"""
    user_id: str
    
    # Usage analytics
    total_sessions: int = 0
    total_commands: int = 0
    average_session_duration_minutes: float = 0.0
    success_rate: float = 0.0
    
    # Command analytics
    most_used_commands: List[Dict[str, Any]] = Field(default_factory=list)
    command_categories_distribution: Dict[str, int] = Field(default_factory=dict)
    peak_usage_hours: List[int] = Field(default_factory=list)
    
    # Pattern analytics
    active_patterns_count: int = 0
    pattern_types_distribution: Dict[str, int] = Field(default_factory=dict)
    confidence_scores: Dict[str, float] = Field(default_factory=dict)
    
    # Personalization effectiveness
    suggestion_acceptance_rate: float = 0.0
    personalization_satisfaction_score: float = 0.0
    adaptation_accuracy: float = 0.0
    
    # Time-based data
    data_period_start: datetime
    data_period_end: datetime
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        frozen = True


# Utility functions for schema validation and conversion
def validate_user_preferences(preferences: Dict[str, Any]) -> UserPreferences:
    """Validate and convert dictionary to UserPreferences"""
    return UserPreferences(**preferences)


def create_default_user_profile(user_id: str, username: str = None) -> UserProfile:
    """Create a default user profile with sensible defaults"""
    preferences = UserPreferences(user_id=user_id)
    personalization_settings = PersonalizationSettings(user_id=user_id)
    
    return UserProfile(
        user_id=user_id,
        username=username,
        preferences=preferences,
        personalization_settings=personalization_settings
    )


# Export all schemas
__all__ = [
    # Enums
    "ResponseTone", "ResponseVerbosity", "PreferenceSource", "UsageContext",
    "CommandCategory", "BehaviorPatternType", "LearningStatus",
    
    # Main Data Models  
    "ResponseStyle", "TimePreferences", "ToolPreferences", "PrivacySettings",
    "UserPreferences", "CommandUsage", "UsageSession", "BehaviorPattern", 
    "PersonalizationSettings", "UserProfile", "LearningData",
    
    # Utility Functions
    "validate_user_preferences", "create_default_user_profile"
]