"""
JARVIS 2.0 - Email Integration Plugin
Advanced Gmail & Outlook integration with AI-powered features
"""

import asyncio
import json
import re
import os
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum

try:
    import httpx
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import Flow
    from googleapiclient.discovery import build
    import exchangelib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    EMAIL_DEPS_AVAILABLE = True
except ImportError:
    EMAIL_DEPS_AVAILABLE = False

from src.core.tools.base import BaseTool, ToolParameter
from src.core.logger import logger


class EmailProvider(Enum):
    """Email provider types."""
    GMAIL = "gmail"
    OUTLOOK = "outlook"
    GENERIC_IMAP = "imap"


class EmailPriority(Enum):
    """Email priority levels."""
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


@dataclass
class EmailMessage:
    """Email message data structure."""
    id: str
    subject: str
    sender: str
    recipients: List[str]
    body: str
    html_body: Optional[str]
    timestamp: datetime
    is_read: bool
    priority: EmailPriority
    labels: List[str]
    attachments: List[Dict[str, Any]]
    thread_id: Optional[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "subject": self.subject,
            "sender": self.sender,
            "recipients": self.recipients,
            "body": self.body,
            "html_body": self.html_body,
            "timestamp": self.timestamp.isoformat(),
            "is_read": self.is_read,
            "priority": self.priority.value,
            "labels": self.labels,
            "attachments": self.attachments,
            "thread_id": self.thread_id
        }


@dataclass
class EmailFilter:
    """Email filtering criteria."""
    sender: Optional[str] = None
    subject_contains: Optional[str] = None
    body_contains: Optional[str] = None
    has_attachments: Optional[bool] = None
    is_unread: Optional[bool] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    labels: Optional[List[str]] = None
    priority: Optional[EmailPriority] = None
    max_results: int = 50


