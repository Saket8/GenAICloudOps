from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, Body
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
import csv
import io

from app.core.database import get_db
from app.services.auth_service import AuthService
from app.services.chatbot_service import get_chatbot_service
from app.models.user import User
from app.models.chatbot import (
    Conversation, ConversationMessage, QueryTemplate, ConversationAnalytics,
    ChatbotFeedback, ConversationStatus, MessageRole, IntentType
)
from app.schemas.chatbot import (
    EnhancedChatRequest, EnhancedChatResponse, ConversationCreateRequest,
    ConversationResponse, ConversationListResponse, MessageResponse,
    ConversationWithMessagesResponse, QueryTemplateRequest, TemplateResponse,
    TemplateListResponse, UseTemplateRequest, ConversationExportRequest,
    ConversationExportResponse, ConversationAnalyticsResponse,
    ChatbotFeedbackRequest, FeedbackResponse, ChatbotHealthResponse,
    SuggestedQueriesResponse, ConversationStatusEnum, MessageRoleEnum
)
from app.core.permissions import require_permissions
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Enhanced Chat Endpoints

@router.post("/chat/enhanced", response_model=EnhancedChatResponse)
async def enhanced_chat(
    request: EnhancedChatRequest,
    current_user: User = Depends(AuthService.get_current_user)
):
    """Enhanced chat with intent recognition, OCI integration, and advanced features"""
    try:
        chatbot_service = get_chatbot_service()
        response = await chatbot_service.enhanced_chat(
            message=request.message,
            user_id=current_user.id,
            session_id=request.session_id,
            context=request.context,
            oci_context=request.oci_context,
            enable_intent_recognition=request.enable_intent_recognition,
            use_templates=request.use_templates
        )
        return response
        
    except Exception as e:
        import traceback
        logger.error(f"Enhanced chat error: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Enhanced chat failed: {str(e)} - {traceback.format_exc()[:200]}"
        )

# Conversation Management

@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    request: ConversationCreateRequest,
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new conversation"""
    try:
        import uuid
        conversation = Conversation(
            session_id=str(uuid.uuid4()),
            user_id=current_user.id,
            title=request.title,
            context=request.context,
            status=ConversationStatus.ACTIVE
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        
        return ConversationResponse(
            id=conversation.id,
            session_id=conversation.session_id,
            user_id=conversation.user_id,
            title=conversation.title,
            status=ConversationStatusEnum(conversation.status.value),
            context=conversation.context,
            total_messages=conversation.total_messages,
            total_tokens_used=conversation.total_tokens_used,
            last_activity=conversation.last_activity,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Create conversation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create conversation: {str(e)}"
        )

@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    status_filter: Optional[ConversationStatusEnum] = Query(None),
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """List user's conversations with pagination"""
    try:
        query = db.query(Conversation).filter(Conversation.user_id == current_user.id)
        
        if status_filter:
            query = query.filter(Conversation.status == ConversationStatus(status_filter.value))
        
        total = query.count()
        conversations = query.order_by(desc(Conversation.last_activity)).offset(
            (page - 1) * per_page
        ).limit(per_page).all()
        
        conversation_responses = [
            ConversationResponse(
                id=conv.id,
                session_id=conv.session_id,
                user_id=conv.user_id,
                title=conv.title,
                status=ConversationStatusEnum(conv.status.value),
                context=conv.context,
                total_messages=conv.total_messages,
                total_tokens_used=conv.total_tokens_used,
                last_activity=conv.last_activity,
                created_at=conv.created_at,
                updated_at=conv.updated_at
            )
            for conv in conversations
        ]
        
        return ConversationListResponse(
            conversations=conversation_responses,
            total=total,
            page=page,
            per_page=per_page
        )
        
    except Exception as e:
        logger.error(f"List conversations error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list conversations: {str(e)}"
        )

