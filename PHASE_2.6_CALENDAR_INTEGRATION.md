# JARVIS 2.0 - Calendar Integration Plugin Documentation

## Overview

The Calendar Integration Plugin provides comprehensive calendar management with Google Calendar and Outlook/Exchange support. It includes AI-powered scheduling assistance, meeting optimization, and intelligent calendar analysis.

## Features

### Core Calendar Operations
- **Multi-Provider Support**: Google Calendar via Google API, Outlook/Exchange via EWS  
- **Event Management**: Create, read, update, delete calendar events
- **Calendar Listing**: View and manage multiple calendars
- **Advanced Filtering**: Complex event filtering and search capabilities
- **Real-time Operations**: Async operations for responsive performance

### Smart Scheduling
- **Free Time Finding**: Automatically identify available meeting slots
- **Meeting Suggestions**: AI-powered optimal meeting time recommendations  
- **Availability Analysis**: Analyze participant availability patterns
- **Conflict Detection**: Identify and resolve scheduling conflicts
- **Time Zone Handling**: Intelligent multi-timezone scheduling

### AI-Powered Features
- **Calendar Pattern Analysis**: Identify usage patterns and optimize schedules
- **Meeting Optimization**: Suggest better meeting times based on preferences
- **Workload Analysis**: Analyze meeting load and productivity patterns
- **Smart Reminders**: Context-aware reminder suggestions
- **Attendee Insights**: Analyze meeting participant patterns

## Installation

### Dependencies

```bash
# Install required packages
pip install google-auth google-auth-oauthlib google-api-python-client exchangelib icalendar
```

### Google Calendar Setup

1. **Create Google Cloud Project**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing
   - Enable Google Calendar API

2. **Create OAuth 2.0 Credentials**:
   - Go to APIs & Services → Credentials
   - Create OAuth 2.0 client ID (Desktop application)
   - Download credentials JSON file

3. **Configure JARVIS**:
   ```python
   # Setup Google Calendar
   result = await calendar_tool.execute(
       action="setup_google",
       credentials={
           "credentials_file": "path/to/credentials.json",
           "token_file": "path/to/google_calendar_token.json"
       }
   )
   ```

### Outlook Calendar Setup

1. **Exchange Server Setup**:
   ```python
   # Setup Outlook/Exchange
   result = await calendar_tool.execute(
       action="setup_outlook", 
       credentials={
           "email": "your-email@company.com",
           "password": "your-password",
           "server": "exchange.company.com"  # Optional for Outlook.com
       }
   )
   ```

## Usage Examples

### Basic Operations

```python
from src.plugins.calendar_integration import CalendarIntegrationTool

# Create tool instance
calendar_tool = CalendarIntegrationTool()

# Setup Google Calendar (one-time)
await calendar_tool.execute(
    action="setup_google",
    credentials={"credentials_file": "credentials.json"}
)

# List calendars
calendars_result = await calendar_tool.execute(
    action="list_calendars",
    provider="google"
)

# List upcoming events
events_result = await calendar_tool.execute(
    action="list_events",
    provider="google",
    filter={
        "time_min": "2024-01-15T00:00:00Z",
        "time_max": "2024-01-22T23:59:59Z",
        "max_results": 20
    }
)
```

### Event Management

```python
# Create new event
new_event = {
    "title": "Team Standup",
    "description": "Daily team synchronization meeting",
    "start_time": "2024-01-15T09:00:00Z",
    "end_time": "2024-01-15T09:30:00Z",
    "location": "Conference Room A",
    "attendees": [
        {
            "email": "teammate1@company.com",
            "name": "John Doe",
            "optional": False
        },
        {
            "email": "teammate2@company.com", 
            "name": "Jane Smith",
            "optional": False
        }
    ],
    "reminders": [
        {"method": "popup", "minutes": 10},
        {"method": "email", "minutes": 60}
    ],
    "recurrence": {
        "rules": ["RRULE:FREQ=DAILY;BYDAY=MO,TU,WE,TH,FR"]
    }
}

result = await calendar_tool.execute(
    action="create_event",
    provider="google",
    calendar_id="primary",
    event_data=new_event
)

# Update existing event
update_data = {
    "title": "Updated Team Standup",
    "location": "Conference Room B"
}

result = await calendar_tool.execute(
    action="update_event",
    provider="google",
    event_id="event123",
    calendar_id="primary",
    event_data=update_data
)

# Delete event
result = await calendar_tool.execute(
    action="delete_event",
    provider="google",
    event_id="event123",
    calendar_id="primary"
)
```

