# Conversational Agent (Chatbot) - Task 12 Implementation

## Overview

This document describes the comprehensive chatbot implementation completed for Task 12. The chatbot provides an intelligent conversational interface with advanced features including intent recognition, OCI integration, query templates, and comprehensive analytics.

## Features Implemented

### 🤖 Core Chatbot Features
- **Enhanced Chat Interface**: Advanced chat with multi-turn conversation support
- **Intent Recognition**: Automatic detection of user intent (infrastructure queries, troubleshooting, etc.)
- **Session Management**: Persistent conversation sessions with context preservation
- **Context-Aware Responses**: Leverages conversation history and OCI context for better responses

### 🔍 Intent Recognition System
The chatbot automatically recognizes 8 different intent types:
- `GENERAL_CHAT`: General conversation
- `INFRASTRUCTURE_QUERY`: Questions about infrastructure components
- `TROUBLESHOOTING`: Problem diagnosis and resolution
- `RESOURCE_ANALYSIS`: Resource usage and performance analysis
- `COST_OPTIMIZATION`: Cost analysis and optimization queries
- `MONITORING_ALERT`: Alert-related questions
- `REMEDIATION_REQUEST`: Automated remediation requests
- `HELP_REQUEST`: Help and documentation requests

### 📋 Query Templates
22 predefined query templates across 6 categories:
- **Infrastructure** (4 templates): Instance status, VCN configuration, storage analysis, database health
- **Monitoring** (4 templates): Active alerts, CPU analysis, memory investigation, custom metrics
- **Troubleshooting** (4 templates): Connection timeouts, high latency, service unavailability, performance degradation
- **Cost** (4 templates): Cost analysis, rightsizing, unused resources, cost trends
- **Remediation** (3 templates): Instance restart, application scaling, storage expansion
- **Analysis** (3 templates): Security assessment, capacity planning, compliance reports

### ☁️ OCI Integration
- **Real-time OCI Context**: Integrates with OCI APIs to provide current infrastructure state
- **Compartment-Aware**: Context-aware responses based on OCI compartment information
- **Resource Discovery**: Automatic discovery and analysis of OCI resources
- **Alert Integration**: Real-time alert information from OCI monitoring

### 📊 Analytics & Export
- **Conversation Analytics**: Detailed usage metrics and insights
- **Export Functionality**: Export conversations in JSON, CSV, or Markdown formats
- **Usage Statistics**: Track template usage, response times, and user patterns
- **Feedback System**: Rate and provide feedback on chatbot responses

### 🔒 Security & Permissions
- **Role-Based Access**: Templates and features based on user roles
- **Permission Checks**: Operator-level permissions for sensitive operations
- **Secure Context**: Safe handling of OCI credentials and sensitive data

## API Endpoints

### Enhanced Chat
- `POST /api/v1/chatbot/chat/enhanced` - Enhanced chat with all features
- `GET /api/v1/chatbot/suggestions` - Get suggested queries by category

### Conversation Management
- `POST /api/v1/chatbot/conversations` - Create new conversation
- `GET /api/v1/chatbot/conversations` - List user conversations
- `GET /api/v1/chatbot/conversations/{session_id}` - Get conversation with messages
- `PATCH /api/v1/chatbot/conversations/{session_id}/archive` - Archive conversation

### Query Templates
- `GET /api/v1/chatbot/templates` - List available templates
- `POST /api/v1/chatbot/templates` - Create new template (operator role required)
- `POST /api/v1/chatbot/templates/{template_id}/use` - Use a template

### Analytics & Export
- `GET /api/v1/chatbot/analytics` - Get conversation analytics
- `POST /api/v1/chatbot/conversations/{session_id}/export` - Export conversation
- `POST /api/v1/chatbot/feedback` - Submit feedback

### Health & Monitoring
- `GET /api/v1/chatbot/health` - Chatbot service health status

## Database Schema

### New Tables Added
1. **conversations**: Store conversation metadata and context
2. **conversation_messages**: Individual messages with AI metadata
3. **conversation_intents**: Intent recognition results
4. **query_templates**: Predefined query templates
5. **conversation_analytics**: Usage analytics and metrics
6. **chatbot_feedback**: User feedback on responses

## Usage Examples

