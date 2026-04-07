"""
Tests for Calendar Integration Plugin
"""

import pytest
import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from src.plugins.calendar_integration import (
    CalendarIntegrationTool,
    CalendarEvent,
    CalendarFilter,
    TimeSlot,
    CalendarProvider,
    EventStatus,
    EventPrivacy,
    AttendeeStatus,
    GoogleCalendarManager,
    OutlookCalendarManager,
    CalendarAI
)


class TestCalendarEvent:
    """Test CalendarEvent data structure."""
    
    def test_calendar_event_creation(self):
        """Test creating a CalendarEvent."""
        now = datetime.now(timezone.utc)
        event = CalendarEvent(
            id="123",
            title="Test Meeting",
            description="Test description",
            start_time=now,
            end_time=now + timedelta(hours=1),
            location="Conference Room A",
            attendees=[{
                'email': 'attendee@example.com',
                'name': 'John Doe',
                'status': 'accepted',
                'optional': False
            }],
            organizer={'email': 'organizer@example.com', 'name': 'Jane Smith'},
            status=EventStatus.CONFIRMED,
            privacy=EventPrivacy.PUBLIC,
            calendar_id="primary",
            is_all_day=False,
            timezone="UTC",
            recurrence=None,
            reminders=[{'method': 'popup', 'minutes': 10}],
            meeting_link="https://meet.google.com/abc-def-ghi",
            attachments=[]
        )
        
        assert event.id == "123"
        assert event.title == "Test Meeting"
        assert event.location == "Conference Room A"
        assert event.status == EventStatus.CONFIRMED
        assert event.privacy == EventPrivacy.PUBLIC
        assert not event.is_all_day
        assert len(event.attendees) == 1
        assert event.attendees[0]['email'] == 'attendee@example.com'
    
    def test_calendar_event_to_dict(self):
        """Test converting CalendarEvent to dictionary."""
        now = datetime.now(timezone.utc)
        event = CalendarEvent(
            id="123",
            title="Test Meeting",
            description="Test description",
            start_time=now,
            end_time=now + timedelta(hours=1),
            location="Room A",
            attendees=[],
            organizer=None,
            status=EventStatus.CONFIRMED,
            privacy=EventPrivacy.PUBLIC,
            calendar_id="primary",
            is_all_day=False,
            timezone="UTC",
            recurrence=None,
            reminders=[],
            meeting_link=None,
            attachments=[]
        )
        
        result = event.to_dict()
        
        assert result["id"] == "123"
        assert result["title"] == "Test Meeting"
        assert result["location"] == "Room A"
        assert result["status"] == "confirmed"
        assert result["privacy"] == "public"
        assert result["is_all_day"] is False
        assert result["calendar_id"] == "primary"


class TestCalendarFilter:
    """Test CalendarFilter functionality."""
    
    def test_calendar_filter_defaults(self):
        """Test default CalendarFilter values."""
        filter_obj = CalendarFilter()
        
        assert filter_obj.calendar_ids is None
        assert filter_obj.time_min is None
        assert filter_obj.time_max is None
        assert filter_obj.text_query is None
        assert filter_obj.attendee_email is None
        assert filter_obj.status is None
        assert filter_obj.max_results == 100
        assert filter_obj.show_deleted is False
    
    def test_calendar_filter_with_values(self):
        """Test CalendarFilter with specific values."""
        time_min = datetime.now(timezone.utc)
        time_max = time_min + timedelta(days=7)
        
        filter_obj = CalendarFilter(
            calendar_ids=["primary", "work"],
            time_min=time_min,
            time_max=time_max,
            text_query="meeting",
            attendee_email="test@example.com",
            status=EventStatus.CONFIRMED,
            max_results=50,
            show_deleted=True
        )
        
        assert filter_obj.calendar_ids == ["primary", "work"]
        assert filter_obj.time_min == time_min
        assert filter_obj.time_max == time_max
        assert filter_obj.text_query == "meeting"
        assert filter_obj.attendee_email == "test@example.com"
        assert filter_obj.status == EventStatus.CONFIRMED
        assert filter_obj.max_results == 50
        assert filter_obj.show_deleted is True


