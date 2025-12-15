from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum

class ConversationStatusEnum(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"

class MessageRoleEnum(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class IntentTypeEnum(str, Enum):
    GENERAL_CHAT = "general_chat"
    INFRASTRUCTURE_QUERY = "infrastructure_query"
    TROUBLESHOOTING = "troubleshooting"
    RESOURCE_ANALYSIS = "resource_analysis"
    COST_OPTIMIZATION = "cost_optimization"
    MONITORING_ALERT = "monitoring_alert"
    REMEDIATION_REQUEST = "remediation_request"
    HELP_REQUEST = "help_request"

# Request/Response Schemas

class ConversationCreateRequest(BaseModel):
    title: Optional[str] = Field(None, description="Conversation title")
    context: Optional[Dict[str, Any]] = Field(None, description="Initial context")

class ConversationResponse(BaseModel):
    id: int
    session_id: str
    user_id: int
    title: Optional[str]
    status: ConversationStatusEnum
    context: Optional[Dict[str, Any]]
    total_messages: int
    total_tokens_used: int
    last_activity: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]

class ConversationListResponse(BaseModel):
    conversations: List[ConversationResponse]
    total: int
    page: int
    per_page: int

class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    role: MessageRoleEnum
    content: str
    model_used: Optional[str]
    tokens_used: int
    response_time: Optional[float]
    cached: bool
    context_snapshot: Optional[Dict[str, Any]]
    created_at: datetime

class ConversationWithMessagesResponse(BaseModel):
    conversation: ConversationResponse
    messages: List[MessageResponse]

class EnhancedChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000, description="User message")
    session_id: Optional[str] = Field(None, description="Session ID for conversation context")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context")
    oci_context: Optional[Dict[str, Any]] = Field(None, description="OCI-specific context")
    enable_intent_recognition: bool = Field(True, description="Enable intent recognition")
    use_templates: bool = Field(True, description="Allow template suggestions")

class EnhancedChatResponse(BaseModel):
    response: str = Field(..., description="AI response")
    session_id: str = Field(..., description="Session ID")
    conversation_id: Optional[int] = Field(None, description="Database conversation ID")
    model: str = Field(..., description="Model used")
    tokens_used: int = Field(..., description="Tokens consumed")
    response_time: float = Field(..., description="Response time in seconds")
    cached: bool = Field(False, description="Whether response was cached")
    intent: Optional["IntentResponse"] = Field(None, description="Detected intent")
    suggested_templates: List["TemplateResponse"] = Field(default_factory=list, description="Suggested query templates")
    oci_insights: Optional[Dict[str, Any]] = Field(None, description="OCI-specific insights")

class IntentResponse(BaseModel):
    intent_type: IntentTypeEnum
    confidence_score: float
    entities: Optional[Dict[str, Any]]

class QueryTemplateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    category: str = Field(..., description="Template category")
    template_text: str = Field(..., description="Template text with variables")
    variables: Optional[Dict[str, Any]] = Field(None, description="Variable definitions")
    requires_role: Optional[str] = Field(None, description="Minimum role required")

class TemplateResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    category: str
    template_text: str
    variables: Optional[Dict[str, Any]]
    usage_count: int
    requires_role: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

class TemplateListResponse(BaseModel):
    templates: List[TemplateResponse]
    total: int
    categories: List[str]

class UseTemplateRequest(BaseModel):
    template_id: int = Field(..., description="Template ID to use")
    variables: Optional[Dict[str, Any]] = Field(None, description="Variable values")
    session_id: Optional[str] = Field(None, description="Session ID")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")

class ConversationExportRequest(BaseModel):
    session_id: str = Field(..., description="Session ID to export")
    format: str = Field("json", description="Export format (json, csv, markdown)")
    include_metadata: bool = Field(True, description="Include metadata in export")

class ConversationExportResponse(BaseModel):
    session_id: str
    format: str
    content: str
    filename: str
    exported_at: datetime

class ConversationAnalyticsResponse(BaseModel):
    user_id: int
    period: str
    total_conversations: int
    total_messages: int
    total_tokens: int
    avg_response_time: float
    intent_breakdown: Dict[str, int]
    top_queries: List[str]
    most_used_templates: List[Dict[str, Any]]

class ChatbotFeedbackRequest(BaseModel):
    session_id: str = Field(..., description="Session ID")
    message_id: Optional[int] = Field(None, description="Specific message ID")
    rating: int = Field(..., ge=1, le=5, description="Rating (1-5)")
    feedback_text: Optional[str] = Field(None, description="Feedback text")
    feedback_type: Optional[str] = Field(None, description="Feedback type")

class FeedbackResponse(BaseModel):
    id: int
    conversation_id: int
    message_id: int
    user_id: int
    rating: int
    feedback_text: Optional[str]
    feedback_type: Optional[str]
    created_at: datetime

class ChatbotHealthResponse(BaseModel):
    status: str
    database_connection: bool
    redis_connection: bool
    ai_service: bool
    intent_recognition: bool
    total_conversations: int
    active_sessions: int
    avg_response_time: float

class SuggestedQueriesResponse(BaseModel):
    infrastructure_queries: List[str]
    monitoring_queries: List[str]
    troubleshooting_queries: List[str]
    cost_queries: List[str]

# Update forward references
EnhancedChatResponse.model_rebuild() 