class GmailManager:
    """Gmail API integration manager."""
    
    def __init__(self):
        self.service = None
        self.credentials = None
        self.scopes = [
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/gmail.send',
            'https://www.googleapis.com/auth/gmail.modify'
        ]
    
    async def authenticate(self, credentials_path: str, token_path: str) -> bool:
        """Authenticate with Gmail API."""
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
            
            self.service = build('gmail', 'v1', credentials=self.credentials)
            return True
            
        except Exception as e:
            logger.error(f"Gmail authentication failed: {e}")
            return False
    
    async def get_messages(self, filter_criteria: EmailFilter) -> List[EmailMessage]:
        """Get messages based on filter criteria."""
        try:
            # Build Gmail query
            query_parts = []
            
            if filter_criteria.sender:
                query_parts.append(f"from:{filter_criteria.sender}")
            if filter_criteria.subject_contains:
                query_parts.append(f"subject:{filter_criteria.subject_contains}")
            if filter_criteria.body_contains:
                query_parts.append(f"{filter_criteria.body_contains}")
            if filter_criteria.has_attachments:
                query_parts.append("has:attachment")
            if filter_criteria.is_unread:
                query_parts.append("is:unread")
            if filter_criteria.date_from:
                query_parts.append(f"after:{filter_criteria.date_from.strftime('%Y/%m/%d')}")
            if filter_criteria.date_to:
                query_parts.append(f"before:{filter_criteria.date_to.strftime('%Y/%m/%d')}")
            if filter_criteria.labels:
                for label in filter_criteria.labels:
                    query_parts.append(f"label:{label}")
            
            query = " ".join(query_parts) if query_parts else ""
            
            # Get message IDs
            result = self.service.users().messages().list(
                userId='me', 
                q=query, 
                maxResults=filter_criteria.max_results
            ).execute()
            
            messages = result.get('messages', [])
            email_messages = []
            
            # Get full message details
            for msg in messages:
                msg_detail = self.service.users().messages().get(
                    userId='me', 
                    id=msg['id'],
                    format='full'
                ).execute()
                
                email_msg = self._parse_gmail_message(msg_detail)
                if email_msg:
                    email_messages.append(email_msg)
            
            return email_messages
            
        except Exception as e:
            logger.error(f"Failed to get Gmail messages: {e}")
            return []
    
    def _parse_gmail_message(self, msg_data: Dict) -> Optional[EmailMessage]:
        """Parse Gmail API message data."""
        try:
            headers = {h['name']: h['value'] for h in msg_data['payload']['headers']}
            
            # Extract body
            body = ""
            html_body = None
            
            def extract_body(payload):
                nonlocal body, html_body
                if 'body' in payload and payload['body'].get('data'):
                    data = payload['body']['data']
                    decoded = base64.urlsafe_b64decode(data).decode('utf-8')
                    if payload.get('mimeType') == 'text/html':
                        html_body = decoded
                    else:
                        body = decoded
                elif 'parts' in payload:
                    for part in payload['parts']:
                        extract_body(part)
            
            extract_body(msg_data['payload'])
            
            # Parse recipients
            recipients = []
            if 'To' in headers:
                recipients.extend([addr.strip() for addr in headers['To'].split(',')])
            if 'Cc' in headers:
                recipients.extend([addr.strip() for addr in headers['Cc'].split(',')])
            
            # Parse labels
            labels = msg_data.get('labelIds', [])
            
            # Parse attachments
            attachments = []
            if 'parts' in msg_data['payload']:
                for part in msg_data['payload']['parts']:
                    if part.get('filename'):
                        attachments.append({
                            'filename': part['filename'],
                            'mimeType': part['mimeType'],
                            'size': part['body'].get('size', 0)
                        })
            
            # Determine if read
            is_read = 'UNREAD' not in labels
            
            # Parse timestamp
            timestamp = datetime.fromtimestamp(int(msg_data['internalDate']) / 1000)
            
            return EmailMessage(
                id=msg_data['id'],
                subject=headers.get('Subject', ''),
                sender=headers.get('From', ''),
                recipients=recipients,
                body=body,
                html_body=html_body,
                timestamp=timestamp,
                is_read=is_read,
                priority=EmailPriority.NORMAL,  # Gmail doesn't expose priority easily
                labels=labels,
                attachments=attachments,
                thread_id=msg_data.get('threadId')
            )
            
        except Exception as e:
            logger.error(f"Failed to parse Gmail message: {e}")
            return None
    
    async def send_message(
        self, 
        to: List[str], 
        subject: str, 
        body: str,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        html_body: Optional[str] = None
    ) -> bool:
        """Send an email message."""
        try:
            
            # Create message
            if html_body:
                message = MIMEMultipart('alternative')
                message.attach(MIMEText(body, 'plain'))
                message.attach(MIMEText(html_body, 'html'))
            else:
                message = MIMEText(body)
            
            message['to'] = ', '.join(to)
            message['subject'] = subject
            
            if cc:
                message['cc'] = ', '.join(cc)
            if bcc:
                message['bcc'] = ', '.join(bcc)
            
            # Send message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send Gmail message: {e}")
            return False