class TestTimeSlot:
    """Test TimeSlot functionality."""
    
    def test_time_slot_creation(self):
        """Test creating a TimeSlot."""
        start_time = datetime.now(timezone.utc)
        end_time = start_time + timedelta(minutes=30)
        
        slot = TimeSlot(
            start_time=start_time,
            end_time=end_time,
            duration_minutes=30
        )
        
        assert slot.start_time == start_time
        assert slot.end_time == end_time
        assert slot.duration_minutes == 30
    
    def test_time_slot_to_dict(self):
        """Test converting TimeSlot to dictionary."""
        start_time = datetime.now(timezone.utc)
        end_time = start_time + timedelta(minutes=45)
        
        slot = TimeSlot(
            start_time=start_time,
            end_time=end_time,
            duration_minutes=45
        )
        
        result = slot.to_dict()
        
        assert result["start_time"] == start_time.isoformat()
        assert result["end_time"] == end_time.isoformat()
        assert result["duration_minutes"] == 45


class TestGoogleCalendarManager:
    """Test Google Calendar integration manager."""
    
    @pytest.fixture
    def google_manager(self):
        """Create GoogleCalendarManager instance."""
        return GoogleCalendarManager()
    
    def test_init(self, google_manager):
        """Test GoogleCalendarManager initialization."""
        assert google_manager.service is None
        assert google_manager.credentials is None
        assert len(google_manager.scopes) == 2
    
    @patch('src.plugins.calendar_integration.os.path.exists')
    @patch('src.plugins.calendar_integration.Credentials.from_authorized_user_file')
    @patch('src.plugins.calendar_integration.build')
    async def test_authenticate_existing_token(
        self, 
        mock_build, 
        mock_credentials, 
        mock_exists,
        google_manager
    ):
        """Test authentication with existing valid token."""
        mock_exists.return_value = True
        mock_creds = MagicMock()
        mock_creds.valid = True
        mock_credentials.return_value = mock_creds
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        
        result = await google_manager.authenticate("creds.json", "token.json")
        
        assert result is True
        assert google_manager.service == mock_service
        assert google_manager.credentials == mock_creds
    
    def test_parse_google_event(self, google_manager):
        """Test parsing Google Calendar event data."""
        # Mock Google Calendar API event format
        mock_event_data = {
            'id': '123',
            'summary': 'Test Event',
            'description': 'Test description',
            'location': 'Test Location',
            'status': 'confirmed',
            'visibility': 'public',
            'start': {
                'dateTime': '2024-01-15T10:00:00Z',
                'timeZone': 'UTC'
            },
            'end': {
                'dateTime': '2024-01-15T11:00:00Z',
                'timeZone': 'UTC'
            },
            'attendees': [
                {
                    'email': 'attendee@example.com',
                    'displayName': 'Test Attendee',
                    'responseStatus': 'accepted',
                    'optional': False
                }
            ],
            'organizer': {
                'email': 'organizer@example.com',
                'displayName': 'Test Organizer'
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': 10}
                ]
            }
        }
        
        result = google_manager._parse_google_event(mock_event_data, 'primary')
        
        assert result is not None
        assert result.id == '123'
        assert result.title == 'Test Event'
        assert result.description == 'Test description'
        assert result.location == 'Test Location'
        assert result.status == EventStatus.CONFIRMED
        assert result.privacy == EventPrivacy.PUBLIC
        assert result.calendar_id == 'primary'
        assert not result.is_all_day
        assert len(result.attendees) == 1
        assert result.attendees[0]['email'] == 'attendee@example.com'
        assert result.organizer['email'] == 'organizer@example.com'
        assert len(result.reminders) == 1
        assert result.reminders[0]['minutes'] == 10
    
    def test_parse_all_day_event(self, google_manager):
        """Test parsing all-day Google Calendar event."""
        mock_event_data = {
            'id': '456',
            'summary': 'All Day Event',
            'status': 'confirmed',
            'start': {'date': '2024-01-15'},
            'end': {'date': '2024-01-16'},
            'attendees': []
        }
        
        result = google_manager._parse_google_event(mock_event_data, 'primary')
        
        assert result is not None
        assert result.is_all_day is True
        assert result.timezone == 'UTC'
    
    def test_event_matches_filter(self, google_manager):
        """Test event filtering logic."""
        now = datetime.now(timezone.utc)
        event = CalendarEvent(
            id="123",
            title="Test Event",
            description="",
            start_time=now,
            end_time=now + timedelta(hours=1),
            location="",
            attendees=[{'email': 'test@example.com', 'name': '', 'status': 'accepted', 'optional': False}],
            organizer=None,
            status=EventStatus.CONFIRMED,
            privacy=EventPrivacy.PUBLIC,
            calendar_id="primary",
            is_all_day=False,
            timezone="UTC",
            recurrence=None,
            reminders=[],
            meeting_link=None,
            attachments=[]
        )
        
        # Test attendee filter match
        filter_with_attendee = CalendarFilter(attendee_email='test@example.com')
        assert google_manager._event_matches_filter(event, filter_with_attendee) is True
        
        # Test attendee filter no match
        filter_no_attendee = CalendarFilter(attendee_email='other@example.com')
        assert google_manager._event_matches_filter(event, filter_no_attendee) is False
        
        # Test status filter match
        filter_status_match = CalendarFilter(status=EventStatus.CONFIRMED)
        assert google_manager._event_matches_filter(event, filter_status_match) is True
        
        # Test status filter no match
        filter_status_no_match = CalendarFilter(status=EventStatus.CANCELLED)
        assert google_manager._event_matches_filter(event, filter_status_no_match) is False


