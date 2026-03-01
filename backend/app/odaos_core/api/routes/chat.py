# Chat API Routes with SSE Streaming

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
from typing import Optional
import json
import asyncio
import time
from uuid import uuid4
from datetime import datetime

from app.odaos_core.api.models.chat import ChatRequest, ChatResponse, StreamEvent
from app.odaos_core.api.services.chat_service import ChatService
from app.odaos_core.api.services.session_service import SessionService


router = APIRouter()

# Services (will be dependency injected)
chat_service = ChatService()
session_service = SessionService()


@router.post("/", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    """
    Send a chat message and get a complete response.
    Use /stream for real-time streaming responses.
    """
    session_id = request.session_id or str(uuid4())
    
    # Process through orchestrator
    response = await chat_service.process_message(
        message=request.message,
        session_id=session_id,
        include_viz=request.include_viz
    )
    
    # Save to session history
    await session_service.add_message(session_id, "user", request.message)
    await session_service.add_message(session_id, "assistant", response["content"])
    
    return ChatResponse(
        message_id=str(uuid4()),
        content=response["content"],
        session_id=session_id,
        suggestions=response.get("suggestions", []),
        chart_data=response.get("chart_data")
    )


@router.get("/stream")
async def stream_chat(
    message: str = Query(..., min_length=1, max_length=4000),
    session_id: Optional[str] = None,
    include_viz: bool = True
):
    """
    Stream chat response via Server-Sent Events (SSE).
    
    Events:
    - token: Individual response tokens
    - chart: Visualization data
    - suggestions: Follow-up question suggestions
    - insight: Proactive AI insight
    - done: Stream complete
    - error: Error occurred
    """
    session_id = session_id or str(uuid4())
    
    async def event_generator():
        try:
            start_time = time.perf_counter()

            # Save user message
            await session_service.add_message(session_id, "user", message)
            
            full_response = ""
            
            # Stream LLM response tokens
            async for token in chat_service.stream_response(message, session_id):
                full_response += token
                yield {
                    "event": "token",
                    "data": json.dumps({"type": "token", "content": token})
                }
                await asyncio.sleep(0.01)  # Prevent overwhelming the client
            
            # Save assistant response
            await session_service.add_message(session_id, "assistant", full_response)
            
            # Generate chart if applicable
            if include_viz:
                chart_data = await chat_service.generate_chart_if_needed(message, full_response, session_id=session_id)
                if chart_data:
                    yield {
                        "event": "chart",
                        "data": json.dumps({"type": "chart", "data": chart_data})
                    }
            
            # Generate follow-up suggestions
            suggestions = await chat_service.generate_suggestions(message, full_response)
            yield {
                "event": "suggestions",
                "data": json.dumps({"type": "suggestions", "items": suggestions})
            }
            
            # Check for proactive insights
            insights = await chat_service.get_proactive_insights(message)
            for insight in insights:
                yield {
                    "event": "insight",
                    "data": json.dumps({"type": "insight", "data": insight})
                }
            
            # Signal usage metrics
            response_time_ms = int((time.perf_counter() - start_time) * 1000)
            usage = chat_service.get_usage_metrics(
                message,
                full_response,
                response_time_ms=response_time_ms
            )
            yield {
                "event": "usage",
                "data": json.dumps({"type": "usage", "data": usage})
            }
            
            # Signal completion
            yield {
                "event": "done",
                "data": json.dumps({
                    "type": "done",
                    "session_id": session_id,
                    "usage": usage,
                })
            }
            
        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps({"type": "error", "message": str(e)})
            }
    
    return EventSourceResponse(event_generator())


@router.get("/suggestions")
async def get_suggestions(
    context: Optional[str] = None,
    category: Optional[str] = None
):
    """Get quick reply suggestions based on context."""
    suggestions = await chat_service.get_quick_replies(context, category)
    return {"suggestions": suggestions}


@router.get("/templates")
async def get_query_templates():
    """Get predefined query templates for common questions."""
    templates = [
        {
            "category": "Customer Insights",
            "queries": [
                "Show customer distribution by region",
                "Which products are selling best?",
                "What's our customer churn rate?"
            ]
        },
        {
            "category": "Revenue Analysis",
            "queries": [
                "Show monthly revenue trends",
                "Compare revenue by product category",
                "What's our average revenue per user?"
            ]
        },
        {
            "category": "Risk Management",
            "queries": [
                "Who are our high-risk customers?",
                "Show overdue payment analysis",
                "Identify anomalies in billing data"
            ]
        },
        {
            "category": "Database Health",
            "queries": [
                "How is the database performing?",
                "Show tablespace usage",
                "Are there any blocking sessions?"
            ]
        }
    ]
    return {"templates": templates}