class OutlookManager:
    """Outlook/Exchange integration manager."""
    
    def __init__(self):
        self.account = None
    
    async def authenticate(self, email: str, password: str, server: str = None) -> bool:
        """Authenticate with Outlook/Exchange."""
        try:
            if server:
                # Exchange server
                config = exchangelib.Configuration(
                    server=server,
                    credentials=exchangelib.Credentials(email, password)
                )
            else:
                # Outlook.com
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
            self.account.inbox.count()
            return True
            
        except Exception as e:
            logger.error(f"Outlook authentication failed: {e}")
            return False
    
    async def get_messages(self, filter_criteria: EmailFilter) -> List[EmailMessage]:
        """Get messages from Outlook."""
        try:
            folder = self.account.inbox
            
            # Build filter
            filters = []
            if filter_criteria.sender:
                filters.append(folder.filter(sender__icontains=filter_criteria.sender))
            if filter_criteria.subject_contains:
                filters.append(folder.filter(subject__icontains=filter_criteria.subject_contains))
            if filter_criteria.is_unread is not None:
                filters.append(folder.filter(is_read=not filter_criteria.is_unread))
            if filter_criteria.date_from:
                filters.append(folder.filter(datetime_received__gte=filter_criteria.date_from))
            if filter_criteria.date_to:
                filters.append(folder.filter(datetime_received__lte=filter_criteria.date_to))
            if filter_criteria.has_attachments:
                filters.append(folder.filter(has_attachments=filter_criteria.has_attachments))
            
            # Apply filters
            items = folder
            for f in filters:
                items = items.intersection(f)
            
            # Get messages
            messages = []
            for item in items[:filter_criteria.max_results]:
                email_msg = self._parse_outlook_message(item)
                if email_msg:
                    messages.append(email_msg)
            
            return messages
            
        except Exception as e:
            logger.error(f"Failed to get Outlook messages: {e}")
            return []
    
    def _parse_outlook_message(self, msg) -> Optional[EmailMessage]:
        """Parse Outlook message."""
        try:
            recipients = []
            for recipient in msg.to_recipients or []:
                recipients.append(str(recipient.email_address))
            for recipient in msg.cc_recipients or []:
                recipients.append(str(recipient.email_address))
            
            attachments = []
            for attachment in msg.attachments or []:
                attachments.append({
                    'filename': attachment.name,
                    'size': attachment.size if hasattr(attachment, 'size') else 0
                })
            
            return EmailMessage(
                id=msg.message_id,
                subject=msg.subject or '',
                sender=str(msg.sender.email_address) if msg.sender else '',
                recipients=recipients,
                body=msg.text_body or '',
                html_body=msg.body,
                timestamp=msg.datetime_received,
                is_read=msg.is_read,
                priority=EmailPriority.HIGH if msg.importance == 'High' else EmailPriority.NORMAL,
                labels=[],
                attachments=attachments,
                thread_id=msg.conversation_id.id if msg.conversation_id else None
            )
            
        except Exception as e:
            logger.error(f"Failed to parse Outlook message: {e}")
            return None
    
    async def send_message(
        self,
        to: List[str],
        subject: str,
        body: str,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        html_body: Optional[str] = None
    ) -> bool:
        """Send Outlook message."""
        try:
            message = exchangelib.Message(
                account=self.account,
                subject=subject,
                body=html_body or body,
                to_recipients=[exchangelib.Mailbox(email_address=addr) for addr in to]
            )
            
            if cc:
                message.cc_recipients = [exchangelib.Mailbox(email_address=addr) for addr in cc]
            if bcc:
                message.bcc_recipients = [exchangelib.Mailbox(email_address=addr) for addr in bcc]
            
            message.send()
            return True
            
        except Exception as e:
            logger.error(f"Failed to send Outlook message: {e}")
            return False