class TestOutlookCalendarManager:
    """Test Outlook Calendar integration manager."""
    
    @pytest.fixture
    def outlook_manager(self):
        """Create OutlookCalendarManager instance."""
        return OutlookCalendarManager()
    
    def test_init(self, outlook_manager):
        """Test OutlookCalendarManager initialization."""
        assert outlook_manager.account is None
    
    @patch('src.plugins.calendar_integration.exchangelib.Configuration')
    @patch('src.plugins.calendar_integration.exchangelib.Credentials')
    @patch('src.plugins.calendar_integration.exchangelib.Account')
    async def test_authenticate_outlook(
        self, 
        mock_account,
        mock_credentials, 
        mock_config,
        outlook_manager
    ):
        """Test Outlook authentication."""
        mock_account_instance = MagicMock()
        mock_calendar = MagicMock()
        mock_account_instance.calendar = mock_calendar
        mock_calendar.all.return_value.only.return_value.__getitem__ = lambda self, key: []
        mock_account.return_value = mock_account_instance
        
        result = await outlook_manager.authenticate(
            "test@outlook.com", 
            "password"
        )
        
        assert result is True
        assert outlook_manager.account == mock_account_instance
    
    def test_parse_outlook_event(self, outlook_manager):
        """Test parsing Outlook event."""
        # Mock Outlook event
        mock_event = MagicMock()
        mock_event.id = "outlook123"
        mock_event.subject = "Outlook Meeting"
        mock_event.text_body = "Meeting description"
        mock_event.location = "Conference Room B"
        mock_event.start = datetime.now(timezone.utc)
        mock_event.end = datetime.now(timezone.utc) + timedelta(hours=1)
        mock_event.is_all_day = False
        mock_event.start.tzinfo = timezone.utc
        
        # Mock attendees
        mock_required_attendee = MagicMock()
        mock_required_attendee.mailbox.email_address = "required@example.com"
        mock_required_attendee.mailbox.name = "Required Attendee"
        
        mock_optional_attendee = MagicMock()
        mock_optional_attendee.mailbox.email_address = "optional@example.com"
        mock_optional_attendee.mailbox.name = "Optional Attendee"
        
        mock_event.required_attendees = [mock_required_attendee]
        mock_event.optional_attendees = [mock_optional_attendee]
        
        # Mock organizer
        mock_event.organizer = MagicMock()
        mock_event.organizer.email_address = "organizer@example.com"
        mock_event.organizer.name = "Meeting Organizer"
        
        result = outlook_manager._parse_outlook_event(mock_event)
        
        assert result is not None
        assert result.id == "outlook123"
        assert result.title == "Outlook Meeting"
        assert result.description == "Meeting description"
        assert result.location == "Conference Room B"
        assert result.status == EventStatus.CONFIRMED
        assert result.privacy == EventPrivacy.PUBLIC
        assert result.calendar_id == "primary"
        assert not result.is_all_day
        
        # Check attendees
        assert len(result.attendees) == 2
        required_attendee = next(a for a in result.attendees if not a['optional'])
        optional_attendee = next(a for a in result.attendees if a['optional'])
        
        assert required_attendee['email'] == "required@example.com"
        assert optional_attendee['email'] == "optional@example.com"
        
        # Check organizer
        assert result.organizer['email'] == "organizer@example.com"


