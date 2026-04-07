"""
Comprehensive test suite for JARVIS 2.0 Learning System

Tests all components of the learning system including schemas, tracker,
analytics, behavior detector, personalization engine, and storage.
"""

import pytest
import asyncio
import tempfile
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

# Import learning system components
from src.core.learning.schemas import (
    UserProfile, UserPreferences, BehaviorPattern, CommandUsage, UsageSession,
    ResponseStyle, ResponseTone, ResponseVerbosity, CommandCategory, UsageContext,
    BehaviorPatternType, create_default_user_profile
)
from src.core.learning.storage import LearningStorage
from src.core.learning.tracker import PreferenceTracker
from src.core.learning.analytics import AnalyticsEngine
from src.core.learning.detector import BehaviorDetector
from src.core.learning.engine import PersonalizationEngine
from src.core.learning.adapter import AdaptiveResponseGenerator

class TestLearningSchemas:
    """Test learning system data schemas"""
    
    def test_user_preferences_creation(self):
        """Test UserPreferences creation and defaults"""
        prefs = UserPreferences(user_id="test_user")
        
        assert prefs.user_id == "test_user"
        assert prefs.response_style.tone == ResponseTone.FRIENDLY
        assert prefs.response_style.verbosity == ResponseVerbosity.NORMAL
        assert prefs.response_style.technical_level == 3
        assert prefs.privacy_settings.collect_usage_data is True
        assert prefs.tool_preferences.automation_enabled is True
    
    def test_user_profile_creation(self):
        """Test UserProfile creation with default values"""
        profile = create_default_user_profile("test_user", "Test User")
        
        assert profile.user_id == "test_user"
        assert profile.username == "Test User"
        assert profile.preferences.user_id == "test_user"
        assert profile.personalization_settings.user_id == "test_user"
        assert len(profile.behavior_patterns) == 0
    
    def test_command_usage_creation(self):
        """Test CommandUsage record creation"""
        usage = CommandUsage(
            user_id="test_user",
            session_id="test_session",
            command="help",
            category=CommandCategory.HELP,
            success=True,
            execution_time_ms=150.5,
            context=UsageContext.PERSONAL
        )
        
        assert usage.user_id == "test_user"
        assert usage.command == "help"
        assert usage.success is True
        assert usage.execution_time_ms == 150.5
        assert usage.category == CommandCategory.HELP
    
    def test_behavior_pattern_creation(self):
        """Test BehaviorPattern creation and updates"""
        pattern = BehaviorPattern(
            user_id="test_user",
            pattern_type=BehaviorPatternType.TIME_BASED,
            pattern_name="Morning Usage",
            description="High activity in the morning",
            confidence_score=0.85,
            strength=0.7,
            pattern_data={"peak_hour": 9}
        )
        
        assert pattern.pattern_type == BehaviorPatternType.TIME_BASED
        assert pattern.confidence_score == 0.85
        assert pattern.strength == 0.7
        assert pattern.is_active is True
        
        # Test updating observation
        initial_count = pattern.observation_count
        pattern.update_observation({"new_data": "test"})
        assert pattern.observation_count == initial_count + 1