class EmailAI:
    """AI-powered email analysis and automation."""
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
    
    async def categorize_emails(self, emails: List[EmailMessage]) -> Dict[str, List[EmailMessage]]:
        """Categorize emails using AI."""
        categories = {
            'urgent': [],
            'work': [],
            'personal': [],
            'promotions': [],
            'newsletters': [],
            'spam': [],
            'other': []
        }
        
        for email in emails:
            try:
                prompt = f"""
                Categorize this email into one of: urgent, work, personal, promotions, newsletters, spam, other
                
                Subject: {email.subject}
                From: {email.sender}
                Body: {email.body[:500]}...
                
                Response format: category_name
                """
                
                response = await self.llm_client.chat([{"role": "user", "content": prompt}])
                category = response.strip().lower()
                
                if category in categories:
                    categories[category].append(email)
                else:
                    categories['other'].append(email)
                    
            except Exception as e:
                logger.error(f"Failed to categorize email {email.id}: {e}")
                categories['other'].append(email)
        
        return categories
    
    async def generate_reply(self, original_email: EmailMessage, context: str = "") -> str:
        """Generate AI reply to email."""
        try:
            prompt = f"""
            Generate a professional email reply to the following email:
            
            Original Subject: {original_email.subject}
            From: {original_email.sender}
            Body: {original_email.body}
            
            Additional context: {context}
            
            Generate a helpful, professional, and contextually appropriate reply.
            Only return the reply body, no subject line.
            """
            
            response = await self.llm_client.chat([{"role": "user", "content": prompt}])
            return response.strip()
            
        except Exception as e:
            logger.error(f"Failed to generate reply: {e}")
            return "I apologize, but I'm unable to generate a response at this time."
    
    async def summarize_emails(self, emails: List[EmailMessage]) -> str:
        """Create AI summary of multiple emails."""
        try:
            email_summaries = []
            for email in emails[:10]:  # Limit to avoid token limits
                summary = f"From: {email.sender}\nSubject: {email.subject}\nSnippet: {email.body[:200]}..."
                email_summaries.append(summary)
            
            prompt = f"""
            Create a concise summary of these emails:
            
            {chr(10).join(email_summaries)}
            
            Provide:
            1. Overall summary
            2. Urgent items requiring attention
            3. Key action items
            4. Important senders
            """
            
            response = await self.llm_client.chat([{"role": "user", "content": prompt}])
            return response.strip()
            
        except Exception as e:
            logger.error(f"Failed to summarize emails: {e}")
            return "Unable to generate email summary."
    
    async def extract_action_items(self, emails: List[EmailMessage]) -> List[Dict[str, Any]]:
        """Extract action items from emails."""
        action_items = []
        
        for email in emails:
            try:
                prompt = f"""
                Extract action items from this email. Return JSON array of actions.
                
                Subject: {email.subject}
                From: {email.sender}
                Body: {email.body}
                
                Format: [{"task": "description", "deadline": "date if mentioned", "priority": "high/medium/low"}]
                """
                
                response = await self.llm_client.chat([{"role": "user", "content": prompt}])
                
                # Parse JSON response
                try:
                    items = json.loads(response.strip())
                    for item in items:
                        item['email_id'] = email.id
                        item['email_subject'] = email.subject
                        action_items.append(item)
                except json.JSONDecodeError:
                    pass
                    
            except Exception as e:
                logger.error(f"Failed to extract action items from {email.id}: {e}")
        
        return action_items