### Advanced Filtering and Search

```python
# Complex filtering
filter_criteria = {
    "calendar_ids": ["primary", "work@company.com"],
    "time_min": "2024-01-01T00:00:00Z",
    "time_max": "2024-01-31T23:59:59Z",
    "text_query": "project meeting",
    "attendee_email": "manager@company.com",
    "status": "confirmed",
    "max_results": 50,
    "show_deleted": False
}

result = await calendar_tool.execute(
    action="list_events",
    provider="google",
    filter=filter_criteria
)

# Search events by text
search_result = await calendar_tool.execute(
    action="search_events",
    provider="google",
    query="quarterly review",
    filter={"max_results": 25}
)
```

### Smart Scheduling

```python
# Find available meeting slots
meeting_requirements = {
    "duration_minutes": 60,
    "attendee_emails": ["alice@company.com", "bob@company.com"],
    "business_hours_start": 9,
    "business_hours_end": 17,
    "days_ahead": 14,
    "preferred_times": ["morning", "early_afternoon"],
    "avoid_lunch_hours": True
}

result = await calendar_tool.execute(
    action="find_free_time",
    provider="google",
    meeting_data=meeting_requirements
)

# Get AI meeting time suggestions
suggestion_result = await calendar_tool.execute(
    action="suggest_meeting_times",
    meeting_data={
        "attendee_emails": ["team@company.com"],
        "duration_minutes": 90,
        "context": "Sprint planning session",
        "preferred_times": ["morning"],
        "meeting_type": "recurring"
    }
)

# Analyze availability patterns
availability_result = await calendar_tool.execute(
    action="get_availability",
    provider="google",
    meeting_data={
        "attendee_emails": ["alice@company.com", "bob@company.com"],
        "time_range": {
            "start": "2024-01-15T00:00:00Z",
            "end": "2024-01-19T23:59:59Z"
        }
    }
)
```

### Calendar Analytics

```python
# Analyze calendar patterns
analysis_result = await calendar_tool.execute(
    action="analyze_patterns",
    provider="google",
    filter={
        "time_min": "2024-01-01T00:00:00Z",
        "time_max": "2024-01-31T23:59:59Z",
        "calendar_ids": ["primary"]
    }
)

# Expected response structure:
{
    "success": True,
    "analysis": {
        "total_events": 45,
        "total_meeting_hours": 67.5,
        "avg_meeting_duration": 90,  # minutes
        "busiest_day": "Tuesday",
        "busiest_hour": "14:00",
        "meeting_days_distribution": {
            "Monday": 8,
            "Tuesday": 12,
            "Wednesday": 10,
            "Thursday": 9,
            "Friday": 6
        },
        "meeting_hours_distribution": {
            "9": 5,
            "10": 8,
            "11": 6,
            "14": 12,
            "15": 8,
            "16": 6
        },
        "insights": [
            "Peak meeting time is 2:00 PM",
            "Tuesday is your busiest meeting day",
            "Average meeting duration suggests efficient scheduling"
        ]
    }
}
```

## Data Structures

### CalendarEvent

```python
@dataclass
class CalendarEvent:
    id: str                              # Unique event identifier
    title: str                           # Event title/summary
    description: Optional[str]           # Event description
    start_time: datetime                 # Event start time
    end_time: datetime                   # Event end time
    location: Optional[str]              # Event location
    attendees: List[Dict[str, Any]]      # List of attendees
    organizer: Optional[Dict[str, str]]  # Event organizer
    status: EventStatus                  # Event status (confirmed/tentative/cancelled)
    privacy: EventPrivacy                # Privacy level (public/private/confidential)
    calendar_id: str                     # Parent calendar ID
    is_all_day: bool                     # All-day event flag
    timezone: str                        # Event timezone
    recurrence: Optional[Dict[str, Any]] # Recurrence rules
    reminders: List[Dict[str, Any]]      # Reminder settings
    meeting_link: Optional[str]          # Video meeting URL
    attachments: List[Dict[str, Any]]    # File attachments
```

### CalendarFilter

```python
@dataclass
class CalendarFilter:
    calendar_ids: Optional[List[str]] = None      # Filter by specific calendars
    time_min: Optional[datetime] = None           # Start time filter
    time_max: Optional[datetime] = None           # End time filter
    text_query: Optional[str] = None              # Text search query
    attendee_email: Optional[str] = None          # Filter by attendee
    status: Optional[EventStatus] = None          # Filter by event status
    max_results: int = 100                        # Maximum results to return
    show_deleted: bool = False                    # Include deleted events
```

