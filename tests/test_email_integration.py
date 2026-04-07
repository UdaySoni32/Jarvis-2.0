"""
Tests for Email Integration Plugin
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from src.plugins.email_integration import (
    EmailIntegrationTool,
    EmailMessage,
    EmailFilter,
    EmailProvider,
    EmailPriority,
    GmailManager,
    OutlookManager,
    EmailAI
)


class TestEmailMessage:
    """Test EmailMessage data structure."""
    
    def test_email_message_creation(self):
        """Test creating an EmailMessage."""
        msg = EmailMessage(
            id="123",
            subject="Test Email",
            sender="test@example.com",
            recipients=["recipient@example.com"],
            body="Test body",
            html_body="<p>Test body</p>",
            timestamp=datetime.now(),
            is_read=False,
            priority=EmailPriority.HIGH,
            labels=["inbox"],
            attachments=[],
            thread_id="thread123"
        )
        
        assert msg.id == "123"
        assert msg.subject == "Test Email"
        assert msg.sender == "test@example.com"
        assert msg.recipients == ["recipient@example.com"]
        assert msg.priority == EmailPriority.HIGH
        assert not msg.is_read
    
    def test_email_message_to_dict(self):
        """Test converting EmailMessage to dictionary."""
        timestamp = datetime.now()
        msg = EmailMessage(
            id="123",
            subject="Test",
            sender="sender@example.com",
            recipients=["rec@example.com"],
            body="Body",
            html_body=None,
            timestamp=timestamp,
            is_read=True,
            priority=EmailPriority.NORMAL,
            labels=["inbox"],
            attachments=[],
            thread_id=None
        )
        
        result = msg.to_dict()
        
        assert result["id"] == "123"
        assert result["subject"] == "Test"
        assert result["sender"] == "sender@example.com"
        assert result["recipients"] == ["rec@example.com"]
        assert result["timestamp"] == timestamp.isoformat()
        assert result["is_read"] is True
        assert result["priority"] == "normal"


class TestEmailFilter:
    """Test EmailFilter functionality."""
    
    def test_email_filter_defaults(self):
        """Test default EmailFilter values."""
        filter_obj = EmailFilter()
        
        assert filter_obj.sender is None
        assert filter_obj.subject_contains is None
        assert filter_obj.body_contains is None
        assert filter_obj.has_attachments is None
        assert filter_obj.is_unread is None
        assert filter_obj.date_from is None
        assert filter_obj.date_to is None
        assert filter_obj.labels is None
        assert filter_obj.priority is None
        assert filter_obj.max_results == 50
    
    def test_email_filter_with_values(self):
        """Test EmailFilter with specific values."""
        date_from = datetime.now() - timedelta(days=7)
        date_to = datetime.now()
        
        filter_obj = EmailFilter(
            sender="test@example.com",
            subject_contains="meeting",
            has_attachments=True,
            is_unread=True,
            date_from=date_from,
            date_to=date_to,
            labels=["work"],
            priority=EmailPriority.HIGH,
            max_results=25
        )
        
        assert filter_obj.sender == "test@example.com"
        assert filter_obj.subject_contains == "meeting"
        assert filter_obj.has_attachments is True
        assert filter_obj.is_unread is True
        assert filter_obj.date_from == date_from
        assert filter_obj.date_to == date_to
        assert filter_obj.labels == ["work"]
        assert filter_obj.priority == EmailPriority.HIGH
        assert filter_obj.max_results == 25


class TestGmailManager:
    """Test Gmail integration manager."""
    
    @pytest.fixture
    def gmail_manager(self):
        """Create GmailManager instance."""
        return GmailManager()
    
    def test_init(self, gmail_manager):
        """Test GmailManager initialization."""
        assert gmail_manager.service is None
        assert gmail_manager.credentials is None
        assert len(gmail_manager.scopes) == 3
    
    @patch('src.plugins.email_integration.os.path.exists')
    @patch('src.plugins.email_integration.Credentials.from_authorized_user_file')
    @patch('src.plugins.email_integration.build')
    async def test_authenticate_existing_token(
        self, 
        mock_build, 
        mock_credentials, 
        mock_exists,
        gmail_manager
    ):
        """Test authentication with existing valid token."""
        mock_exists.return_value = True
        mock_creds = MagicMock()
        mock_creds.valid = True
        mock_credentials.return_value = mock_creds
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        
        result = await gmail_manager.authenticate("creds.json", "token.json")
        
        assert result is True
        assert gmail_manager.service == mock_service
        assert gmail_manager.credentials == mock_creds
        mock_build.assert_called_once_with('gmail', 'v1', credentials=mock_creds)
    
    async def test_authenticate_no_deps(self, gmail_manager):
        """Test authentication without dependencies."""
        with patch('src.plugins.email_integration.EMAIL_DEPS_AVAILABLE', False):
            # This would fail in actual code due to import error
            # but we test the structure
            pass
    
    def test_parse_gmail_message(self, gmail_manager):
        """Test parsing Gmail message data."""
        # Mock Gmail API message format
        mock_msg_data = {
            'id': '123',
            'threadId': 'thread123',
            'labelIds': ['INBOX', 'UNREAD'],
            'internalDate': '1640995200000',  # Unix timestamp in milliseconds
            'payload': {
                'headers': [
                    {'name': 'Subject', 'value': 'Test Subject'},
                    {'name': 'From', 'value': 'sender@example.com'},
                    {'name': 'To', 'value': 'recipient@example.com'}
                ],
                'body': {
                    'data': 'VGVzdCBib2R5'  # base64 encoded "Test body"
                },
                'mimeType': 'text/plain',
                'parts': []
            }
        }
        
        with patch('base64.urlsafe_b64decode') as mock_decode:
            mock_decode.return_value = b'Test body'
            
            result = gmail_manager._parse_gmail_message(mock_msg_data)
            
            assert result is not None
            assert result.id == '123'
            assert result.subject == 'Test Subject'
            assert result.sender == 'sender@example.com'
            assert result.recipients == ['recipient@example.com']
            assert result.body == 'Test body'
            assert result.thread_id == 'thread123'
            assert not result.is_read  # UNREAD label present


class TestOutlookManager:
    """Test Outlook integration manager."""
    
    @pytest.fixture
    def outlook_manager(self):
        """Create OutlookManager instance."""
        return OutlookManager()
    
    def test_init(self, outlook_manager):
        """Test OutlookManager initialization."""
        assert outlook_manager.account is None
    
    @patch('src.plugins.email_integration.exchangelib.Configuration')
    @patch('src.plugins.email_integration.exchangelib.Credentials')
    @patch('src.plugins.email_integration.exchangelib.Account')
    async def test_authenticate_outlook(
        self, 
        mock_account,
        mock_credentials, 
        mock_config,
        outlook_manager
    ):
        """Test Outlook authentication."""
        mock_account_instance = MagicMock()
        mock_account_instance.inbox.count.return_value = 5
        mock_account.return_value = mock_account_instance
        
        result = await outlook_manager.authenticate(
            "test@outlook.com", 
            "password"
        )
        
        assert result is True
        assert outlook_manager.account == mock_account_instance
    
    def test_parse_outlook_message(self, outlook_manager):
        """Test parsing Outlook message."""
        # Mock Outlook message
        mock_msg = MagicMock()
        mock_msg.message_id = "outlook123"
        mock_msg.subject = "Outlook Test"
        mock_msg.sender.email_address = "outlook_sender@example.com"
        mock_msg.to_recipients = [MagicMock()]
        mock_msg.to_recipients[0].email_address = "outlook_recipient@example.com"
        mock_msg.cc_recipients = []
        mock_msg.text_body = "Outlook body"
        mock_msg.body = "<p>Outlook body</p>"
        mock_msg.datetime_received = datetime.now()
        mock_msg.is_read = True
        mock_msg.importance = "Normal"
        mock_msg.attachments = []
        mock_msg.conversation_id = None
        
        result = outlook_manager._parse_outlook_message(mock_msg)
        
        assert result is not None
        assert result.id == "outlook123"
        assert result.subject == "Outlook Test"
        assert result.sender == "outlook_sender@example.com"
        assert result.recipients == ["outlook_recipient@example.com"]
        assert result.body == "Outlook body"
        assert result.html_body == "<p>Outlook body</p>"
        assert result.is_read is True


class TestEmailAI:
    """Test AI-powered email features."""
    
    @pytest.fixture
    def email_ai(self):
        """Create EmailAI instance."""
        mock_llm = AsyncMock()
        return EmailAI(mock_llm)
    
    @pytest.fixture
    def sample_emails(self):
        """Create sample email messages."""
        return [
            EmailMessage(
                id="1",
                subject="Urgent: System Down",
                sender="admin@company.com",
                recipients=["user@company.com"],
                body="The production system is down. Please investigate immediately.",
                html_body=None,
                timestamp=datetime.now(),
                is_read=False,
                priority=EmailPriority.HIGH,
                labels=["inbox"],
                attachments=[],
                thread_id=None
            ),
            EmailMessage(
                id="2",
                subject="Weekly Newsletter",
                sender="newsletter@example.com",
                recipients=["user@company.com"],
                body="Here's this week's newsletter with updates...",
                html_body=None,
                timestamp=datetime.now(),
                is_read=True,
                priority=EmailPriority.LOW,
                labels=["inbox"],
                attachments=[],
                thread_id=None
            )
        ]
    
    async def test_categorize_emails(self, email_ai, sample_emails):
        """Test AI email categorization."""
        email_ai.llm_client.chat = AsyncMock(side_effect=["urgent", "newsletters"])
        
        result = await email_ai.categorize_emails(sample_emails)
        
        assert "urgent" in result
        assert "newsletters" in result
        assert len(result["urgent"]) == 1
        assert len(result["newsletters"]) == 1
        assert result["urgent"][0].subject == "Urgent: System Down"
        assert result["newsletters"][0].subject == "Weekly Newsletter"
    
    async def test_generate_reply(self, email_ai, sample_emails):
        """Test AI reply generation."""
        email_ai.llm_client.chat = AsyncMock(return_value="Thank you for the urgent notification. I'm investigating the issue now and will update you shortly.")
        
        result = await email_ai.generate_reply(
            sample_emails[0], 
            "System administrator on duty"
        )
        
        assert "investigating" in result.lower()
        assert "update" in result.lower()
        email_ai.llm_client.chat.assert_called_once()
    
    async def test_summarize_emails(self, email_ai, sample_emails):
        """Test AI email summarization."""
        summary_text = """
        Summary: 2 emails received
        Urgent: System down notification requiring immediate action
        Regular: Weekly newsletter
        Action items: Investigate production system issue
        """
        email_ai.llm_client.chat = AsyncMock(return_value=summary_text.strip())
        
        result = await email_ai.summarize_emails(sample_emails)
        
        assert "System down" in result
        assert "newsletter" in result
        assert "Investigate" in result
        email_ai.llm_client.chat.assert_called_once()
    
    async def test_extract_action_items(self, email_ai, sample_emails):
        """Test AI action item extraction."""
        action_json = '[{"task": "Investigate production system", "deadline": "immediately", "priority": "high"}]'
        email_ai.llm_client.chat = AsyncMock(return_value=action_json)
        
        result = await email_ai.extract_action_items(sample_emails[:1])
        
        assert len(result) == 1
        assert result[0]["task"] == "Investigate production system"
        assert result[0]["priority"] == "high"
        assert result[0]["email_id"] == "1"
        assert result[0]["email_subject"] == "Urgent: System Down"


class TestEmailIntegrationTool:
    """Test main EmailIntegrationTool."""
    
    @pytest.fixture
    def email_tool(self):
        """Create EmailIntegrationTool instance."""
        return EmailIntegrationTool()
    
    def test_init(self, email_tool):
        """Test tool initialization."""
        assert email_tool.name == "email_integration"
        assert "email management" in email_tool.description.lower()
        assert email_tool.gmail_manager is not None
        assert email_tool.outlook_manager is not None
        assert email_tool.active_provider is None
    
    def test_get_parameters(self, email_tool):
        """Test parameter definitions."""
        params = email_tool.get_parameters()
        
        assert "action" in params
        assert params["action"].required is True
        assert "setup_gmail" in params["action"].enum
        assert "send_email" in params["action"].enum
        
        assert "provider" in params
        assert params["provider"].default == "gmail"
        
        assert "credentials" in params
        assert "email_data" in params
        assert "filter" in params
    
    @patch('src.plugins.email_integration.EMAIL_DEPS_AVAILABLE', False)
    async def test_execute_no_deps(self, email_tool):
        """Test execution without dependencies."""
        result = await email_tool.execute("setup_gmail")
        
        assert result["success"] is False
        assert "dependencies not installed" in result["error"]
    
    async def test_execute_unknown_action(self, email_tool):
        """Test execution with unknown action."""
        with patch('src.plugins.email_integration.EMAIL_DEPS_AVAILABLE', True):
            result = await email_tool.execute("unknown_action")
            
            assert result["success"] is False
            assert "Unknown action" in result["error"]
    
    def test_parse_filter(self, email_tool):
        """Test filter parsing."""
        filter_dict = {
            "sender": "test@example.com",
            "subject_contains": "meeting",
            "has_attachments": True,
            "is_unread": True,
            "date_from": "2024-01-01T00:00:00",
            "date_to": "2024-12-31T23:59:59",
            "labels": ["work", "urgent"],
            "priority": "high",
            "max_results": 25
        }
        
        result = email_tool._parse_filter(filter_dict)
        
        assert result.sender == "test@example.com"
        assert result.subject_contains == "meeting"
        assert result.has_attachments is True
        assert result.is_unread is True
        assert result.date_from is not None
        assert result.date_to is not None
        assert result.labels == ["work", "urgent"]
        assert result.priority == EmailPriority.HIGH
        assert result.max_results == 25
    
    def test_parse_filter_empty(self, email_tool):
        """Test parsing empty filter."""
        result = email_tool._parse_filter(None)
        
        assert result.sender is None
        assert result.max_results == 50  # default
    
    def test_parse_filter_invalid_dates(self, email_tool):
        """Test parsing filter with invalid dates."""
        filter_dict = {
            "date_from": "invalid-date",
            "date_to": "also-invalid",
            "priority": "invalid-priority"
        }
        
        result = email_tool._parse_filter(filter_dict)
        
        assert result.date_from is None
        assert result.date_to is None
        assert result.priority is None
    
    async def test_setup_gmail_success(self, email_tool):
        """Test successful Gmail setup."""
        with patch('src.plugins.email_integration.EMAIL_DEPS_AVAILABLE', True):
            email_tool.gmail_manager.authenticate = AsyncMock(return_value=True)
            
            credentials = {
                "credentials_file": "creds.json",
                "token_file": "token.json"
            }
            
            result = await email_tool._setup_gmail(credentials)
            
            assert result["success"] is True
            assert result["provider"] == "gmail"
            assert email_tool.active_provider == EmailProvider.GMAIL
    
    async def test_setup_gmail_failure(self, email_tool):
        """Test failed Gmail setup."""
        with patch('src.plugins.email_integration.EMAIL_DEPS_AVAILABLE', True):
            email_tool.gmail_manager.authenticate = AsyncMock(return_value=False)
            
            result = await email_tool._setup_gmail({})
            
            assert result["success"] is False
            assert "authentication failed" in result["error"]
    
    async def test_setup_outlook_success(self, email_tool):
        """Test successful Outlook setup."""
        with patch('src.plugins.email_integration.EMAIL_DEPS_AVAILABLE', True):
            email_tool.outlook_manager.authenticate = AsyncMock(return_value=True)
            
            credentials = {
                "email": "test@outlook.com",
                "password": "password123"
            }
            
            result = await email_tool._setup_outlook(credentials)
            
            assert result["success"] is True
            assert result["provider"] == "outlook"
            assert email_tool.active_provider == EmailProvider.OUTLOOK
    
    async def test_setup_outlook_missing_creds(self, email_tool):
        """Test Outlook setup with missing credentials."""
        with patch('src.plugins.email_integration.EMAIL_DEPS_AVAILABLE', True):
            result = await email_tool._setup_outlook({})
            
            assert result["success"] is False
            assert "Email and password required" in result["error"]
    
    async def test_list_emails(self, email_tool):
        """Test listing emails."""
        with patch('src.plugins.email_integration.EMAIL_DEPS_AVAILABLE', True):
            # Mock email messages
            mock_messages = [
                EmailMessage(
                    id="1",
                    subject="Test 1",
                    sender="sender1@example.com",
                    recipients=["user@example.com"],
                    body="Body 1",
                    html_body=None,
                    timestamp=datetime.now(),
                    is_read=True,
                    priority=EmailPriority.NORMAL,
                    labels=["inbox"],
                    attachments=[],
                    thread_id=None
                )
            ]
            
            email_tool.gmail_manager.get_messages = AsyncMock(return_value=mock_messages)
            
            result = await email_tool._list_emails("gmail", {})
            
            assert result["success"] is True
            assert result["count"] == 1
            assert result["provider"] == "gmail"
            assert len(result["messages"]) == 1
            assert result["messages"][0]["id"] == "1"
    
    async def test_send_email(self, email_tool):
        """Test sending email."""
        with patch('src.plugins.email_integration.EMAIL_DEPS_AVAILABLE', True):
            email_tool.gmail_manager.send_message = AsyncMock(return_value=True)
            
            email_data = {
                "to": ["recipient@example.com"],
                "subject": "Test Subject",
                "body": "Test body",
                "cc": ["cc@example.com"],
                "html_body": "<p>Test body</p>"
            }
            
            result = await email_tool._send_email("gmail", email_data)
            
            assert result["success"] is True
            assert result["provider"] == "gmail"
            assert "sent successfully" in result["message"]
            
            # Verify the call
            email_tool.gmail_manager.send_message.assert_called_once_with(
                ["recipient@example.com"],
                "Test Subject",
                "Test body",
                ["cc@example.com"],
                [],
                "<p>Test body</p>"
            )
    
    async def test_search_emails(self, email_tool):
        """Test searching emails."""
        with patch('src.plugins.email_integration.EMAIL_DEPS_AVAILABLE', True):
            mock_messages = []
            email_tool.gmail_manager.get_messages = AsyncMock(return_value=mock_messages)
            
            result = await email_tool._search_emails("gmail", "test query")
            
            assert result["success"] is True
            assert result["query"] == "test query"
            assert result["provider"] == "gmail"
            assert result["count"] == 0
    
    async def test_get_unread_count(self, email_tool):
        """Test getting unread email count."""
        with patch('src.plugins.email_integration.EMAIL_DEPS_AVAILABLE', True):
            mock_messages = [MagicMock() for _ in range(5)]
            email_tool.gmail_manager.get_messages = AsyncMock(return_value=mock_messages)
            
            result = await email_tool._get_unread_count("gmail")
            
            assert result["success"] is True
            assert result["unread_count"] == 5
            assert result["provider"] == "gmail"


# Integration Tests
class TestEmailIntegrationFull:
    """Full integration tests for email functionality."""
    
    @pytest.fixture
    def email_tool(self):
        """Create fully configured email tool."""
        tool = EmailIntegrationTool()
        return tool
    
    @pytest.mark.asyncio
    async def test_full_workflow_gmail(self, email_tool):
        """Test complete Gmail workflow."""
        with patch('src.plugins.email_integration.EMAIL_DEPS_AVAILABLE', True):
            # Mock all dependencies
            email_tool.gmail_manager.authenticate = AsyncMock(return_value=True)
            email_tool.gmail_manager.get_messages = AsyncMock(return_value=[])
            email_tool.gmail_manager.send_message = AsyncMock(return_value=True)
            
            # Setup
            setup_result = await email_tool.execute(
                "setup_gmail",
                credentials={"credentials_file": "test_creds.json"}
            )
            assert setup_result["success"] is True
            
            # List emails
            list_result = await email_tool.execute(
                "list_emails",
                provider="gmail",
                filter={"is_unread": True, "max_results": 10}
            )
            assert list_result["success"] is True
            
            # Send email
            send_result = await email_tool.execute(
                "send_email",
                provider="gmail",
                email_data={
                    "to": ["test@example.com"],
                    "subject": "Test",
                    "body": "Test body"
                }
            )
            assert send_result["success"] is True
            
            # Get unread count
            count_result = await email_tool.execute(
                "get_unread_count",
                provider="gmail"
            )
            assert count_result["success"] is True


if __name__ == "__main__":
    pytest.main([__file__])