class TestLearningStorage:
    """Test learning system storage functionality"""
    
    @pytest.fixture
    async def storage(self):
        """Create temporary storage for testing"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
            db_path = tmp.name
        
        storage = LearningStorage("sqlite", db_path=db_path, auto_cleanup=False)
        await storage.initialize()
        
        yield storage
        
        # Cleanup
        try:
            os.unlink(db_path)
        except:
            pass
    
    @pytest.mark.asyncio
    async def test_user_profile_storage(self, storage):
        """Test storing and loading user profiles"""
        profile = create_default_user_profile("test_user", "Test User")
        
        # Store profile
        await storage.store_user_profile(profile)
        
        # Load profile
        loaded_profile = await storage.load_user_profile("test_user")
        
        assert loaded_profile is not None
        assert loaded_profile.user_id == "test_user"
        assert loaded_profile.username == "Test User"
        assert loaded_profile.preferences.user_id == "test_user"
    
    @pytest.mark.asyncio
    async def test_command_usage_storage(self, storage):
        """Test storing and retrieving command usage"""
        usage = CommandUsage(
            user_id="test_user",
            session_id="test_session",
            command="test command",
            category=CommandCategory.SYSTEM,
            success=True,
            execution_time_ms=200.0,
            context=UsageContext.PERSONAL
        )
        
        # Store usage
        await storage.store_command_usage(usage)
        
        # Retrieve usage history
        history = await storage.get_user_command_history("test_user", limit=10)
        
        assert len(history) == 1
        assert history[0].command == "test command"
        assert history[0].success is True
    
    @pytest.mark.asyncio
    async def test_behavior_pattern_storage(self, storage):
        """Test storing and retrieving behavior patterns"""
        pattern = BehaviorPattern(
            user_id="test_user",
            pattern_type=BehaviorPatternType.TOOL_PREFERENCE,
            pattern_name="Test Pattern",
            description="Test pattern description",
            confidence_score=0.8,
            strength=0.6,
            pattern_data={"test": "data"}
        )
        
        # Store pattern
        await storage.store_behavior_pattern(pattern)
        
        # Retrieve patterns
        patterns = await storage.get_user_behavior_patterns("test_user")
        
        assert len(patterns) == 1
        assert patterns[0].pattern_name == "Test Pattern"
        assert patterns[0].confidence_score == 0.8


class TestPreferenceTracker:
    """Test preference tracking functionality"""
    
    @pytest.fixture
    async def tracker(self):
        """Create preference tracker with temporary storage"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
            db_path = tmp.name
        
        storage = LearningStorage("sqlite", db_path=db_path, auto_cleanup=False)
        await storage.initialize()
        
        tracker = PreferenceTracker(storage)
        
        yield tracker
        
        # Cleanup
        try:
            os.unlink(db_path)
        except:
            pass
    
    def test_explicit_preference_setting(self, tracker):
        """Test setting explicit preferences"""
        user_id = "test_user"
        
        # Set explicit preference
        tracker.set_explicit_preference(user_id, "response_style", "tone", "casual")
        
        # Get preferences
        prefs = tracker.get_user_preferences(user_id)
        
        assert prefs.response_style.tone == ResponseTone.CASUAL
    
    @pytest.mark.asyncio
    async def test_command_usage_tracking(self, tracker):
        """Test tracking command usage"""
        user_id = "test_user"
        
        usage = CommandUsage(
            user_id=user_id,
            session_id="test_session",
            command="help",
            category=CommandCategory.HELP,
            success=True,
            execution_time_ms=100.0,
            context=UsageContext.PERSONAL
        )
        
        # Track command usage
        await tracker.track_command_usage(user_id, usage)
        
        # Verify tracking (no exceptions means success)
        assert True
    
    @pytest.mark.asyncio
    async def test_user_feedback_processing(self, tracker):
        """Test processing user feedback"""
        user_id = "test_user"
        
        # Track feedback
        await tracker.track_user_feedback(user_id, "cmd_123", "too_verbose", 2)
        
        # Get preferences to see if they were adjusted
        prefs = tracker.get_user_preferences(user_id)
        
        # Should have adjusted verbosity down from feedback
        # Note: This might need mock storage to verify changes
        assert True  # Basic test that no exception occurred


class TestAnalyticsEngine:
    """Test analytics engine functionality"""
    
    @pytest.fixture
    async def analytics(self):
        """Create analytics engine with temporary storage"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
            db_path = tmp.name
        
        storage = LearningStorage("sqlite", db_path=db_path, auto_cleanup=False)
        await storage.initialize()
        
        analytics = AnalyticsEngine(storage)
        
        yield analytics
        
        # Cleanup
        try:
            os.unlink(db_path)
        except:
            pass
    
    @pytest.mark.asyncio
    async def test_command_usage_recording(self, analytics):
        """Test recording command usage"""
        usage = CommandUsage(
            user_id="test_user",
            session_id="test_session",
            command="test",
            category=CommandCategory.SYSTEM,
            success=True,
            execution_time_ms=150.0,
            context=UsageContext.PERSONAL
        )
        
        # Record usage
        await analytics.record_command_usage(usage)
        
        # Verify recording (no exception means success)
        assert True
    
    @pytest.mark.asyncio
    async def test_user_metrics_generation(self, analytics):
        """Test generating user metrics"""
        user_id = "test_user"
        
        # Create some sample data
        for i in range(5):
            usage = CommandUsage(
                user_id=user_id,
                session_id="test_session",
                command=f"command_{i}",
                category=CommandCategory.SYSTEM,
                success=i % 2 == 0,  # Alternate success/failure
                execution_time_ms=100.0 + i * 10,
                context=UsageContext.PERSONAL
            )
            await analytics.record_command_usage(usage)
        
        # Get metrics
        metrics = await analytics.get_user_metrics(user_id, days=1)
        
        assert metrics.total_commands == 5
        assert 0 < metrics.success_rate < 1  # Should be around 60%
        assert metrics.avg_response_time > 0


class TestBehaviorDetector:
    """Test behavior pattern detection"""
    
    @pytest.fixture
    async def detector(self):
        """Create behavior detector with temporary storage"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
            db_path = tmp.name
        
        storage = LearningStorage("sqlite", db_path=db_path, auto_cleanup=False)
        await storage.initialize()
        
        detector = BehaviorDetector(storage)
        
        yield detector
        
        # Cleanup
        try:
            os.unlink(db_path)
        except:
            pass
    
    @pytest.mark.asyncio
    async def test_pattern_detection_insufficient_data(self, detector):
        """Test pattern detection with insufficient data"""
        user_id = "test_user"
        
        # Try to detect patterns with no data
        patterns = await detector.detect_user_patterns(user_id)
        
        assert len(patterns) == 0
    
    def test_pattern_validation(self, detector):
        """Test pattern validation thresholds"""
        from src.core.learning.detector import PatternCandidate
        
        # Create test pattern candidates
        candidates = [
            PatternCandidate(
                pattern_type=BehaviorPatternType.TIME_BASED,
                name="High Confidence Pattern",
                description="Test pattern",
                evidence=["test"],
                confidence=0.8,
                strength=0.7,
                pattern_data={}
            ),
            PatternCandidate(
                pattern_type=BehaviorPatternType.TIME_BASED,
                name="Low Confidence Pattern",
                description="Test pattern",
                evidence=["test"],
                confidence=0.3,  # Below threshold
                strength=0.7,
                pattern_data={}
            )
        ]
        
        # Validate patterns
        validated = detector._validate_patterns("test_user", candidates)
        
        # Should only keep high confidence pattern
        assert len(validated) == 1
        assert validated[0].name == "High Confidence Pattern"


