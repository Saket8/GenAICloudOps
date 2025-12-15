from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON, Enum as SQLEnum, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

# Import the same Base used by other models
from app.models.user import Base

class ConversationStatus(str, enum.Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"

class MessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class IntentType(str, enum.Enum):
    GENERAL_CHAT = "general_chat"
    INFRASTRUCTURE_QUERY = "infrastructure_query"
    TROUBLESHOOTING = "troubleshooting"
    RESOURCE_ANALYSIS = "resource_analysis"
    COST_OPTIMIZATION = "cost_optimization"
    MONITORING_ALERT = "monitoring_alert"
    REMEDIATION_REQUEST = "remediation_request"
    HELP_REQUEST = "help_request"

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Conversation metadata
    title = Column(String(255), nullable=True)  # Auto-generated or user-set title
    status = Column(SQLEnum(ConversationStatus), default=ConversationStatus.ACTIVE)
    context = Column(JSON, nullable=True)  # OCI context, compartment info, etc.
    
    # Analytics
    total_messages = Column(Integer, default=0)
    total_tokens_used = Column(Integer, default=0)
    last_activity = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("ConversationMessage", back_populates="conversation", cascade="all, delete-orphan")
    intents = relationship("ConversationIntent", back_populates="conversation", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Conversation(session_id='{self.session_id}', user_id={self.user_id})>"

class ConversationMessage(Base):
    __tablename__ = "conversation_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    
    # Message content
    role = Column(SQLEnum(MessageRole), nullable=False)
    content = Column(Text, nullable=False)
    
    # AI metadata
    model_used = Column(String(100), nullable=True)
    tokens_used = Column(Integer, default=0)
    response_time = Column(Float, nullable=True)
    cached = Column(Boolean, default=False)
    
    # Context at time of message
    context_snapshot = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    
    def __repr__(self):
        return f"<ConversationMessage(id={self.id}, role='{self.role}', conversation_id={self.conversation_id})>"

class ConversationIntent(Base):
    __tablename__ = "conversation_intents"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    
    # Intent recognition
    intent_type = Column(SQLEnum(IntentType), nullable=False)
    confidence_score = Column(Float, nullable=False)  # 0.0 to 1.0
    entities = Column(JSON, nullable=True)  # Extracted entities (resource names, etc.)
    
    # Associated message
    message_id = Column(Integer, ForeignKey("conversation_messages.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    conversation = relationship("Conversation", back_populates="intents")
    message = relationship("ConversationMessage")
    
    def __repr__(self):
        return f"<ConversationIntent(intent_type='{self.intent_type}', confidence={self.confidence_score})>"

class QueryTemplate(Base):
    __tablename__ = "query_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Template metadata
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=False)  # Infrastructure, Monitoring, Cost, etc.
    
    # Template content
    template_text = Column(Text, nullable=False)
    variables = Column(JSON, nullable=True)  # Variable definitions
    
    # Usage statistics
    usage_count = Column(Integer, default=0)
    
    # Permissions
    requires_role = Column(String(50), nullable=True)  # Minimum role required
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<QueryTemplate(name='{self.name}', category='{self.category}')>"

class ConversationAnalytics(Base):
    __tablename__ = "conversation_analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Time period
    date = Column(DateTime(timezone=True), nullable=False)
    
    # Usage metrics
    total_conversations = Column(Integer, default=0)
    total_messages = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    avg_response_time = Column(Float, default=0.0)
    
    # Intent breakdown
    intent_breakdown = Column(JSON, nullable=True)  # Intent type counts
    
    # Popular queries
    top_queries = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    
    def __repr__(self):
        return f"<ConversationAnalytics(user_id={self.user_id}, date='{self.date}')>"

class ChatbotFeedback(Base):
    __tablename__ = "chatbot_feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    message_id = Column(Integer, ForeignKey("conversation_messages.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Feedback details
    rating = Column(Integer, nullable=False)  # 1-5 scale
    feedback_text = Column(Text, nullable=True)
    feedback_type = Column(String(50), nullable=True)  # helpful, accurate, irrelevant, etc.
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    conversation = relationship("Conversation")
    message = relationship("ConversationMessage")
    user = relationship("User")
    
    def __repr__(self):
        return f"<ChatbotFeedback(id={self.id}, rating={self.rating})>" 