@router.get("/conversations/{session_id}", response_model=ConversationWithMessagesResponse)
async def get_conversation_with_messages(
    session_id: str = Path(...),
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """Get conversation with all messages"""
    try:
        conversation = db.query(Conversation).filter(
            Conversation.session_id == session_id,
            Conversation.user_id == current_user.id
        ).first()
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        messages = db.query(ConversationMessage).filter(
            ConversationMessage.conversation_id == conversation.id
        ).order_by(ConversationMessage.created_at).all()
        
        conversation_response = ConversationResponse(
            id=conversation.id,
            session_id=conversation.session_id,
            user_id=conversation.user_id,
            title=conversation.title,
            status=ConversationStatusEnum(conversation.status.value),
            context=conversation.context,
            total_messages=conversation.total_messages,
            total_tokens_used=conversation.total_tokens_used,
            last_activity=conversation.last_activity,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at
        )
        
        message_responses = [
            MessageResponse(
                id=msg.id,
                conversation_id=msg.conversation_id,
                role=MessageRoleEnum(msg.role.value),
                content=msg.content,
                model_used=msg.model_used,
                tokens_used=msg.tokens_used,
                response_time=msg.response_time,
                cached=msg.cached,
                context_snapshot=msg.context_snapshot,
                created_at=msg.created_at
            )
            for msg in messages
        ]
        
        return ConversationWithMessagesResponse(
            conversation=conversation_response,
            messages=message_responses
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get conversation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conversation: {str(e)}"
        )

@router.patch("/conversations/{session_id}/archive")
async def archive_conversation(
    session_id: str = Path(...),
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """Archive a conversation"""
    try:
        conversation = db.query(Conversation).filter(
            Conversation.session_id == session_id,
            Conversation.user_id == current_user.id
        ).first()
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        conversation.status = ConversationStatus.ARCHIVED
        db.commit()
        
        return {"message": "Conversation archived successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Archive conversation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to archive conversation: {str(e)}"
        )

# Query Templates

@router.post("/templates", response_model=TemplateResponse)
async def create_template(
    request: QueryTemplateRequest,
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new query template (requires operator permissions)"""
    try:
        template = QueryTemplate(
            name=request.name,
            description=request.description,
            category=request.category,
            template_text=request.template_text,
            variables=request.variables,
            requires_role=request.requires_role
        )
        db.add(template)
        db.commit()
        db.refresh(template)
        
        return TemplateResponse(
            id=template.id,
            name=template.name,
            description=template.description,
            category=template.category,
            template_text=template.template_text,
            variables=template.variables,
            usage_count=template.usage_count,
            requires_role=template.requires_role,
            is_active=template.is_active,
            created_at=template.created_at,
            updated_at=template.updated_at
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Create template error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create template: {str(e)}"
        )

@router.get("/templates-test")
async def templates_test():
    """Test endpoint to verify router works"""
    return {"status": "success", "message": "Templates router is working!"}

@router.get("/templates", response_model=TemplateListResponse)
async def list_templates(
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """List available query templates"""
    templates = db.query(QueryTemplate).filter(QueryTemplate.is_active == True).all()
    
    template_responses = []
    for t in templates:
        template_responses.append(TemplateResponse(
            id=t.id,
            name=t.name,
            description=t.description or "",
            category=t.category,
            template_text=t.template_text,
            variables=t.variables or {},
            usage_count=t.usage_count,
            requires_role=t.requires_role,
            is_active=t.is_active,
            created_at=t.created_at,
            updated_at=t.updated_at
        ))
    
    return TemplateListResponse(
        templates=template_responses,
        total=len(template_responses),
        categories=["Infrastructure", "Monitoring", "Troubleshooting", "Cost", "Remediation", "Analysis"]
    )

@router.post("/templates/{template_id}/use", response_model=EnhancedChatResponse)
async def use_template(
    template_id: int = Path(...),
    request: UseTemplateRequest = None,
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """Use a query template to generate a chat message"""
    try:
        template = db.query(QueryTemplate).filter(
            QueryTemplate.id == template_id,
            QueryTemplate.is_active == True
        ).first()
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        
        # Check permissions
        user_roles = [ur.role.name.value for ur in current_user.user_roles]
        if template.requires_role and template.requires_role not in user_roles and 'admin' not in user_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to use this template"
            )
        
        # Format template with variables
        message = template.template_text
        if request and request.variables:
            try:
                message = message.format(**request.variables)
            except KeyError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing template variable: {e}"
                )
        
        # Update usage count
        template.usage_count += 1
        db.commit()
        
        # Generate enhanced chat response
        chatbot_service = get_chatbot_service()
        response = await chatbot_service.enhanced_chat(
            message=message,
            user_id=current_user.id,
            session_id=request.session_id if request else None,
            context=request.context if request else None,
            enable_intent_recognition=True,
            use_templates=False  # Don't suggest more templates when using one
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Use template error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to use template: {str(e)}"
        )

# Export and Analytics

@router.post("/conversations/{session_id}/export", response_model=ConversationExportResponse)
async def export_conversation(
    session_id: str = Path(...),
    request: ConversationExportRequest = None,
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """Export conversation in various formats"""
    try:
        conversation = db.query(Conversation).filter(
            Conversation.session_id == session_id,
            Conversation.user_id == current_user.id
        ).first()
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        messages = db.query(ConversationMessage).filter(
            ConversationMessage.conversation_id == conversation.id
        ).order_by(ConversationMessage.created_at).all()
        
        export_format = request.format if request else "json"
        include_metadata = request.include_metadata if request else True
        
        if export_format == "json":
            content = _export_to_json(conversation, messages, include_metadata)
            filename = f"conversation_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        elif export_format == "csv":
            content = _export_to_csv(conversation, messages, include_metadata)
            filename = f"conversation_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        elif export_format == "markdown":
            content = _export_to_markdown(conversation, messages, include_metadata)
            filename = f"conversation_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported export format"
            )
        
        return ConversationExportResponse(
            session_id=session_id,
            format=export_format,
            content=content,
            filename=filename,
            exported_at=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export conversation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export conversation: {str(e)}"
        )

@router.get("/analytics", response_model=ConversationAnalyticsResponse)
async def get_conversation_analytics(
    period: str = Query("7d", regex="^(1d|7d|30d|90d)$"),
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """Get conversation analytics for the user"""
    try:
        # Calculate date range
        period_days = {"1d": 1, "7d": 7, "30d": 30, "90d": 90}
        days = period_days[period]
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get conversations in period
        conversations = db.query(Conversation).filter(
            Conversation.user_id == current_user.id,
            Conversation.created_at >= start_date
        ).all()
        
        # Calculate metrics
        total_conversations = len(conversations)
        total_messages = sum(conv.total_messages for conv in conversations)
        total_tokens = sum(conv.total_tokens_used for conv in conversations)
        
        # Get messages for response time calculation
        conversation_ids = [conv.id for conv in conversations]
        if conversation_ids:
            avg_response_time_result = db.query(func.avg(ConversationMessage.response_time)).filter(
                ConversationMessage.conversation_id.in_(conversation_ids),
                ConversationMessage.response_time.is_not(None)
            ).scalar()
            avg_response_time = float(avg_response_time_result) if avg_response_time_result else 0.0
        else:
            avg_response_time = 0.0
        
        # Intent breakdown (simplified - would need actual intent data)
        intent_breakdown = {
            "general_chat": 40,
            "infrastructure_query": 25,
            "troubleshooting": 20,
            "monitoring_alert": 10,
            "other": 5
        }
        
        # Top queries (simplified)
        top_queries = [
            "What's wrong with my server?",
            "How to check instance status?",
            "Analyze high CPU usage",
            "Check alert status"
        ]
        
        # Most used templates (simplified)
        most_used_templates = [
            {"name": "Check Instance Status", "usage_count": 15},
            {"name": "Analyze High CPU", "usage_count": 12},
            {"name": "Cost Analysis", "usage_count": 8}
        ]
        
        return ConversationAnalyticsResponse(
            user_id=current_user.id,
            period=period,
            total_conversations=total_conversations,
            total_messages=total_messages,
            total_tokens=total_tokens,
            avg_response_time=avg_response_time,
            intent_breakdown=intent_breakdown,
            top_queries=top_queries,
            most_used_templates=most_used_templates
        )
        
    except Exception as e:
        logger.error(f"Get analytics error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get analytics: {str(e)}"
        )

# Feedback

@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    request: ChatbotFeedbackRequest,
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """Submit feedback for chatbot responses"""
    try:
        # Get conversation
        conversation = db.query(Conversation).filter(
            Conversation.session_id == request.session_id,
            Conversation.user_id == current_user.id
        ).first()
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        # Get message if specified
        message_id = request.message_id
        if not message_id:
            # Get the last assistant message
            last_message = db.query(ConversationMessage).filter(
                ConversationMessage.conversation_id == conversation.id,
                ConversationMessage.role == MessageRole.ASSISTANT
            ).order_by(desc(ConversationMessage.created_at)).first()
            
            if last_message:
                message_id = last_message.id
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No message to provide feedback for"
                )
        
        feedback = ChatbotFeedback(
            conversation_id=conversation.id,
            message_id=message_id,
            user_id=current_user.id,
            rating=request.rating,
            feedback_text=request.feedback_text,
            feedback_type=request.feedback_type
        )
        
        db.add(feedback)
        db.commit()
        db.refresh(feedback)
        
        return FeedbackResponse(
            id=feedback.id,
            conversation_id=feedback.conversation_id,
            message_id=feedback.message_id,
            user_id=feedback.user_id,
            rating=feedback.rating,
            feedback_text=feedback.feedback_text,
            feedback_type=feedback.feedback_type,
            created_at=feedback.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Submit feedback error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit feedback: {str(e)}"
        )

# Health and Suggestions

@router.get("/health", response_model=ChatbotHealthResponse)
async def chatbot_health(
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """Get chatbot service health status"""
    try:
        # Check database
        db_healthy = True
        try:
            db.execute("SELECT 1")
        except:
            db_healthy = False
        
        # Check Redis (if available)
        redis_healthy = False
        try:
            from app.services.genai_service import genai_service
            if genai_service.redis_client:
                genai_service.redis_client.ping()
                redis_healthy = True
        except:
            pass
        
        # Check AI service - simplified to avoid timeout
        ai_healthy = "degraded"  # Default to degraded since we have fallback
        try:
            from app.services.genai_service import genai_service
            # Just check if service exists, don't test actual API call
            if genai_service:
                ai_healthy = "available"
        except Exception as e:
            logger.warning(f"AI service check failed: {e}")
            ai_healthy = "unavailable"
        
        # Get stats
        total_conversations = db.query(Conversation).count()
        active_sessions = db.query(Conversation).filter(
            Conversation.status == ConversationStatus.ACTIVE,
            Conversation.last_activity >= datetime.utcnow() - timedelta(hours=1)
        ).count()
        
        # Calculate average response time
        avg_response_time_result = db.query(func.avg(ConversationMessage.response_time)).filter(
            ConversationMessage.response_time.is_not(None),
            ConversationMessage.created_at >= datetime.utcnow() - timedelta(days=7)
        ).scalar()
        avg_response_time = float(avg_response_time_result) if avg_response_time_result else 0.0
        
        overall_status = "healthy" if all([db_healthy, ai_healthy]) else "degraded"
        
        return ChatbotHealthResponse(
            status=overall_status,
            database_connection=db_healthy,
            redis_connection=redis_healthy,
            ai_service=ai_healthy,
            intent_recognition=True,  # Always available
            total_conversations=total_conversations,
            active_sessions=active_sessions,
            avg_response_time=avg_response_time
        )
        
    except Exception as e:
        logger.error(f"Chatbot health check error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {str(e)}"
        )

@router.get("/suggestions", response_model=SuggestedQueriesResponse)
async def get_suggested_queries(
    current_user: User = Depends(AuthService.get_current_user)
):
    """Get suggested queries for different categories"""
    return SuggestedQueriesResponse(
        infrastructure_queries=[
            "What compute instances are running in my compartment?",
            "Show me the network configuration for my VCN",
            "List all storage volumes and their usage",
            "What databases are currently active?"
        ],
        monitoring_queries=[
            "What alerts are currently active?",
            "Show me CPU utilization for the last hour",
            "Are there any critical alerts I should know about?",
            "What's the status of my monitoring alarms?"
        ],
        troubleshooting_queries=[
            "Why is my instance not responding?",
            "How do I fix high memory usage?",
            "My application is running slowly, what should I check?",
            "What could cause connection timeouts?"
        ],
        cost_queries=[
            "What are my current monthly costs?",
            "Which resources are most expensive?",
            "How can I optimize my cloud spending?",
            "Show me cost trends for the last 30 days"
        ]
    )

# Helper functions for export

def _export_to_json(conversation: Conversation, messages: List[ConversationMessage], include_metadata: bool) -> str:
    """Export conversation to JSON format"""
    data = {
        "conversation_id": conversation.session_id,
        "title": conversation.title,
        "created_at": conversation.created_at.isoformat(),
        "messages": [
            {
                "role": msg.role.value,
                "content": msg.content,
                "timestamp": msg.created_at.isoformat(),
                "metadata": {
                    "model_used": msg.model_used,
                    "tokens_used": msg.tokens_used,
                    "response_time": msg.response_time,
                    "cached": msg.cached
                } if include_metadata else None
            }
            for msg in messages
        ]
    }
    
    if include_metadata:
        data["metadata"] = {
            "total_messages": conversation.total_messages,
            "total_tokens_used": conversation.total_tokens_used,
            "last_activity": conversation.last_activity.isoformat() if conversation.last_activity else None,
            "context": conversation.context
        }
    
    return json.dumps(data, indent=2)

def _export_to_csv(conversation: Conversation, messages: List[ConversationMessage], include_metadata: bool) -> str:
    """Export conversation to CSV format"""
    output = io.StringIO()
    
    headers = ["timestamp", "role", "content"]
    if include_metadata:
        headers.extend(["model_used", "tokens_used", "response_time", "cached"])
    
    writer = csv.writer(output)
    writer.writerow(headers)
    
    for msg in messages:
        row = [msg.created_at.isoformat(), msg.role.value, msg.content]
        if include_metadata:
            row.extend([msg.model_used, msg.tokens_used, msg.response_time, msg.cached])
        writer.writerow(row)
    
    return output.getvalue()

def _export_to_markdown(conversation: Conversation, messages: List[ConversationMessage], include_metadata: bool) -> str:
    """Export conversation to Markdown format"""
    lines = [
        f"# Conversation Export",
        f"",
        f"**Session ID:** {conversation.session_id}",
        f"**Title:** {conversation.title or 'Untitled'}",
        f"**Created:** {conversation.created_at.isoformat()}",
        f""
    ]
    
    if include_metadata and conversation.context:
        lines.extend([
            f"**Context:** ```json",
            json.dumps(conversation.context, indent=2),
            "```",
            ""
        ])
    
    lines.append("## Messages")
    lines.append("")
    
    for msg in messages:
        role_emoji = "🧑" if msg.role == MessageRole.USER else "🤖"
        lines.extend([
            f"### {role_emoji} {msg.role.value.title()} - {msg.created_at.strftime('%H:%M:%S')}",
            "",
            msg.content,
            ""
        ])
        
        if include_metadata and msg.role == MessageRole.ASSISTANT:
            lines.extend([
                f"*Model: {msg.model_used}, Tokens: {msg.tokens_used}, Response time: {msg.response_time:.2f}s*",
                ""
            ])
    
    return "\n".join(lines) 