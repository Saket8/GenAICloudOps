from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum

class PromptTypeEnum(str, Enum):
    """Enum for different prompt types"""
    REMEDIATION = "remediation"
    ANALYSIS = "analysis" 
    EXPLANATION = "explanation"
    OPTIMIZATION = "optimization"
    TROUBLESHOOTING = "troubleshooting"
    CHATBOT = "chatbot"

class GenAIRequestSchema(BaseModel):
    """Schema for GenAI requests"""
    prompt: str = Field(..., description="The prompt text")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    prompt_type: PromptTypeEnum = Field(PromptTypeEnum.CHATBOT, description="Type of prompt")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens to generate")
    temperature: Optional[float] = Field(None, description="Temperature for response generation")
    model: Optional[str] = Field(None, description="Specific model to use")
    user_id: Optional[str] = Field(None, description="User ID for rate limiting")
    session_id: Optional[str] = Field(None, description="Session ID for context")

class GenAIResponseSchema(BaseModel):
    """Schema for GenAI responses"""
    content: str = Field(..., description="Generated content")
    model: str = Field(..., description="Model used for generation")
    tokens_used: int = Field(..., description="Number of tokens consumed")
    response_time: float = Field(..., description="Response time in seconds")
    cached: bool = Field(False, description="Whether response was cached")
    timestamp: datetime = Field(..., description="Response timestamp")
    request_id: Optional[str] = Field(None, description="Unique request identifier")

class ChatRequestSchema(BaseModel):
    """Schema for chat completion requests"""
    message: str = Field(..., min_length=1, max_length=4000, description="User message")
    session_id: Optional[str] = Field(None, description="Session ID for conversation context")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context")

class ChatResponseSchema(BaseModel):
    """Schema for chat completion responses"""
    response: str = Field(..., description="AI response")
    session_id: str = Field(..., description="Session ID")
    model: str = Field(..., description="Model used")
    tokens_used: int = Field(..., description="Tokens consumed")
    response_time: float = Field(..., description="Response time in seconds")
    cached: bool = Field(False, description="Whether response was cached")

class RemediationRequestSchema(BaseModel):
    """Schema for remediation suggestion requests"""
    issue_details: str = Field(..., min_length=10, description="Details of the issue")
    environment: str = Field(..., description="Environment name (dev/staging/prod)")
    service_name: str = Field(..., description="Name of the affected service")
    severity: str = Field(..., description="Issue severity level")
    resource_info: Dict[str, Any] = Field(default_factory=dict, description="Resource information")

class RemediationResponseSchema(BaseModel):
    """Schema for remediation suggestion responses"""
    remediation_steps: str = Field(..., description="AI-generated remediation steps")
    model: str = Field(..., description="Model used")
    tokens_used: int = Field(..., description="Tokens consumed")
    response_time: float = Field(..., description="Response time in seconds")

class AnalysisRequestSchema(BaseModel):
    """Schema for data analysis requests"""
    data: Dict[str, Any] = Field(..., description="Data to analyze")
    context: str = Field("", description="Analysis context")

class AnalysisResponseSchema(BaseModel):
    """Schema for data analysis responses"""
    insights: str = Field(..., description="AI-generated insights")
    model: str = Field(..., description="Model used")
    tokens_used: int = Field(..., description="Tokens consumed")
    response_time: float = Field(..., description="Response time in seconds")

class CustomPromptRequestSchema(BaseModel):
    """Schema for custom prompt requests"""
    prompt: str = Field(..., min_length=1, max_length=8000, description="Custom prompt")
    prompt_type: PromptTypeEnum = Field(PromptTypeEnum.CHATBOT, description="Type of prompt")
    max_tokens: Optional[int] = Field(None, ge=1, le=4096, description="Maximum tokens")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="Temperature setting")
    model: Optional[str] = Field(None, description="Specific model to use")

class BatchRequestSchema(BaseModel):
    """Schema for batch processing requests"""
    requests: List[CustomPromptRequestSchema] = Field(
        ..., 
        min_items=1, 
        max_items=10, 
        description="List of requests to process"
    )

class ConversationMessageSchema(BaseModel):
    """Schema for conversation messages"""
    content: str = Field(..., description="Message content")
    role: str = Field(..., description="Message role (user/assistant)")
    timestamp: str = Field(..., description="Message timestamp")

class ConversationContextSchema(BaseModel):
    """Schema for conversation context"""
    messages: List[ConversationMessageSchema] = Field(default_factory=list, description="Conversation messages")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

class ServiceStatsSchema(BaseModel):
    """Schema for service statistics"""
    service: str = Field(..., description="Service name")
    provider: str = Field(..., description="AI provider")
    model: str = Field(..., description="Primary model")
    fallback_model: str = Field(..., description="Fallback model")
    caching_enabled: bool = Field(..., description="Whether caching is enabled")
    batching_enabled: bool = Field(..., description="Whether batching is enabled")
    rate_limit_per_minute: int = Field(..., description="Rate limit per minute")
    cache_ttl_seconds: int = Field(..., description="Cache TTL in seconds")
    supported_prompt_types: List[str] = Field(..., description="Supported prompt types")

class PromptTypeInfo(BaseModel):
    """Schema for prompt type information"""
    type: str = Field(..., description="Prompt type identifier")
    description: str = Field(..., description="Prompt type description")

class PromptTypesResponse(BaseModel):
    """Schema for prompt types response"""
    prompt_types: List[PromptTypeInfo] = Field(..., description="Available prompt types")

class HealthResponseSchema(BaseModel):
    """Schema for health check response"""
    status: str = Field(..., description="Service status")
    service: str = Field(..., description="Service name")
    provider: str = Field(..., description="AI provider")
    test_response: str = Field(..., description="Test response from AI")

class ErrorResponseSchema(BaseModel):
    """Schema for error responses"""
    detail: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")

class SuccessResponseSchema(BaseModel):
    """Schema for success responses"""
    message: str = Field(..., description="Success message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp") 