class TestCalendarAI:
    """Test AI-powered calendar features."""
    
    @pytest.fixture
    def calendar_ai(self):
        """Create CalendarAI instance."""
        mock_llm = AsyncMock()
        return CalendarAI(mock_llm)
    
    @pytest.fixture
    def sample_events(self):
        """Create sample calendar events."""
        now = datetime.now(timezone.utc)
        return [
            CalendarEvent(
                id="1",
                title="Morning Standup",
                description="Daily team standup",
                start_time=now.replace(hour=9, minute=0),
                end_time=now.replace(hour=9, minute=30),
                location="",
                attendees=[],
                organizer=None,
                status=EventStatus.CONFIRMED,
                privacy=EventPrivacy.PUBLIC,
                calendar_id="primary",
                is_all_day=False,
                timezone="UTC",
                recurrence=None,
                reminders=[],
                meeting_link=None,
                attachments=[]
            ),
            CalendarEvent(
                id="2",
                title="Project Review",
                description="Quarterly project review",
                start_time=now.replace(hour=14, minute=0),
                end_time=now.replace(hour=15, minute=30),
                location="Conference Room A",
                attendees=[],
                organizer=None,
                status=EventStatus.CONFIRMED,
                privacy=EventPrivacy.PUBLIC,
                calendar_id="primary",
                is_all_day=False,
                timezone="UTC",
                recurrence=None,
                reminders=[],
                meeting_link=None,
                attachments=[]
            )
        ]
    
    async def test_find_meeting_slots(self, calendar_ai, sample_events):
        """Test finding available meeting slots."""
        duration_minutes = 60
        
        result = await calendar_ai.find_meeting_slots(
            sample_events,
            duration_minutes,
            business_hours_start=9,
            business_hours_end=17,
            days_ahead=1
        )
        
        # Should find slots between existing meetings
        assert len(result) > 0
        
        # Check that slots have correct duration
        for slot in result:
            assert slot.duration_minutes >= duration_minutes
            assert isinstance(slot, TimeSlot)
    
    async def test_suggest_meeting_times(self, calendar_ai):
        """Test AI meeting time suggestions."""
        calendar_ai.llm_client.chat = AsyncMock(
            return_value='{"suggestions": [{"time": "2024-01-15T10:00:00Z", "reasoning": "Morning slot available"}]}'
        )
        
        result = await calendar_ai.suggest_meeting_times(
            attendee_emails=["test1@example.com", "test2@example.com"],
            duration_minutes=60,
            preferred_times=["morning"],
            context="Team meeting"
        )
        
        assert "suggestions" in result
        assert len(result["suggestions"]) == 1
        assert result["suggestions"][0]["time"] == "2024-01-15T10:00:00Z"
        assert "reasoning" in result["suggestions"][0]
        
        calendar_ai.llm_client.chat.assert_called_once()
    
    async def test_analyze_calendar_patterns(self, calendar_ai, sample_events):
        """Test calendar pattern analysis."""
        result = await calendar_ai.analyze_calendar_patterns(sample_events)
        
        assert "total_events" in result
        assert result["total_events"] == 2
        
        assert "total_meeting_hours" in result
        assert result["total_meeting_hours"] > 0
        
        assert "avg_meeting_duration" in result
        assert "busiest_day" in result
        assert "busiest_hour" in result
        assert "meeting_days_distribution" in result
        assert "meeting_hours_distribution" in result
    
    async def test_analyze_empty_calendar(self, calendar_ai):
        """Test pattern analysis with no events."""
        result = await calendar_ai.analyze_calendar_patterns([])
        
        assert "error" in result
        assert result["error"] == "No events to analyze"


