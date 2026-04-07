# JARVIS 2.0 - Email Integration Plugin Documentation

## Overview

The Email Integration Plugin provides comprehensive email management capabilities with support for Gmail and Outlook/Exchange. It includes AI-powered features for email categorization, reply generation, and intelligent automation.

## Features

### Core Email Operations
- **Multi-Provider Support**: Gmail via Google API, Outlook/Exchange via EWS
- **Email Reading**: Fetch emails with advanced filtering and search
- **Email Sending**: Compose and send emails with attachments support
- **Email Organization**: Labels, categories, and folder management
- **Real-time Operations**: Async operations for responsive performance

### Advanced Filtering
- Sender/recipient filtering
- Subject and body content search
- Date range filtering
- Attachment presence filtering
- Read/unread status filtering
- Label/category filtering
- Priority-based filtering

### AI-Powered Features (Future)
- **Smart Categorization**: Automatically categorize emails by content
- **Reply Generation**: AI-generated contextual replies
- **Email Summarization**: Intelligent email thread summaries
- **Action Item Extraction**: Detect tasks and deadlines from emails
- **Priority Detection**: Identify urgent emails automatically

## Installation

### Dependencies

```bash
# Install required packages
pip install google-auth google-auth-oauthlib google-api-python-client exchangelib
```

### Gmail Setup

1. **Create Google Cloud Project**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing
   - Enable Gmail API

2. **Create OAuth 2.0 Credentials**:
   - Go to APIs & Services → Credentials
   - Create OAuth 2.0 client ID (Desktop application)
   - Download credentials JSON file

3. **Configure JARVIS**:
   ```python
   # Setup Gmail
   result = await email_tool.execute(
       action="setup_gmail",
       credentials={
           "credentials_file": "path/to/credentials.json",
           "token_file": "path/to/gmail_token.json"
       }
   )
   ```

### Outlook Setup

1. **Exchange Server Setup**:
   ```python
   # Setup Outlook/Exchange
   result = await email_tool.execute(
       action="setup_outlook", 
       credentials={
           "email": "your-email@company.com",
           "password": "your-password",
           "server": "exchange.company.com"  # Optional for Outlook.com
       }
   )
   ```

2. **Outlook.com Setup**:
   ```python
   # Setup Outlook.com (uses Office 365)
   result = await email_tool.execute(
       action="setup_outlook",
       credentials={
           "email": "your-email@outlook.com", 
           "password": "your-password"
       }
   )
   ```

## Usage Examples

### Basic Operations

```python
from src.plugins.email_integration import EmailIntegrationTool

# Create tool instance
email_tool = EmailIntegrationTool()

# Setup Gmail (one-time)
await email_tool.execute(
    action="setup_gmail",
    credentials={"credentials_file": "credentials.json"}
)

# List recent emails
result = await email_tool.execute(
    action="list_emails",
    provider="gmail",
    filter={
        "max_results": 10,
        "is_unread": True
    }
)

# Send email
await email_tool.execute(
    action="send_email",
    provider="gmail", 
    email_data={
        "to": ["recipient@example.com"],
        "subject": "Hello from JARVIS",
        "body": "This is a test email from JARVIS 2.0",
        "cc": ["manager@example.com"]
    }
)
```

### Advanced Filtering

```python
# Complex filter example
filter_criteria = {
    "sender": "important@company.com",
    "subject_contains": "urgent",
    "has_attachments": True,
    "date_from": "2024-01-01T00:00:00",
    "date_to": "2024-12-31T23:59:59",
    "labels": ["work", "priority"],
    "max_results": 25
}

result = await email_tool.execute(
    action="list_emails",
    provider="gmail",
    filter=filter_criteria
)
```

### Search Operations

```python
# Search emails
search_result = await email_tool.execute(
    action="search_emails",
    provider="gmail",
    query="project deadline"
)

# Get unread count
count_result = await email_tool.execute(
    action="get_unread_count",
    provider="gmail"
)
```

## Data Structures

### EmailMessage