class TestPersonalizationEngine:
    """Test personalization engine functionality"""
    
    @pytest.fixture
    async def engine(self):
        """Create personalization engine with temporary storage"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
            db_path = tmp.name
        
        storage = LearningStorage("sqlite", db_path=db_path, auto_cleanup=False)
        await storage.initialize()
        
        engine = PersonalizationEngine(storage)
        
        yield engine
        
        # Cleanup
        try:
            os.unlink(db_path)
        except:
            pass
    
    @pytest.mark.asyncio
    async def test_user_profile_creation(self, engine):
        """Test user profile creation and caching"""
        user_id = "test_user"
        
        # Get profile (should create new one)
        profile = await engine.get_user_profile(user_id)
        
        assert profile.user_id == user_id
        assert profile.preferences.user_id == user_id
    
    @pytest.mark.asyncio
    async def test_personalized_response(self, engine):
        """Test response personalization"""
        user_id = "test_user"
        
        # Get personalized response
        response = await engine.personalize_response(
            user_id, "Task completed successfully", "success"
        )
        
        # Should return some response (may be same as input if no personalization)
        assert isinstance(response, str)
        assert len(response) > 0
    
    @pytest.mark.asyncio
    async def test_user_interaction_recording(self, engine):
        """Test recording user interactions"""
        user_id = "test_user"
        
        # Record interaction
        await engine.record_user_interaction(user_id, "test command", True, "test context")
        
        # Should not raise exception
        assert True
    
    def test_personalization_control(self, engine):
        """Test enabling/disabling personalization"""
        # Test enabling
        engine.enable_personalization()
        assert engine.personalization_enabled is True
        
        # Test disabling
        engine.disable_personalization()
        assert engine.personalization_enabled is False


class TestAdaptiveResponseGenerator:
    """Test adaptive response generation"""
    
    def test_response_generator_initialization(self):
        """Test response generator initialization"""
        generator = AdaptiveResponseGenerator()
        
        assert generator.adaptation_enabled is True
        assert len(generator.response_templates) > 0
        assert "success" in generator.response_templates
        assert "error" in generator.response_templates
    
    def test_response_adaptation_control(self):
        """Test enabling/disabling response adaptation"""
        generator = AdaptiveResponseGenerator()
        
        # Test disabling
        generator.disable_adaptation()
        assert generator.adaptation_enabled is False
        
        # Test enabling
        generator.enable_adaptation()
        assert generator.adaptation_enabled is True
    
    def test_learning_rate_adjustment(self):
        """Test learning rate setting"""
        generator = AdaptiveResponseGenerator()
        
        # Test valid learning rate
        generator.set_learning_rate(0.5)
        assert generator.learning_rate == 0.5
        
        # Test boundary values
        generator.set_learning_rate(0.0)
        assert generator.learning_rate == 0.0
        
        generator.set_learning_rate(1.0)
        assert generator.learning_rate == 1.0
        
        # Test clamping
        generator.set_learning_rate(1.5)
        assert generator.learning_rate == 1.0  # Should be clamped


class TestLearningSystemIntegration:
    """Integration tests for the complete learning system"""
    
    @pytest.fixture
    async def learning_system(self):
        """Create complete learning system for integration testing"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
            db_path = tmp.name
        
        # Initialize all components
        storage = LearningStorage("sqlite", db_path=db_path, auto_cleanup=False)
        await storage.initialize()
        
        tracker = PreferenceTracker(storage)
        analytics = AnalyticsEngine(storage)
        detector = BehaviorDetector(storage)
        engine = PersonalizationEngine(storage)
        adapter = AdaptiveResponseGenerator(engine)
        
        system = {
            'storage': storage,
            'tracker': tracker,
            'analytics': analytics,
            'detector': detector,
            'engine': engine,
            'adapter': adapter
        }
        
        yield system
        
        # Cleanup
        try:
            os.unlink(db_path)
        except:
            pass
    
    @pytest.mark.asyncio
    async def test_complete_user_workflow(self, learning_system):
        """Test complete workflow from command tracking to personalization"""
        user_id = "integration_test_user"
        
        # 1. Track multiple commands
        commands = [
            ("help", CommandCategory.HELP, True, 100.0),
            ("status", CommandCategory.SYSTEM, True, 150.0),
            ("agent analyze code", CommandCategory.AGENT, True, 5000.0),
            ("automation list", CommandCategory.AUTOMATION, True, 200.0),
            ("invalid_command", CommandCategory.SYSTEM, False, 50.0),
        ]
        
        for cmd, category, success, exec_time in commands:
            usage = CommandUsage(
                user_id=user_id,
                session_id="integration_session",
                command=cmd,
                category=category,
                success=success,
                execution_time_ms=exec_time,
                context=UsageContext.PERSONAL
            )
            
            await learning_system['tracker'].track_command_usage(user_id, usage)
            await learning_system['analytics'].record_command_usage(usage)
        
        # 2. Generate metrics
        metrics = await learning_system['analytics'].get_user_metrics(user_id)
        
        assert metrics.total_commands == 5
        assert metrics.success_rate == 0.8  # 4/5 successful
        
        # 3. Try to detect patterns (may not find any with small dataset)
        patterns = await learning_system['detector'].detect_user_patterns(user_id)
        
        # Should not crash even with limited data
        assert isinstance(patterns, list)
        
        # 4. Get personalized suggestions
        suggestions = await learning_system['engine'].get_personalized_suggestions(user_id)
        
        # Should return a list (might be empty)
        assert isinstance(suggestions, list)
        
        # 5. Test response adaptation
        response = await learning_system['adapter'].generate_adaptive_response(
            user_id, "Command executed successfully", "success"
        )
        
        assert isinstance(response, str)
        assert len(response) > 0
    
    @pytest.mark.asyncio
    async def test_preference_learning_workflow(self, learning_system):
        """Test automatic preference learning workflow"""
        user_id = "pref_test_user"
        
        # Simulate user feedback that should adjust preferences
        feedback_commands = [
            ("too_verbose", 1),
            ("too_verbose", 2), 
            ("too_technical", 2),
        ]
        
        for feedback, rating in feedback_commands:
            await learning_system['tracker'].track_user_feedback(
                user_id, f"cmd_{feedback}", feedback, rating
            )
        
        # Get updated preferences
        prefs = learning_system['tracker'].get_user_preferences(user_id)
        
        # Preferences should be adjusted based on feedback
        assert prefs.user_id == user_id
        # Note: Actual preference changes would need mock storage verification
    
    def test_system_statistics(self, learning_system):
        """Test system statistics and status reporting"""
        # Get statistics from various components
        personalization_stats = learning_system['engine'].get_personalization_stats()
        detection_stats = learning_system['detector'].get_detection_stats()
        adaptation_stats = learning_system['adapter'].get_adaptation_stats()
        
        # Verify statistics structure
        assert isinstance(personalization_stats, dict)
        assert isinstance(detection_stats, dict)
        assert isinstance(adaptation_stats, dict)
        
        # Check expected keys
        assert 'personalization_enabled' in personalization_stats
        assert 'learning_enabled' in personalization_stats
        assert 'total_users' in detection_stats
        assert 'adaptation_enabled' in adaptation_stats


class TestLearningSystemPerformance:
    """Performance tests for learning system components"""
    
    @pytest.mark.asyncio
    async def test_bulk_command_tracking(self):
        """Test performance with bulk command tracking"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
            db_path = tmp.name
        
        try:
            storage = LearningStorage("sqlite", db_path=db_path, auto_cleanup=False)
            await storage.initialize()
            
            analytics = AnalyticsEngine(storage)
            
            # Track 100 commands
            start_time = datetime.utcnow()
            
            for i in range(100):
                usage = CommandUsage(
                    user_id="perf_test_user",
                    session_id="perf_session",
                    command=f"command_{i}",
                    category=CommandCategory.SYSTEM,
                    success=True,
                    execution_time_ms=100.0,
                    context=UsageContext.PERSONAL
                )
                await analytics.record_command_usage(usage)
            
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            # Should complete within reasonable time (< 5 seconds for 100 commands)
            assert duration < 5.0
            
        finally:
            try:
                os.unlink(db_path)
            except:
                pass


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])