class TestCalendarIntegrationTool:
    """Test main CalendarIntegrationTool."""
    
    @pytest.fixture
    def calendar_tool(self):
        """Create CalendarIntegrationTool instance."""
        return CalendarIntegrationTool()
    
    def test_init(self, calendar_tool):
        """Test tool initialization."""
        assert calendar_tool.name == "calendar_integration"
        assert "calendar management" in calendar_tool.description.lower()
        assert calendar_tool.google_manager is not None
        assert calendar_tool.outlook_manager is not None
        assert calendar_tool.active_provider is None
    
    def test_get_parameters(self, calendar_tool):
        """Test parameter definitions."""
        params = calendar_tool.get_parameters()
        
        assert "action" in params
        assert params["action"].required is True
        assert "setup_google" in params["action"].enum
        assert "create_event" in params["action"].enum
        
        assert "provider" in params
        assert params["provider"].default == "google"
        
        assert "credentials" in params
        assert "event_data" in params
        assert "filter" in params
    
    @patch('src.plugins.calendar_integration.CALENDAR_DEPS_AVAILABLE', False)
    async def test_execute_no_deps(self, calendar_tool):
        """Test execution without dependencies."""
        result = await calendar_tool.execute("setup_google")
        
        assert result["success"] is False
        assert "dependencies not installed" in result["error"]
    
    async def test_execute_unknown_action(self, calendar_tool):
        """Test execution with unknown action."""
        with patch('src.plugins.calendar_integration.CALENDAR_DEPS_AVAILABLE', True):
            result = await calendar_tool.execute("unknown_action")
            
            assert result["success"] is False
            assert "Unknown action" in result["error"]
    
    def test_parse_filter(self, calendar_tool):
        """Test filter parsing."""
        filter_dict = {
            "calendar_ids": ["primary", "work"],
            "time_min": "2024-01-01T00:00:00Z",
            "time_max": "2024-12-31T23:59:59Z",
            "text_query": "meeting",
            "attendee_email": "test@example.com",
            "status": "confirmed",
            "max_results": 50,
            "show_deleted": True
        }
        
        result = calendar_tool._parse_filter(filter_dict)
        
        assert result.calendar_ids == ["primary", "work"]
        assert result.time_min is not None
        assert result.time_max is not None
        assert result.text_query == "meeting"
        assert result.attendee_email == "test@example.com"
        assert result.status == EventStatus.CONFIRMED
        assert result.max_results == 50
        assert result.show_deleted is True
    
    def test_parse_filter_empty(self, calendar_tool):
        """Test parsing empty filter."""
        result = calendar_tool._parse_filter(None)
        
        assert result.calendar_ids is None
        assert result.max_results == 100  # default
    
    def test_parse_filter_invalid_dates(self, calendar_tool):
        """Test parsing filter with invalid dates."""
        filter_dict = {
            "time_min": "invalid-date",
            "time_max": "also-invalid",
            "status": "invalid-status"
        }
        
        result = calendar_tool._parse_filter(filter_dict)
        
        assert result.time_min is None
        assert result.time_max is None
        assert result.status is None
    
    async def test_setup_google_success(self, calendar_tool):
        """Test successful Google Calendar setup."""
        with patch('src.plugins.calendar_integration.CALENDAR_DEPS_AVAILABLE', True):
            calendar_tool.google_manager.authenticate = AsyncMock(return_value=True)
            
            credentials = {
                "credentials_file": "creds.json",
                "token_file": "token.json"
            }
            
            result = await calendar_tool._setup_google(credentials)
            
            assert result["success"] is True
            assert result["provider"] == "google"
            assert calendar_tool.active_provider == CalendarProvider.GOOGLE
    
    async def test_setup_google_failure(self, calendar_tool):
        """Test failed Google Calendar setup."""
        with patch('src.plugins.calendar_integration.CALENDAR_DEPS_AVAILABLE', True):
            calendar_tool.google_manager.authenticate = AsyncMock(return_value=False)
            
            result = await calendar_tool._setup_google({})
            
            assert result["success"] is False
            assert "authentication failed" in result["error"]
    
    async def test_setup_outlook_success(self, calendar_tool):
        """Test successful Outlook Calendar setup."""
        with patch('src.plugins.calendar_integration.CALENDAR_DEPS_AVAILABLE', True):
            calendar_tool.outlook_manager.authenticate = AsyncMock(return_value=True)
            
            credentials = {
                "email": "test@outlook.com",
                "password": "password123"
            }
            
            result = await calendar_tool._setup_outlook(credentials)
            
            assert result["success"] is True
            assert result["provider"] == "outlook"
            assert calendar_tool.active_provider == CalendarProvider.OUTLOOK
    
    async def test_setup_outlook_missing_creds(self, calendar_tool):
        """Test Outlook setup with missing credentials."""
        with patch('src.plugins.calendar_integration.CALENDAR_DEPS_AVAILABLE', True):
            result = await calendar_tool._setup_outlook({})
            
            assert result["success"] is False
            assert "Email and password required" in result["error"]
    
    async def test_list_calendars(self, calendar_tool):
        """Test listing calendars."""
        with patch('src.plugins.calendar_integration.CALENDAR_DEPS_AVAILABLE', True):
            mock_calendars = [
                {"id": "primary", "summary": "Primary Calendar"},
                {"id": "work", "summary": "Work Calendar"}
            ]
            
            calendar_tool.google_manager.get_calendars = AsyncMock(return_value=mock_calendars)
            
            result = await calendar_tool._list_calendars("google")
            
            assert result["success"] is True
            assert result["count"] == 2
            assert result["provider"] == "google"
            assert len(result["calendars"]) == 2
            assert result["calendars"][0]["id"] == "primary"
    
    async def test_list_events(self, calendar_tool):
        """Test listing events."""
        with patch('src.plugins.calendar_integration.CALENDAR_DEPS_AVAILABLE', True):
            now = datetime.now(timezone.utc)
            mock_events = [
                CalendarEvent(
                    id="1",
                    title="Test Event",
                    description="",
                    start_time=now,
                    end_time=now + timedelta(hours=1),
                    location="",
                    attendees=[],
                    organizer=None,
                    status=EventStatus.CONFIRMED,
                    privacy=EventPrivacy.PUBLIC,
                    calendar_id="primary",
                    is_all_day=False,
                    timezone="UTC",
                    recurrence=None,
                    reminders=[],
                    meeting_link=None,
                    attachments=[]
                )
            ]
            
            calendar_tool.google_manager.get_events = AsyncMock(return_value=mock_events)
            
            result = await calendar_tool._list_events("google", {})
            
            assert result["success"] is True
            assert result["count"] == 1
            assert result["provider"] == "google"
            assert len(result["events"]) == 1
            assert result["events"][0]["id"] == "1"