### Basic Chat Request
```json
POST /api/v1/chatbot/chat/enhanced
{
  "message": "What's wrong with my web server?",
  "session_id": "optional-session-id",
  "oci_context": {
    "compartment_id": "ocid1.compartment.oc1...",
    "resource_name": "web-server-01"
  },
  "enable_intent_recognition": true,
  "use_templates": true
}
```

### Using a Template
```json
POST /api/v1/chatbot/templates/1/use
{
  "template_id": 1,
  "variables": {
    "instance_name": "web-server-01",
    "compartment_id": "ocid1.compartment.oc1..."
  },
  "session_id": "session-123"
}
```

### Export Conversation
```json
POST /api/v1/chatbot/conversations/session-123/export
{
  "format": "markdown",
  "include_metadata": true
}
```

## Configuration

### Environment Variables
The chatbot uses the existing GenAI service configuration:
- `GROQ_API_KEY`: API key for Groq AI service
- `REDIS_ENABLED`: Enable Redis for caching and session storage
- `GENAI_ENABLE_CACHING`: Enable response caching
- `GENAI_RATE_LIMIT_PER_MINUTE`: Rate limiting configuration

### Database Migration
Run the initialization scripts to set up the database:
```bash
# Create tables
python -c "from app.core.database import create_tables; create_tables()"

# Initialize default templates
python init_chatbot_templates.py
```

## Integration Points

### Existing Services Integration
- **GenAI Service**: Core AI functionality and conversation management
- **Cloud Service**: OCI API integration for real-time data
- **Monitoring Service**: Alert and metrics integration
- **Auth Service**: User authentication and role-based permissions

### Frontend Integration
The chatbot endpoints are designed to work with React frontend components:
- ChatbotPanel component for the main interface
- Template selection and variable input
- Conversation history and export functionality
- Analytics dashboards

## Performance Considerations

### Caching Strategy
- **Redis Caching**: AI responses cached to reduce API calls
- **Session Storage**: Conversation context stored in Redis
- **Template Caching**: Frequently used templates cached for performance

### Rate Limiting
- Per-user rate limiting to prevent abuse
- Gradual backoff for high-usage scenarios
- Priority queuing for different user roles

### Async Operations
- Non-blocking AI API calls
- Async OCI integration for real-time data
- Background processing for analytics

## Security Features

### Data Protection
- Sensitive OCI context handled securely
- User conversations isolated by user ID
- Audit logging for all chatbot interactions

### Permission Model
- Role-based access to templates and features
- Operator permissions required for remediation templates
- Admin oversight for template management

## Monitoring & Observability

### Health Checks
- AI service connectivity monitoring
- Database connection health
- Redis cache status
- Average response time tracking

### Metrics
- Conversation volume and patterns
- Intent recognition accuracy
- Template usage statistics
- User satisfaction ratings

## Future Enhancements

### Planned Features
- Advanced NLP for better intent recognition
- Integration with additional cloud providers
- Voice interface support
- Custom prompt engineering interface
- Machine learning-based response optimization

### Integration Opportunities
- Slack/Teams bot integration
- Email notification integration
- Mobile app support
- API webhook notifications

## Troubleshooting

### Common Issues
1. **Database Connection**: Ensure all tables are created and migrations run
2. **Redis Connection**: Check Redis configuration if caching is enabled
3. **API Key Issues**: Verify Groq API key is valid and has sufficient quota
4. **Permission Errors**: Check user roles and template permissions

### Debug Commands
```bash
# Check database tables
sqlite3 app.db ".tables"

# Test template loading
python init_chatbot_templates.py

# Health check
curl -X GET "http://localhost:8000/api/v1/chatbot/health"
```

## Implementation Summary

Task 12 has been successfully completed with a comprehensive chatbot implementation that includes:

✅ **Database Models**: Complete schema for conversations, intents, templates, and analytics  
✅ **Enhanced Chat Service**: Advanced chatbot with intent recognition and OCI integration  
✅ **API Endpoints**: Full REST API for all chatbot functionality  
✅ **Query Templates**: 22 predefined templates across 6 categories  
✅ **Analytics & Export**: Comprehensive analytics and export capabilities  
✅ **Security & Permissions**: Role-based access and secure data handling  
✅ **Integration**: Seamless integration with existing services and infrastructure  

The chatbot is production-ready and provides a sophisticated conversational interface for cloud operations management. 