### TimeSlot

```python
@dataclass
class TimeSlot:
    start_time: datetime     # Slot start time
    end_time: datetime       # Slot end time
    duration_minutes: int    # Slot duration in minutes
```

## CLI Integration

### Available Commands

```bash
# Setup calendar providers
JARVIS> calendar setup google --credentials-file credentials.json
JARVIS> calendar setup outlook --email user@company.com --password secret

# List calendars and events
JARVIS> calendar list-calendars --provider google
JARVIS> calendar list-events --this-week --max-results 20
JARVIS> calendar search "team meeting" --next-month

# Create and manage events  
JARVIS> calendar create-event --title "Project Review" --start "2024-01-15T14:00:00" --duration 90 --attendees alice@company.com,bob@company.com
JARVIS> calendar update-event --event-id abc123 --location "Conference Room B"
JARVIS> calendar delete-event --event-id abc123

# Smart scheduling
JARVIS> calendar find-free-time --duration 60 --attendees alice@company.com,bob@company.com --next-2-weeks
JARVIS> calendar suggest-meeting --duration 90 --attendees team@company.com --context "Sprint planning"
JARVIS> calendar check-availability --attendees alice@company.com,bob@company.com --date 2024-01-15

# Analytics and insights
JARVIS> calendar analyze-patterns --last-month
JARVIS> calendar meeting-stats --this-quarter
JARVIS> calendar optimize-schedule --suggestions
```

## API Reference

### Actions

| Action | Description | Required Parameters |
|--------|-------------|-------------------|
| `setup_google` | Configure Google Calendar access | `credentials` |
| `setup_outlook` | Configure Outlook Calendar access | `credentials` |
| `list_calendars` | List available calendars | `provider` |
| `list_events` | List events with filtering | `provider`, `filter` (optional) |
| `create_event` | Create new calendar event | `provider`, `event_data` |
| `update_event` | Update existing event | `provider`, `event_id`, `event_data` |
| `delete_event` | Delete calendar event | `provider`, `event_id`, `calendar_id` |
| `search_events` | Search events by text query | `provider`, `query` |
| `find_free_time` | Find available meeting slots | `provider`, `meeting_data` |
| `suggest_meeting_times` | AI meeting time suggestions | `meeting_data` |
| `analyze_patterns` | Analyze calendar usage patterns | `provider`, `filter` |
| `get_availability` | Check attendee availability | `provider`, `meeting_data` |
| `schedule_meeting` | Schedule optimized meeting | `provider`, `meeting_data` |

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `action` | string | Action to perform (required) |
| `provider` | string | Calendar provider: "google" or "outlook" |
| `credentials` | object | Authentication credentials |
| `filter` | object | Event filtering criteria |
| `event_data` | object | Event data for creation/updating |
| `event_id` | string | Specific event ID for operations |
| `calendar_id` | string | Calendar ID for operations |
| `query` | string | Search query string |
| `meeting_data` | object | Meeting scheduling requirements |

### Response Format

```python
# Success response
{
    "success": True,
    "data": {...},           # Operation-specific data
    "message": "...",        # Success message
    "provider": "google"     # Provider used
}

# Error response  
{
    "success": False,
    "error": "Error message",
    "details": {...}         # Error details (optional)
}
```

## Security & Privacy

### Authentication
- **Google Calendar**: OAuth 2.0 with scope-limited access
- **Outlook**: Username/password or modern authentication
- **Token Storage**: Secure local token caching
- **Credential Protection**: No plaintext password storage

### Privacy Features  
- **Local Processing**: All data processed locally
- **No Data Sharing**: Calendar data never sent to external services
- **Secure Storage**: Encrypted token storage
- **Minimal Permissions**: Request only required calendar scopes

### Security Best Practices
1. Use OAuth 2.0 for Google Calendar (preferred)
2. Enable 2FA on calendar accounts
3. Use app-specific passwords when possible
4. Regularly rotate credentials
5. Monitor calendar access logs
6. Review and limit app permissions

## Performance Optimization

### Caching Strategy
- **Token Caching**: Avoid repeated authentication
- **Event Caching**: Cache frequently accessed events
- **Calendar Metadata**: Store calendar information locally
- **Query Optimization**: Optimize API calls and filtering

### Async Operations
- **Non-blocking Calls**: All operations use async/await
- **Batch Processing**: Group related operations
- **Connection Pooling**: Reuse API connections
- **Rate Limiting**: Respect provider API limits