# Integration Tests
class TestCalendarIntegrationFull:
    """Full integration tests for calendar functionality."""
    
    @pytest.fixture
    def calendar_tool(self):
        """Create fully configured calendar tool."""
        tool = CalendarIntegrationTool()
        return tool
    
    @pytest.mark.asyncio
    async def test_full_workflow_google(self, calendar_tool):
        """Test complete Google Calendar workflow."""
        with patch('src.plugins.calendar_integration.CALENDAR_DEPS_AVAILABLE', True):
            # Mock all dependencies
            calendar_tool.google_manager.authenticate = AsyncMock(return_value=True)
            calendar_tool.google_manager.get_calendars = AsyncMock(return_value=[])
            calendar_tool.google_manager.get_events = AsyncMock(return_value=[])
            
            # Setup
            setup_result = await calendar_tool.execute(
                "setup_google",
                credentials={"credentials_file": "test_creds.json"}
            )
            assert setup_result["success"] is True
            
            # List calendars
            calendars_result = await calendar_tool.execute(
                "list_calendars",
                provider="google"
            )
            assert calendars_result["success"] is True
            
            # List events
            events_result = await calendar_tool.execute(
                "list_events",
                provider="google",
                filter={"max_results": 10}
            )
            assert events_result["success"] is True


if __name__ == "__main__":
    pytest.main([__file__])