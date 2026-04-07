"""
JARVIS 2.0 - Calendar Integration Plugin
Advanced Google Calendar & Outlook Calendar integration with AI scheduling
"""

import asyncio
import json
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import uuid

try:
    import httpx
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import Flow
    from googleapiclient.discovery import build
    import exchangelib
    from icalendar import Calendar as ICalCalendar, Event as ICalEvent
    CALENDAR_DEPS_AVAILABLE = True
except ImportError:
    CALENDAR_DEPS_AVAILABLE = False

from src.core.tools.base import BaseTool, ToolParameter
from src.core.logger import logger


class CalendarProvider(Enum):
    """Calendar provider types."""
    GOOGLE = "google"
    OUTLOOK = "outlook"
    ICALENDAR = "icalendar"


class EventStatus(Enum):
    """Event status types."""
    CONFIRMED = "confirmed"
    TENTATIVE = "tentative"
    CANCELLED = "cancelled"


class EventPrivacy(Enum):
    """Event privacy levels."""
    PUBLIC = "public"
    PRIVATE = "private"
    CONFIDENTIAL = "confidential"


class AttendeeStatus(Enum):
    """Attendee response status."""
    NEEDS_ACTION = "needsAction"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    TENTATIVE = "tentative"


class RecurrenceFrequency(Enum):
    """Recurrence frequency options."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


@dataclass
class CalendarEvent:
    """Calendar event data structure."""
    id: str
    title: str
    description: Optional[str]
    start_time: datetime
    end_time: datetime
    location: Optional[str]
    attendees: List[Dict[str, Any]]
    organizer: Optional[Dict[str, str]]
    status: EventStatus
    privacy: EventPrivacy
    calendar_id: str
    is_all_day: bool
    timezone: str
    recurrence: Optional[Dict[str, Any]]
    reminders: List[Dict[str, Any]]
    meeting_link: Optional[str]
    attachments: List[Dict[str, Any]]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "location": self.location,
            "attendees": self.attendees,
            "organizer": self.organizer,
            "status": self.status.value,
            "privacy": self.privacy.value,
            "calendar_id": self.calendar_id,
            "is_all_day": self.is_all_day,
            "timezone": self.timezone,
            "recurrence": self.recurrence,
            "reminders": self.reminders,
            "meeting_link": self.meeting_link,
            "attachments": self.attachments
        }


@dataclass
class CalendarFilter:
    """Calendar filtering criteria."""
    calendar_ids: Optional[List[str]] = None
    time_min: Optional[datetime] = None
    time_max: Optional[datetime] = None
    text_query: Optional[str] = None
    attendee_email: Optional[str] = None
    status: Optional[EventStatus] = None
    max_results: int = 100
    show_deleted: bool = False


@dataclass
class TimeSlot:
    """Available time slot."""
    start_time: datetime
    end_time: datetime
    duration_minutes: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "duration_minutes": self.duration_minutes
        }


class GoogleCalendarManager:
    """Google Calendar API integration manager."""
    
    def __init__(self):
        self.service = None
        self.credentials = None
        self.scopes = [
            'https://www.googleapis.com/auth/calendar',
            'https://www.googleapis.com/auth/calendar.events'
        ]
    
    async def authenticate(self, credentials_path: str, token_path: str) -> bool:
        """Authenticate with Google Calendar API."""
        try:
            # Load existing token
            if os.path.exists(token_path):
                self.credentials = Credentials.from_authorized_user_file(token_path, self.scopes)
            
            # If there are no valid credentials, authenticate
            if not self.credentials or not self.credentials.valid:
                if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                    self.credentials.refresh(Request())
                else:
                    flow = Flow.from_client_secrets_file(credentials_path, self.scopes)
                    flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
                    
                    auth_url, _ = flow.authorization_url(prompt='consent')
                    logger.info(f"Please visit: {auth_url}")
                    
                    code = input("Enter authorization code: ")
                    flow.fetch_token(code=code)
                    self.credentials = flow.credentials
                
                # Save credentials
                with open(token_path, 'w') as token_file:
                    token_file.write(self.credentials.to_json())
            
            self.service = build('calendar', 'v3', credentials=self.credentials)
            return True
            
        except Exception as e:
            logger.error(f"Google Calendar authentication failed: {e}")
            return False
    
    async def get_calendars(self) -> List[Dict[str, Any]]:
        """Get list of available calendars."""
        try:
            result = self.service.calendarList().list().execute()
            return result.get('items', [])
        except Exception as e:
            logger.error(f"Failed to get calendars: {e}")
            return []
    
    async def get_events(self, filter_criteria: CalendarFilter) -> List[CalendarEvent]:
        """Get events based on filter criteria."""
        try:
            events = []
            
            # Get calendar IDs to search
            calendar_ids = filter_criteria.calendar_ids
            if not calendar_ids:
                calendars = await self.get_calendars()
                calendar_ids = [cal['id'] for cal in calendars]
            
            # Search each calendar
            for calendar_id in calendar_ids:
                # Build query parameters
                query_params = {
                    'calendarId': calendar_id,
                    'maxResults': filter_criteria.max_results,
                    'singleEvents': True,
                    'orderBy': 'startTime',
                    'showDeleted': filter_criteria.show_deleted
                }
                
                if filter_criteria.time_min:
                    query_params['timeMin'] = filter_criteria.time_min.isoformat()
                if filter_criteria.time_max:
                    query_params['timeMax'] = filter_criteria.time_max.isoformat()
                if filter_criteria.text_query:
                    query_params['q'] = filter_criteria.text_query
                
                # Execute query
                result = self.service.events().list(**query_params).execute()
                calendar_events = result.get('items', [])
                
                # Parse events
                for event_data in calendar_events:
                    parsed_event = self._parse_google_event(event_data, calendar_id)
                    if parsed_event:
                        # Apply additional filters
                        if self._event_matches_filter(parsed_event, filter_criteria):
                            events.append(parsed_event)
            
            return events[:filter_criteria.max_results]
            
        except Exception as e:
            logger.error(f"Failed to get Google Calendar events: {e}")
            return []
    
    def _parse_google_event(self, event_data: Dict, calendar_id: str) -> Optional[CalendarEvent]:
        """Parse Google Calendar event data."""
        try:
            # Parse start and end times
            start_data = event_data.get('start', {})
            end_data = event_data.get('end', {})
            
            # Handle all-day events
            if 'date' in start_data:
                start_time = datetime.fromisoformat(start_data['date']).replace(tzinfo=timezone.utc)
                end_time = datetime.fromisoformat(end_data['date']).replace(tzinfo=timezone.utc)
                is_all_day = True
                event_timezone = 'UTC'
            else:
                start_time = datetime.fromisoformat(start_data['dateTime'].replace('Z', '+00:00'))
                end_time = datetime.fromisoformat(end_data['dateTime'].replace('Z', '+00:00'))
                is_all_day = False
                event_timezone = start_data.get('timeZone', 'UTC')
            
            # Parse attendees
            attendees = []
            for attendee_data in event_data.get('attendees', []):
                attendees.append({
                    'email': attendee_data.get('email', ''),
                    'name': attendee_data.get('displayName', ''),
                    'status': attendee_data.get('responseStatus', 'needsAction'),
                    'optional': attendee_data.get('optional', False)
                })
            
            # Parse organizer
            organizer_data = event_data.get('organizer', {})
            organizer = {
                'email': organizer_data.get('email', ''),
                'name': organizer_data.get('displayName', '')
            } if organizer_data else None
            
            # Parse reminders
            reminders = []
            reminder_data = event_data.get('reminders', {})
            if reminder_data.get('useDefault'):
                reminders.append({'method': 'default', 'minutes': 10})
            else:
                for override in reminder_data.get('overrides', []):
                    reminders.append({
                        'method': override.get('method', 'popup'),
                        'minutes': override.get('minutes', 10)
                    })
            
            # Parse recurrence
            recurrence = None
            if 'recurrence' in event_data:
                recurrence = {
                    'rules': event_data['recurrence']
                }
            
            # Get meeting link
            meeting_link = None
            if 'conferenceData' in event_data:
                for entry_point in event_data['conferenceData'].get('entryPoints', []):
                    if entry_point.get('entryPointType') == 'video':
                        meeting_link = entry_point.get('uri')
                        break
            
            # Parse attachments
            attachments = []
            for attachment in event_data.get('attachments', []):
                attachments.append({
                    'title': attachment.get('title', ''),
                    'file_url': attachment.get('fileUrl', ''),
                    'mime_type': attachment.get('mimeType', '')
                })
            
            return CalendarEvent(
                id=event_data['id'],
                title=event_data.get('summary', 'Untitled Event'),
                description=event_data.get('description', ''),
                start_time=start_time,
                end_time=end_time,
                location=event_data.get('location', ''),
                attendees=attendees,
                organizer=organizer,
                status=EventStatus(event_data.get('status', 'confirmed')),
                privacy=EventPrivacy(event_data.get('visibility', 'public')),
                calendar_id=calendar_id,
                is_all_day=is_all_day,
                timezone=event_timezone,
                recurrence=recurrence,
                reminders=reminders,
                meeting_link=meeting_link,
                attachments=attachments
            )
            
        except Exception as e:
            logger.error(f"Failed to parse Google Calendar event: {e}")
            return None
    
    async def create_event(self, event: CalendarEvent) -> Optional[str]:
        """Create a new calendar event."""
        try:
            # Build event data
            event_data = {
                'summary': event.title,
                'description': event.description or '',
                'location': event.location or '',
                'status': event.status.value
            }
            
            # Set start and end times
            if event.is_all_day:
                event_data['start'] = {'date': event.start_time.date().isoformat()}
                event_data['end'] = {'date': event.end_time.date().isoformat()}
            else:
                event_data['start'] = {
                    'dateTime': event.start_time.isoformat(),
                    'timeZone': event.timezone
                }
                event_data['end'] = {
                    'dateTime': event.end_time.isoformat(),
                    'timeZone': event.timezone
                }
            
            # Add attendees
            if event.attendees:
                event_data['attendees'] = [
                    {
                        'email': attendee['email'],
                        'displayName': attendee.get('name', ''),
                        'optional': attendee.get('optional', False)
                    }
                    for attendee in event.attendees
                ]
            
            # Add reminders
            if event.reminders:
                event_data['reminders'] = {
                    'useDefault': False,
                    'overrides': [
                        {
                            'method': reminder.get('method', 'popup'),
                            'minutes': reminder.get('minutes', 10)
                        }
                        for reminder in event.reminders
                    ]
                }
            
            # Add recurrence
            if event.recurrence:
                event_data['recurrence'] = event.recurrence.get('rules', [])
            
            # Create event
            result = self.service.events().insert(
                calendarId=event.calendar_id or 'primary',
                body=event_data
            ).execute()
            
            return result.get('id')
            
        except Exception as e:
            logger.error(f"Failed to create Google Calendar event: {e}")
            return None
    
    async def update_event(self, event: CalendarEvent) -> bool:
        """Update an existing calendar event."""
        try:
            # Get existing event
            existing_event = self.service.events().get(
                calendarId=event.calendar_id,
                eventId=event.id
            ).execute()
            
            # Update fields
            existing_event.update({
                'summary': event.title,
                'description': event.description or '',
                'location': event.location or '',
                'status': event.status.value
            })
            
            # Update times
            if event.is_all_day:
                existing_event['start'] = {'date': event.start_time.date().isoformat()}
                existing_event['end'] = {'date': event.end_time.date().isoformat()}
            else:
                existing_event['start'] = {
                    'dateTime': event.start_time.isoformat(),
                    'timeZone': event.timezone
                }
                existing_event['end'] = {
                    'dateTime': event.end_time.isoformat(),
                    'timeZone': event.timezone
                }
            
            # Update event
            self.service.events().update(
                calendarId=event.calendar_id,
                eventId=event.id,
                body=existing_event
            ).execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update Google Calendar event: {e}")
            return False
    
    async def delete_event(self, calendar_id: str, event_id: str) -> bool:
        """Delete a calendar event."""
        try:
            self.service.events().delete(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()
            return True
        except Exception as e:
            logger.error(f"Failed to delete Google Calendar event: {e}")
            return False
    
    def _event_matches_filter(self, event: CalendarEvent, filter_criteria: CalendarFilter) -> bool:
        """Check if event matches additional filter criteria."""
        if filter_criteria.attendee_email:
            if not any(attendee['email'] == filter_criteria.attendee_email 
                      for attendee in event.attendees):
                return False
        
        if filter_criteria.status and event.status != filter_criteria.status:
            return False
        
        return True


class OutlookCalendarManager:
    """Outlook Calendar integration manager."""
    
    def __init__(self):
        self.account = None
    
    async def authenticate(self, email: str, password: str, server: str = None) -> bool:
        """Authenticate with Outlook/Exchange."""
        try:
            if server:
                config = exchangelib.Configuration(
                    server=server,
                    credentials=exchangelib.Credentials(email, password)
                )
            else:
                config = exchangelib.Configuration(
                    server='outlook.office365.com',
                    credentials=exchangelib.Credentials(email, password)
                )
            
            self.account = exchangelib.Account(
                email,
                config=config,
                autodiscover=not server
            )
            
            # Test connection
            list(self.account.calendar.all().only('subject')[:1])
            return True
            
        except Exception as e:
            logger.error(f"Outlook Calendar authentication failed: {e}")
            return False
    
    async def get_events(self, filter_criteria: CalendarFilter) -> List[CalendarEvent]:
        """Get events from Outlook Calendar."""
        try:
            calendar = self.account.calendar
            
            # Build query
            query = calendar.all()
            
            # Apply time filters
            if filter_criteria.time_min:
                query = query.filter(start__gte=filter_criteria.time_min)
            if filter_criteria.time_max:
                query = query.filter(end__lte=filter_criteria.time_max)
            
            # Apply text query
            if filter_criteria.text_query:
                query = query.filter(subject__icontains=filter_criteria.text_query)
            
            # Get events
            events = []
            for item in query[:filter_criteria.max_results]:
                parsed_event = self._parse_outlook_event(item)
                if parsed_event:
                    events.append(parsed_event)
            
            return events
            
        except Exception as e:
            logger.error(f"Failed to get Outlook Calendar events: {e}")
            return []
    
    def _parse_outlook_event(self, event_item) -> Optional[CalendarEvent]:
        """Parse Outlook calendar event."""
        try:
            # Parse attendees
            attendees = []
            for attendee in event_item.required_attendees or []:
                attendees.append({
                    'email': str(attendee.mailbox.email_address),
                    'name': str(attendee.mailbox.name),
                    'status': 'needsAction',
                    'optional': False
                })
            
            for attendee in event_item.optional_attendees or []:
                attendees.append({
                    'email': str(attendee.mailbox.email_address),
                    'name': str(attendee.mailbox.name),
                    'status': 'needsAction',
                    'optional': True
                })
            
            # Parse organizer
            organizer = None
            if event_item.organizer:
                organizer = {
                    'email': str(event_item.organizer.email_address),
                    'name': str(event_item.organizer.name)
                }
            
            return CalendarEvent(
                id=event_item.id,
                title=event_item.subject or 'Untitled Event',
                description=event_item.text_body or '',
                start_time=event_item.start,
                end_time=event_item.end,
                location=event_item.location or '',
                attendees=attendees,
                organizer=organizer,
                status=EventStatus.CONFIRMED,  # Default for Outlook
                privacy=EventPrivacy.PUBLIC,   # Default for Outlook
                calendar_id='primary',
                is_all_day=event_item.is_all_day,
                timezone=str(event_item.start.tzinfo),
                recurrence=None,  # TODO: Parse recurrence
                reminders=[],     # TODO: Parse reminders
                meeting_link=None,
                attachments=[]
            )
            
        except Exception as e:
            logger.error(f"Failed to parse Outlook event: {e}")
            return None


class CalendarAI:
    """AI-powered calendar features."""
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
    
    async def find_meeting_slots(
        self, 
        events: List[CalendarEvent],
        duration_minutes: int,
        business_hours_start: int = 9,
        business_hours_end: int = 17,
        days_ahead: int = 14
    ) -> List[TimeSlot]:
        """Find available meeting slots."""
        try:
            available_slots = []
            
            # Generate time range
            start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + timedelta(days=days_ahead)
            
            # Check each day
            current_date = start_date
            while current_date < end_date:
                # Skip weekends
                if current_date.weekday() >= 5:
                    current_date += timedelta(days=1)
                    continue
                
                # Find free slots during business hours
                day_start = current_date.replace(hour=business_hours_start)
                day_end = current_date.replace(hour=business_hours_end)
                
                # Get events for this day
                day_events = [
                    event for event in events
                    if event.start_time.date() == current_date.date()
                    and event.status != EventStatus.CANCELLED
                ]
                
                # Sort events by start time
                day_events.sort(key=lambda e: e.start_time)
                
                # Find gaps between events
                current_time = day_start
                
                for event in day_events:
                    # Check if there's a gap before this event
                    if (event.start_time - current_time).total_seconds() >= duration_minutes * 60:
                        slot_end = min(event.start_time, current_time + timedelta(minutes=duration_minutes))
                        if (slot_end - current_time).total_seconds() >= duration_minutes * 60:
                            available_slots.append(TimeSlot(
                                start_time=current_time,
                                end_time=slot_end,
                                duration_minutes=int((slot_end - current_time).total_seconds() // 60)
                            ))
                    
                    current_time = max(current_time, event.end_time)
                
                # Check for gap at end of day
                if (day_end - current_time).total_seconds() >= duration_minutes * 60:
                    available_slots.append(TimeSlot(
                        start_time=current_time,
                        end_time=current_time + timedelta(minutes=duration_minutes),
                        duration_minutes=duration_minutes
                    ))
                
                current_date += timedelta(days=1)
            
            return available_slots
            
        except Exception as e:
            logger.error(f"Failed to find meeting slots: {e}")
            return []
    
    async def suggest_meeting_times(
        self,
        attendee_emails: List[str],
        duration_minutes: int,
        preferred_times: Optional[List[str]] = None,
        context: str = ""
    ) -> Dict[str, Any]:
        """AI-powered meeting time suggestions."""
        try:
            prompt = f"""
            Suggest optimal meeting times based on:
            - Duration: {duration_minutes} minutes
            - Attendees: {', '.join(attendee_emails)}
            - Preferred times: {preferred_times or 'None specified'}
            - Context: {context}
            
            Consider:
            - Time zones (assume business hours)
            - Meeting type and urgency
            - Common availability patterns
            
            Return JSON with suggested times and reasoning.
            Format: {{"suggestions": [{{"time": "ISO datetime", "reasoning": "why this time"}}]}}
            """
            
            response = await self.llm_client.chat([{"role": "user", "content": prompt}])
            
            try:
                return json.loads(response.strip())
            except json.JSONDecodeError:
                return {"suggestions": [], "error": "Failed to parse AI response"}
                
        except Exception as e:
            logger.error(f"Failed to get AI meeting suggestions: {e}")
            return {"suggestions": [], "error": str(e)}
    
    async def analyze_calendar_patterns(self, events: List[CalendarEvent]) -> Dict[str, Any]:
        """Analyze calendar usage patterns."""
        try:
            if not events:
                return {"error": "No events to analyze"}
            
            # Basic statistics
            total_events = len(events)
            total_meeting_hours = sum(
                (event.end_time - event.start_time).total_seconds() / 3600
                for event in events
            )
            
            # Meeting patterns
            meeting_days = {}
            meeting_hours = {}
            
            for event in events:
                day = event.start_time.strftime('%A')
                hour = event.start_time.hour
                
                meeting_days[day] = meeting_days.get(day, 0) + 1
                meeting_hours[hour] = meeting_hours.get(hour, 0) + 1
            
            # Busiest day and hour
            busiest_day = max(meeting_days, key=meeting_days.get) if meeting_days else 'None'
            busiest_hour = max(meeting_hours, key=meeting_hours.get) if meeting_hours else 0
            
            return {
                "total_events": total_events,
                "total_meeting_hours": round(total_meeting_hours, 2),
                "avg_meeting_duration": round(total_meeting_hours / total_events * 60, 1) if total_events > 0 else 0,
                "busiest_day": busiest_day,
                "busiest_hour": f"{busiest_hour}:00",
                "meeting_days_distribution": meeting_days,
                "meeting_hours_distribution": meeting_hours
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze calendar patterns: {e}")
            return {"error": str(e)}


class CalendarIntegrationTool(BaseTool):
    """Comprehensive calendar integration tool."""
    
    name = "calendar_integration"
    description = "Advanced calendar management with Google Calendar/Outlook integration and AI scheduling"
    
    def __init__(self):
        super().__init__()
        self.google_manager = GoogleCalendarManager()
        self.outlook_manager = OutlookCalendarManager()
        self.calendar_ai = None
        self.active_provider = None
    
    def get_parameters(self) -> Dict[str, ToolParameter]:
        """Get tool parameters."""
        return {
            "action": ToolParameter(
                name="action",
                type="string",
                description="Action to perform",
                required=True,
                enum=[
                    "setup_google", "setup_outlook", "list_calendars", "list_events",
                    "create_event", "update_event", "delete_event", "search_events",
                    "find_free_time", "suggest_meeting_times", "analyze_patterns",
                    "get_availability", "schedule_meeting", "send_invitations"
                ]
            ),
            "provider": ToolParameter(
                name="provider",
                type="string",
                description="Calendar provider (google/outlook)",
                required=False,
                enum=["google", "outlook"],
                default="google"
            ),
            "credentials": ToolParameter(
                name="credentials",
                type="object",
                description="Authentication credentials",
                required=False
            ),
            "filter": ToolParameter(
                name="filter",
                type="object",
                description="Event filtering criteria",
                required=False
            ),
            "event_data": ToolParameter(
                name="event_data",
                type="object",
                description="Event data for creation/updating",
                required=False
            ),
            "event_id": ToolParameter(
                name="event_id",
                type="string",
                description="Event ID for specific operations",
                required=False
            ),
            "calendar_id": ToolParameter(
                name="calendar_id",
                type="string",
                description="Calendar ID for operations",
                required=False
            ),
            "query": ToolParameter(
                name="query",
                type="string",
                description="Search query",
                required=False
            ),
            "meeting_data": ToolParameter(
                name="meeting_data",
                type="object",
                description="Meeting scheduling data",
                required=False
            )
        }
    
    async def execute(
        self,
        action: str,
        provider: str = "google",
        credentials: Optional[Dict] = None,
        filter: Optional[Dict] = None,
        event_data: Optional[Dict] = None,
        event_id: Optional[str] = None,
        calendar_id: Optional[str] = None,
        query: Optional[str] = None,
        meeting_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Execute calendar integration action."""
        if not CALENDAR_DEPS_AVAILABLE:
            return {
                "success": False,
                "error": "Calendar dependencies not installed. Run: pip install google-auth google-auth-oauthlib google-api-python-client exchangelib icalendar"
            }
        
        try:
            if action == "setup_google":
                return await self._setup_google(credentials)
            elif action == "setup_outlook":
                return await self._setup_outlook(credentials)
            elif action == "list_calendars":
                return await self._list_calendars(provider)
            elif action == "list_events":
                return await self._list_events(provider, filter)
            elif action == "create_event":
                return await self._create_event(provider, event_data, calendar_id)
            elif action == "update_event":
                return await self._update_event(provider, event_id, event_data, calendar_id)
            elif action == "delete_event":
                return await self._delete_event(provider, event_id, calendar_id)
            elif action == "search_events":
                return await self._search_events(provider, query, filter)
            elif action == "find_free_time":
                return await self._find_free_time(provider, meeting_data)
            elif action == "suggest_meeting_times":
                return await self._suggest_meeting_times(meeting_data)
            elif action == "analyze_patterns":
                return await self._analyze_patterns(provider, filter)
            elif action == "get_availability":
                return await self._get_availability(provider, meeting_data)
            elif action == "schedule_meeting":
                return await self._schedule_meeting(provider, meeting_data)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
                
        except Exception as e:
            logger.error(f"Calendar integration error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _setup_google(self, credentials: Dict) -> Dict[str, Any]:
        """Set up Google Calendar authentication."""
        try:
            credentials_path = credentials.get('credentials_file', 'credentials.json')
            token_path = credentials.get('token_file', 'google_calendar_token.json')
            
            success = await self.google_manager.authenticate(credentials_path, token_path)
            
            if success:
                self.active_provider = CalendarProvider.GOOGLE
                return {
                    "success": True,
                    "message": "Google Calendar authentication successful",
                    "provider": "google"
                }
            else:
                return {
                    "success": False,
                    "error": "Google Calendar authentication failed"
                }
                
        except Exception as e:
            return {"success": False, "error": f"Google Calendar setup error: {str(e)}"}
    
    async def _setup_outlook(self, credentials: Dict) -> Dict[str, Any]:
        """Set up Outlook Calendar authentication."""
        try:
            email = credentials.get('email')
            password = credentials.get('password')
            server = credentials.get('server')
            
            if not email or not password:
                return {"success": False, "error": "Email and password required for Outlook"}
            
            success = await self.outlook_manager.authenticate(email, password, server)
            
            if success:
                self.active_provider = CalendarProvider.OUTLOOK
                return {
                    "success": True,
                    "message": "Outlook Calendar authentication successful",
                    "provider": "outlook"
                }
            else:
                return {
                    "success": False,
                    "error": "Outlook Calendar authentication failed"
                }
                
        except Exception as e:
            return {"success": False, "error": f"Outlook Calendar setup error: {str(e)}"}
    
    async def _list_calendars(self, provider: str) -> Dict[str, Any]:
        """List available calendars."""
        try:
            if provider == "google":
                calendars = await self.google_manager.get_calendars()
                return {
                    "success": True,
                    "calendars": calendars,
                    "count": len(calendars),
                    "provider": provider
                }
            else:
                return {
                    "success": False,
                    "error": "Outlook calendar listing not yet implemented"
                }
                
        except Exception as e:
            return {"success": False, "error": f"Failed to list calendars: {str(e)}"}
    
    async def _list_events(self, provider: str, filter_dict: Optional[Dict]) -> Dict[str, Any]:
        """List calendar events with filtering."""
        try:
            # Parse filter
            calendar_filter = self._parse_filter(filter_dict)
            
            # Get manager
            if provider == "google":
                manager = self.google_manager
            else:
                manager = self.outlook_manager
            
            # Get events
            events = await manager.get_events(calendar_filter)
            
            return {
                "success": True,
                "events": [event.to_dict() for event in events],
                "count": len(events),
                "provider": provider
            }
            
        except Exception as e:
            return {"success": False, "error": f"Failed to list events: {str(e)}"}
    
    def _parse_filter(self, filter_dict: Optional[Dict]) -> CalendarFilter:
        """Parse filter dictionary into CalendarFilter object."""
        if not filter_dict:
            return CalendarFilter()
        
        # Parse dates
        time_min = None
        time_max = None
        
        if filter_dict.get('time_min'):
            try:
                time_min = datetime.fromisoformat(filter_dict['time_min'])
            except ValueError:
                pass
        
        if filter_dict.get('time_max'):
            try:
                time_max = datetime.fromisoformat(filter_dict['time_max'])
            except ValueError:
                pass
        
        # Parse status
        status = None
        if filter_dict.get('status'):
            try:
                status = EventStatus(filter_dict['status'])
            except ValueError:
                pass
        
        return CalendarFilter(
            calendar_ids=filter_dict.get('calendar_ids'),
            time_min=time_min,
            time_max=time_max,
            text_query=filter_dict.get('text_query'),
            attendee_email=filter_dict.get('attendee_email'),
            status=status,
            max_results=filter_dict.get('max_results', 100),
            show_deleted=filter_dict.get('show_deleted', False)
        )
    
    # Additional methods would be implemented here...
    async def _create_event(self, provider: str, event_data: Dict, calendar_id: str) -> Dict[str, Any]:
        """Create calendar event (placeholder)."""
        return {"success": False, "error": "Event creation not yet implemented"}
    
    async def _find_free_time(self, provider: str, meeting_data: Dict) -> Dict[str, Any]:
        """Find free time slots (placeholder)."""
        return {"success": False, "error": "Free time finding not yet implemented"}


# Export the tool
__all__ = ['CalendarIntegrationTool']