```python
@dataclass
class EmailMessage:
    id: str                      # Unique message ID
    subject: str                 # Email subject
    sender: str                  # Sender email address
    recipients: List[str]        # List of recipients
    body: str                    # Plain text body
    html_body: Optional[str]     # HTML body (if available)
    timestamp: datetime          # Email timestamp
    is_read: bool               # Read status
    priority: EmailPriority     # Priority level
    labels: List[str]           # Labels/categories
    attachments: List[Dict]     # Attachment metadata
    thread_id: Optional[str]    # Thread/conversation ID
```

### EmailFilter

```python
@dataclass 
class EmailFilter:
    sender: Optional[str] = None                    # Filter by sender
    subject_contains: Optional[str] = None          # Subject search term
    body_contains: Optional[str] = None             # Body search term
    has_attachments: Optional[bool] = None          # Has attachments
    is_unread: Optional[bool] = None                # Unread status
    date_from: Optional[datetime] = None            # Start date
    date_to: Optional[datetime] = None              # End date
    labels: Optional[List[str]] = None              # Label filter
    priority: Optional[EmailPriority] = None        # Priority filter
    max_results: int = 50                           # Maximum results
```

## CLI Integration

### Available Commands

```bash
# Setup email providers
JARVIS> email setup gmail --credentials-file credentials.json
JARVIS> email setup outlook --email user@company.com --password secret

# List and search emails  
JARVIS> email list --unread-only --max-results 10
JARVIS> email search "project meeting" 
JARVIS> email filter --sender boss@company.com --urgent

# Send emails
JARVIS> email send --to colleague@company.com --subject "Meeting Notes" --body "Here are the notes..."
JARVIS> email reply --email-id 123 --message "Thanks for the update"

# Email management
JARVIS> email mark-read --email-id 123
JARVIS> email unread-count
JARVIS> email summary --last-week

# AI features (when available)
JARVIS> email categorize --last-24h
JARVIS> email extract-actions --unread-only
JARVIS> email generate-reply --email-id 123 --context "I'm out of office"
```

## API Reference

### Actions

| Action | Description | Required Parameters |
|--------|-------------|-------------------|
| `setup_gmail` | Configure Gmail access | `credentials` |
| `setup_outlook` | Configure Outlook access | `credentials` |
| `list_emails` | List emails with filtering | `provider`, `filter` (optional) |
| `send_email` | Send new email | `provider`, `email_data` |
| `search_emails` | Search emails by query | `provider`, `query` |
| `mark_read` | Mark email as read | `provider`, `email_id` |
| `get_unread_count` | Get unread email count | `provider` |
| `categorize_emails` | AI email categorization | `provider`, `filter` (optional) |
| `summarize_emails` | AI email summarization | `provider`, `filter` (optional) |
| `generate_reply` | AI reply generation | `provider`, `email_id`, `email_data` |
| `extract_actions` | Extract action items | `provider`, `filter` (optional) |

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `action` | string | Action to perform (required) |
| `provider` | string | Email provider: "gmail" or "outlook" |
| `credentials` | object | Authentication credentials |
| `filter` | object | Email filtering criteria |
| `email_data` | object | Email content for sending |
| `email_id` | string | Specific email ID for operations |
| `query` | string | Search query string |

### Response Format