class EmailIntegrationTool(BaseTool):
    """Comprehensive email integration tool."""
    
    name = "email_integration"
    description = "Advanced email management with Gmail/Outlook integration and AI features"
    
    def __init__(self):
        super().__init__()
        self.gmail_manager = GmailManager()
        self.outlook_manager = OutlookManager()
        self.email_ai = None
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
                    "setup_gmail", "setup_outlook", "list_emails", "send_email",
                    "categorize_emails", "summarize_emails", "generate_reply",
                    "search_emails", "mark_read", "extract_actions", "get_unread_count"
                ]
            ),
            "provider": ToolParameter(
                name="provider",
                type="string",
                description="Email provider (gmail/outlook)",
                required=False,
                enum=["gmail", "outlook"],
                default="gmail"
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
                description="Email filter criteria",
                required=False
            ),
            "email_data": ToolParameter(
                name="email_data",
                type="object",
                description="Email data for sending",
                required=False
            ),
            "email_id": ToolParameter(
                name="email_id",
                type="string",
                description="Email ID for specific operations",
                required=False
            ),
            "query": ToolParameter(
                name="query",
                type="string",
                description="Search query",
                required=False
            )
        }
    
    async def execute(
        self,
        action: str,
        provider: str = "gmail",
        credentials: Optional[Dict] = None,
        filter: Optional[Dict] = None,
        email_data: Optional[Dict] = None,
        email_id: Optional[str] = None,
        query: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute email integration action."""
        if not EMAIL_DEPS_AVAILABLE:
            return {
                "success": False,
                "error": "Email dependencies not installed. Run: pip install google-auth google-auth-oauthlib google-api-python-client exchangelib"
            }
        
        try:
            if action == "setup_gmail":
                return await self._setup_gmail(credentials)
            elif action == "setup_outlook":
                return await self._setup_outlook(credentials)
            elif action == "list_emails":
                return await self._list_emails(provider, filter)
            elif action == "send_email":
                return await self._send_email(provider, email_data)
            elif action == "categorize_emails":
                return await self._categorize_emails(provider, filter)
            elif action == "summarize_emails":
                return await self._summarize_emails(provider, filter)
            elif action == "generate_reply":
                return await self._generate_reply(provider, email_id, email_data)
            elif action == "search_emails":
                return await self._search_emails(provider, query)
            elif action == "mark_read":
                return await self._mark_read(provider, email_id)
            elif action == "extract_actions":
                return await self._extract_actions(provider, filter)
            elif action == "get_unread_count":
                return await self._get_unread_count(provider)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
                
        except Exception as e:
            logger.error(f"Email integration error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _setup_gmail(self, credentials: Dict) -> Dict[str, Any]:
        """Set up Gmail authentication."""
        try:
            credentials_path = credentials.get('credentials_file', 'credentials.json')
            token_path = credentials.get('token_file', 'gmail_token.json')
            
            success = await self.gmail_manager.authenticate(credentials_path, token_path)
            
            if success:
                self.active_provider = EmailProvider.GMAIL
                return {
                    "success": True,
                    "message": "Gmail authentication successful",
                    "provider": "gmail"
                }
            else:
                return {
                    "success": False,
                    "error": "Gmail authentication failed"
                }
                
        except Exception as e:
            return {"success": False, "error": f"Gmail setup error: {str(e)}"}
    
    async def _setup_outlook(self, credentials: Dict) -> Dict[str, Any]:
        """Set up Outlook authentication."""
        try:
            email = credentials.get('email')
            password = credentials.get('password')
            server = credentials.get('server')
            
            if not email or not password:
                return {"success": False, "error": "Email and password required for Outlook"}
            
            success = await self.outlook_manager.authenticate(email, password, server)
            
            if success:
                self.active_provider = EmailProvider.OUTLOOK
                return {
                    "success": True,
                    "message": "Outlook authentication successful",
                    "provider": "outlook"
                }
            else:
                return {
                    "success": False,
                    "error": "Outlook authentication failed"
                }
                
        except Exception as e:
            return {"success": False, "error": f"Outlook setup error: {str(e)}"}
    
    async def _list_emails(self, provider: str, filter_dict: Optional[Dict]) -> Dict[str, Any]:
        """List emails with filtering."""
        try:
            # Parse filter
            email_filter = self._parse_filter(filter_dict)
            
            # Get manager
            if provider == "gmail":
                manager = self.gmail_manager
            else:
                manager = self.outlook_manager
            
            # Get messages
            messages = await manager.get_messages(email_filter)
            
            return {
                "success": True,
                "messages": [msg.to_dict() for msg in messages],
                "count": len(messages),
                "provider": provider
            }
            
        except Exception as e:
            return {"success": False, "error": f"Failed to list emails: {str(e)}"}
    
    async def _send_email(self, provider: str, email_data: Dict) -> Dict[str, Any]:
        """Send email."""
        try:
            to = email_data.get('to', [])
            if isinstance(to, str):
                to = [to]
            
            subject = email_data.get('subject', '')
            body = email_data.get('body', '')
            cc = email_data.get('cc', [])
            bcc = email_data.get('bcc', [])
            html_body = email_data.get('html_body')
            
            # Get manager
            if provider == "gmail":
                manager = self.gmail_manager
            else:
                manager = self.outlook_manager
            
            # Send message
            success = await manager.send_message(to, subject, body, cc, bcc, html_body)
            
            if success:
                return {
                    "success": True,
                    "message": f"Email sent successfully to {', '.join(to)}",
                    "provider": provider
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to send email"
                }
                
        except Exception as e:
            return {"success": False, "error": f"Failed to send email: {str(e)}"}
    
    def _parse_filter(self, filter_dict: Optional[Dict]) -> EmailFilter:
        """Parse filter dictionary into EmailFilter object."""
        if not filter_dict:
            return EmailFilter()
        
        # Parse dates
        date_from = None
        date_to = None
        
        if filter_dict.get('date_from'):
            try:
                date_from = datetime.fromisoformat(filter_dict['date_from'])
            except ValueError:
                pass
        
        if filter_dict.get('date_to'):
            try:
                date_to = datetime.fromisoformat(filter_dict['date_to'])
            except ValueError:
                pass
        
        # Parse priority
        priority = None
        if filter_dict.get('priority'):
            try:
                priority = EmailPriority(filter_dict['priority'])
            except ValueError:
                pass
        
        return EmailFilter(
            sender=filter_dict.get('sender'),
            subject_contains=filter_dict.get('subject_contains'),
            body_contains=filter_dict.get('body_contains'),
            has_attachments=filter_dict.get('has_attachments'),
            is_unread=filter_dict.get('is_unread'),
            date_from=date_from,
            date_to=date_to,
            labels=filter_dict.get('labels', []),
            priority=priority,
            max_results=filter_dict.get('max_results', 50)
        )
    
    # Additional methods for AI features would be implemented here...
    async def _categorize_emails(self, provider: str, filter_dict: Optional[Dict]) -> Dict[str, Any]:
        """Categorize emails using AI (placeholder - needs LLM integration)."""
        return {
            "success": False,
            "error": "AI categorization not yet implemented - requires LLM integration"
        }
    
    async def _summarize_emails(self, provider: str, filter_dict: Optional[Dict]) -> Dict[str, Any]:
        """Summarize emails using AI (placeholder)."""
        return {
            "success": False,
            "error": "AI summarization not yet implemented - requires LLM integration"
        }
    
    async def _generate_reply(self, provider: str, email_id: str, context: Dict) -> Dict[str, Any]:
        """Generate AI reply (placeholder)."""
        return {
            "success": False,
            "error": "AI reply generation not yet implemented - requires LLM integration"
        }
    
    async def _search_emails(self, provider: str, query: str) -> Dict[str, Any]:
        """Search emails."""
        try:
            # Create filter from query
            email_filter = EmailFilter(
                subject_contains=query,
                body_contains=query,
                max_results=50
            )
            
            # Get manager
            if provider == "gmail":
                manager = self.gmail_manager
            else:
                manager = self.outlook_manager
            
            # Search messages
            messages = await manager.get_messages(email_filter)
            
            return {
                "success": True,
                "messages": [msg.to_dict() for msg in messages],
                "count": len(messages),
                "query": query,
                "provider": provider
            }
            
        except Exception as e:
            return {"success": False, "error": f"Search failed: {str(e)}"}
    
    async def _mark_read(self, provider: str, email_id: str) -> Dict[str, Any]:
        """Mark email as read (placeholder)."""
        return {
            "success": False,
            "error": "Mark as read not yet implemented"
        }
    
    async def _extract_actions(self, provider: str, filter_dict: Optional[Dict]) -> Dict[str, Any]:
        """Extract action items from emails (placeholder)."""
        return {
            "success": False,
            "error": "Action item extraction not yet implemented - requires LLM integration"
        }
    
    async def _get_unread_count(self, provider: str) -> Dict[str, Any]:
        """Get unread email count."""
        try:
            email_filter = EmailFilter(is_unread=True, max_results=1000)
            
            if provider == "gmail":
                manager = self.gmail_manager
            else:
                manager = self.outlook_manager
            
            messages = await manager.get_messages(email_filter)
            
            return {
                "success": True,
                "unread_count": len(messages),
                "provider": provider
            }
            
        except Exception as e:
            return {"success": False, "error": f"Failed to get unread count: {str(e)}"}


# Export the tool
__all__ = ['EmailIntegrationTool']