### Memory Management
- **Efficient Parsing**: Stream large calendar datasets
- **Pagination**: Handle large result sets appropriately
- **Resource Cleanup**: Properly dispose of resources
- **Memory Limits**: Set reasonable memory usage bounds

## Error Handling

### Common Issues

1. **Authentication Failures**
   ```python
   # Check credentials and permissions
   if not result["success"]:
       if "authentication" in result["error"].lower():
           print("Please verify your credentials and permissions")
   ```

2. **API Rate Limits**
   ```python
   # Implement retry with exponential backoff
   if "rate limit" in result["error"].lower():
       await asyncio.sleep(60)  # Wait before retry
   ```

3. **Time Zone Issues**
   ```python
   # Always use timezone-aware datetimes
   from datetime import datetime, timezone
   
   start_time = datetime.now(timezone.utc)
   event_data = {
       "start_time": start_time.isoformat(),
       "timezone": "UTC"
   }
   ```

### Error Codes

| Error Type | Description | Solution |
|------------|-------------|----------|
| `AUTH_FAILED` | Authentication failed | Check credentials and scopes |
| `PERMISSION_DENIED` | Insufficient permissions | Update OAuth permissions |
| `RATE_LIMITED` | API rate limit exceeded | Implement backoff strategy |
| `NOT_FOUND` | Event/calendar not found | Verify IDs and permissions |
| `INVALID_TIME` | Invalid time format | Use ISO 8601 format |
| `CONFLICT` | Scheduling conflict | Check availability first |

## Testing

### Unit Tests
```bash
# Run calendar integration tests
python -m pytest tests/test_calendar_integration.py -v
```

### Integration Tests
```bash  
# Test with real calendar accounts (requires setup)
python -m pytest tests/test_calendar_integration.py::TestCalendarIntegrationFull -v
```

### Mock Testing
```python
# Use mock providers for testing
with patch('src.plugins.calendar_integration.CALENDAR_DEPS_AVAILABLE', True):
    # Mock calendar operations
    calendar_tool.google_manager.authenticate = AsyncMock(return_value=True)
    calendar_tool.google_manager.get_events = AsyncMock(return_value=[])
```

## Troubleshooting

### Google Calendar Issues
1. **Enable Calendar API** in Google Cloud Console
2. **Check OAuth Scopes** - ensure calendar permissions are granted
3. **Verify Credentials File** - download fresh credentials if needed
4. **Token Refresh** - delete token file to force re-authentication
5. **Check Quotas** - verify API usage limits

### Outlook Calendar Issues  
1. **Check Exchange Server** - verify server address and connectivity
2. **Enable EWS** - ensure Exchange Web Services are enabled
3. **App Passwords** - use app-specific passwords if 2FA is enabled
4. **Modern Auth** - configure OAuth 2.0 if available
5. **Firewall Rules** - check network connectivity

### General Issues
1. **Check Dependencies** - ensure all packages are installed correctly
2. **Time Zone Handling** - verify timezone configurations
3. **Date Format** - use ISO 8601 format for all dates
4. **API Limits** - monitor and respect rate limiting
5. **Log Analysis** - check JARVIS logs for detailed error messages

## Future Enhancements

### Planned Features
- [ ] **iCalendar Support**: Import/export .ics files
- [ ] **Room Booking**: Integration with room booking systems
- [ ] **Travel Time**: Automatic travel time calculation
- [ ] **Weather Integration**: Weather-aware scheduling
- [ ] **Multi-account Support**: Handle multiple calendar accounts
- [ ] **Offline Mode**: Basic functionality without internet

### AI Enhancements
- [ ] **Smart Scheduling**: ML-based optimal meeting scheduling
- [ ] **Preference Learning**: Learn user scheduling preferences
- [ ] **Conflict Prediction**: Predict and prevent scheduling conflicts
- [ ] **Meeting Insights**: Analyze meeting effectiveness
- [ ] **Workload Optimization**: Balance meeting loads automatically
- [ ] **Natural Language**: Parse natural language scheduling requests

### Integration Features
- [ ] **Email Integration**: Create events from emails automatically
- [ ] **Task Management**: Convert events to tasks and vice versa
- [ ] **CRM Integration**: Connect with customer relationship systems
- [ ] **Project Management**: Link events with project milestones
- [ ] **Communication Tools**: Integrate with Slack, Teams, Discord
- [ ] **Mobile Sync**: Mobile device synchronization

---

## Support

For issues and feature requests, please check:
- JARVIS 2.0 Documentation
- GitHub Issues
- Community Discord

**Last Updated**: April 2026  
**Version**: 2.6.0  
**Author**: JARVIS 2.0 Development Team