```python
# Success response
{
    "success": True,
    "data": {...},           # Operation-specific data
    "message": "...",        # Success message
    "provider": "gmail"      # Provider used
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
- **Gmail**: OAuth 2.0 with scope-limited access
- **Outlook**: Username/password or modern auth
- **Token Storage**: Secure local token caching
- **Credential Protection**: No plaintext password storage

### Privacy Features
- **Local Processing**: All data processed locally
- **No Data Sharing**: Emails never sent to external services
- **Secure Storage**: Encrypted token storage
- **Minimal Permissions**: Request only required scopes

### Security Best Practices
1. Use OAuth 2.0 for Gmail (preferred)
2. Enable 2FA on email accounts
3. Use app-specific passwords when possible
4. Regularly rotate credentials
5. Monitor access logs

## Performance Optimization

### Caching
- **Token Caching**: Avoid re-authentication
- **Message Caching**: Cache frequently accessed emails
- **Metadata Caching**: Store email headers locally
- **Search Indexing**: Index email content for faster search

### Async Operations
- **Non-blocking**: All operations use async/await
- **Batch Processing**: Group operations when possible
- **Connection Pooling**: Reuse API connections
- **Rate Limiting**: Respect provider API limits

### Memory Management
- **Streaming**: Stream large email content
- **Pagination**: Fetch emails in pages
- **Garbage Collection**: Clean up unused objects
- **Resource Limits**: Set maximum memory usage

## Error Handling

### Common Issues

1. **Authentication Failures**
   ```python
   # Check credentials and permissions
   if not result["success"]:
       if "authentication" in result["error"].lower():
           print("Please check your credentials")
   ```

2. **API Rate Limits**
   ```python
   # Implement retry with exponential backoff
   if "rate limit" in result["error"].lower():
       await asyncio.sleep(60)  # Wait before retry
   ```

3. **Network Issues**
   ```python
   # Handle connection errors gracefully
   try:
       result = await email_tool.execute(...)
   except ConnectionError:
       print("Network connection failed")
   ```

### Error Codes

| Error Type | Description | Solution |
|------------|-------------|----------|
| `AUTH_FAILED` | Authentication failed | Check credentials |
| `PERMISSION_DENIED` | Insufficient permissions | Update OAuth scopes |
| `RATE_LIMITED` | API rate limit exceeded | Wait and retry |
| `NOT_FOUND` | Email not found | Verify email ID |
| `NETWORK_ERROR` | Connection failed | Check internet connection |

## Testing

### Unit Tests
```bash
# Run email integration tests
python -m pytest tests/test_email_integration.py -v
```

### Integration Tests
```bash  
# Test with real email accounts (requires setup)
python -m pytest tests/test_email_integration.py::TestEmailIntegrationFull -v
```

### Mock Testing
```python
# Use mock providers for testing
with patch('src.plugins.email_integration.EMAIL_DEPS_AVAILABLE', True):
    # Your test code here
    pass
```

## Troubleshooting

### Gmail Issues
1. **Enable Gmail API** in Google Cloud Console
2. **Check OAuth Scopes** - ensure all required scopes are enabled
3. **Verify Credentials File** - download fresh credentials if needed
4. **Token Refresh** - delete token file to force re-authentication

### Outlook Issues  
1. **Check Exchange Server** - verify server address and port
2. **Enable EWS** - ensure Exchange Web Services are enabled
3. **App Passwords** - use app-specific passwords if 2FA is enabled
4. **Modern Auth** - configure modern authentication if available

### General Issues
1. **Check Dependencies** - ensure all packages are installed
2. **Network Connectivity** - verify internet connection
3. **Firewall Settings** - check firewall rules for API access
4. **Log Files** - check JARVIS logs for detailed error messages

## Future Enhancements

### Planned Features
- [ ] **Calendar Integration**: Sync with email events
- [ ] **Contact Management**: Extract and manage contacts
- [ ] **Email Templates**: Reusable email templates
- [ ] **Bulk Operations**: Mass email operations
- [ ] **Advanced Search**: Full-text search with indexing
- [ ] **Email Rules**: Automated email processing rules

### AI Enhancements
- [ ] **Smart Compose**: AI-assisted email writing
- [ ] **Sentiment Analysis**: Detect email tone and sentiment  
- [ ] **Translation**: Multi-language email support
- [ ] **Meeting Extraction**: Automatically create calendar events
- [ ] **Contact Insights**: AI-powered contact analysis
- [ ] **Email Analytics**: Usage patterns and insights

### Integration Features
- [ ] **CRM Integration**: Connect with customer systems
- [ ] **Task Management**: Create tasks from emails
- [ ] **Document Management**: Save attachments automatically
- [ ] **Notification Systems**: Real-time email notifications
- [ ] **Mobile App**: Mobile email management
- [ ] **Voice Commands**: Voice-controlled email operations

---

## Support

For issues and feature requests, please check:
- JARVIS 2.0 Documentation
- GitHub Issues
- Community Discord

**Last Updated**: April 2026  
**Version**: 2.6.0  
**Author**: JARVIS 2.0 Development Team