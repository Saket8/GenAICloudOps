"""
ODAOS Endpoints — Exposes ODAOS chat, viz, prompt, and session
functionality through the GenAICloudOps API under /api/v1/odaos/*.

All routes are protected by GET current_user (JWT).
"""

import json
import logging
import time
from typing import Optional, Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.api.endpoints.auth import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    session_id: Optional[str] = None
    include_viz: bool = True


class ChatResponse(BaseModel):
    message_id: str
    content: str
    session_id: str
    suggestions: list = []
    chart_data: Optional[dict] = None


class VizRequest(BaseModel):
    query: str = Field(..., min_length=1)
    chart_type: Optional[str] = "auto"
    filters: Optional[dict] = None


class PromptExecuteRequest(BaseModel):
    parameters: dict = {}
    custom_query: Optional[str] = None


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@router.get("/health")
async def odaos_health():
    from app.services.odaos_bridge import is_available
    return {
        "status": "available" if is_available() else "unavailable",
        "service": "ODAOS",
    }


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------

@router.post("/chat", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
):
    """Send a message to the ODAOS orchestrator."""
    from app.services.odaos_bridge import get_chat_service, get_session_service

    chat_service = get_chat_service()
    session_service = get_session_service()

    session_id = request.session_id or str(uuid4())

    response = await chat_service.process_message(
        message=request.message,
        session_id=session_id,
        include_viz=request.include_viz,
    )

    await session_service.add_message(session_id, "user", request.message)
    await session_service.add_message(session_id, "assistant", response["content"])

    return ChatResponse(
        message_id=str(uuid4()),
        content=response["content"],
        session_id=session_id,
        suggestions=response.get("suggestions", []),
        chart_data=response.get("chart_data"),
    )


@router.get("/chat/stream")
async def stream_chat(
    message: str = Query(..., min_length=1, max_length=4000),
    session_id: Optional[str] = None,
    include_viz: bool = True,
    current_user: User = Depends(get_current_user),
):
    """Stream chat response via Server-Sent Events."""
    from app.services.odaos_bridge import get_chat_service, get_session_service
    import asyncio

    chat_service = get_chat_service()
    session_service = get_session_service()
    sid = session_id or str(uuid4())

    async def event_generator():
        try:
            start_time = time.perf_counter()
            await session_service.add_message(sid, "user", message)
            full_response = ""

            async for token in chat_service.stream_response(message, sid):
                full_response += token
                yield f"event: token\ndata: {json.dumps({'type': 'token', 'content': token})}\n\n"
                await asyncio.sleep(0.01)

            await session_service.add_message(sid, "assistant", full_response)

            if include_viz:
                chart_data = await chat_service.generate_chart_if_needed(
                    message, full_response, session_id=sid,
                )
                if chart_data:
                    yield f"event: chart\ndata: {json.dumps({'type': 'chart', 'data': chart_data})}\n\n"

            suggestions = await chat_service.generate_suggestions(message, full_response)
            yield f"event: suggestions\ndata: {json.dumps({'type': 'suggestions', 'items': suggestions})}\n\n"

            response_time_ms = int((time.perf_counter() - start_time) * 1000)
            usage = chat_service.get_usage_metrics(
                message,
                full_response,
                response_time_ms=response_time_ms,
            )
            yield f"event: usage\ndata: {json.dumps({'type': 'usage', 'data': usage})}\n\n"

            yield f"event: done\ndata: {json.dumps({'type': 'done', 'session_id': sid, 'usage': usage})}\n\n"

        except Exception as exc:
            logger.exception("[ODAOS stream] Error")
            yield f"event: error\ndata: {json.dumps({'type': 'error', 'message': str(exc)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ---------------------------------------------------------------------------
# Visualizations
# ---------------------------------------------------------------------------

@router.post("/viz/smart")
async def smart_visualization(
    request: VizRequest,
    current_user: User = Depends(get_current_user),
):
    """Generate a smart visualization from a natural-language query."""
    from app.services.odaos_bridge import get_viz_service
    viz_service = get_viz_service()
    result = await viz_service.generate_smart_viz(
        query=request.query,
        preferred_type=request.chart_type,
        filters=request.filters,
    )
    return result


@router.get("/viz/{chart_type}")
async def get_chart(
    chart_type: Literal["pie", "bar", "line", "scatter", "heatmap", "area"],
    query: str = Query(..., description="Natural language query"),
    filters: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    """Generate a specific chart type."""
    from app.services.odaos_bridge import get_viz_service
    viz_service = get_viz_service()
    filter_dict = json.loads(filters) if filters else None
    return await viz_service.generate_chart(
        chart_type=chart_type, query=query, filters=filter_dict,
    )


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

@router.get("/prompts")
async def list_prompts(
    category: Optional[str] = None,
    search: Optional[str] = None,
    tag: Optional[str] = None,
    difficulty: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
):
    """List ODAOS prompts with optional filtering."""
    from app.services.odaos_bridge import get_prompt_service
    service = get_prompt_service()
    return await service.list_prompts(
        category=category, search=search, tag=tag,
        difficulty=difficulty, page=page, per_page=per_page,
        user_id=current_user.username,
    )


@router.get("/prompts/categories")
async def list_categories(
    current_user: User = Depends(get_current_user),
):
    from app.services.odaos_bridge import get_prompt_service
    return await get_prompt_service().list_categories()


@router.get("/prompts/favorites")
async def get_favorites(
    current_user: User = Depends(get_current_user),
):
    from app.services.odaos_bridge import get_prompt_service
    return await get_prompt_service().get_favorites(user_id=current_user.username)


@router.get("/prompts/history")
async def get_history(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
):
    from app.services.odaos_bridge import get_prompt_service
    return await get_prompt_service().get_history(
        user_id=current_user.username, limit=limit, offset=offset,
    )


@router.get("/prompts/{prompt_id}")
async def get_prompt(
    prompt_id: str,
    current_user: User = Depends(get_current_user),
):
    from app.services.odaos_bridge import get_prompt_service
    prompt = await get_prompt_service().get_prompt(prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return prompt


@router.post("/prompts/{prompt_id}/favorite")
async def toggle_favorite(
    prompt_id: str,
    current_user: User = Depends(get_current_user),
):
    from app.services.odaos_bridge import get_prompt_service
    service = get_prompt_service()
    prompt = await service.get_prompt(prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return await service.toggle_favorite(
        user_id=current_user.username, prompt_id=prompt_id,
    )


@router.post("/prompts/{prompt_id}/execute")
async def execute_prompt(
    prompt_id: str,
    request: PromptExecuteRequest,
    current_user: User = Depends(get_current_user),
):
    """Execute a prompt and stream results via SSE."""
    from app.services.odaos_bridge import get_prompt_service, get_chat_service
    import asyncio

    service = get_prompt_service()
    prompt = await service.get_prompt(prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")

    merged_params = {**prompt.default_values, **request.parameters}

    for param in prompt.parameters:
        if param.required and param.name not in merged_params:
            raise HTTPException(
                status_code=422,
                detail=f"Required parameter '{param.name}' is missing",
            )

    if request.custom_query:
        final_query = request.custom_query
    else:
        final_query = prompt.prompt_template
        for key, value in merged_params.items():
            final_query = final_query.replace(f"{{{key}}}", str(value))

    start_time = time.perf_counter()
    execution_id = str(uuid4())

    async def event_generator():
        result_text = ""
        try:
            chat_service = get_chat_service()
            session_id = f"prompt-exec-{execution_id}"

            async for event in chat_service.stream_prompt_response(
                message=final_query,
                session_id=session_id,
                execution_id=execution_id,
                prompt_category=prompt.category,
            ):
                if isinstance(event, dict):
                    event_type = event.get("type", "token")
                    yield f"event: {event_type}\ndata: {json.dumps(event)}\n\n"
                    if event_type == "token":
                        result_text += event.get("content", "")
                else:
                    yield f"event: token\ndata: {json.dumps({'content': str(event)})}\n\n"
                    result_text += str(event)

            execution_time_ms = int((time.perf_counter() - start_time) * 1000)
            await service.log_execution(
                user_id=current_user.username,
                prompt_id=prompt_id,
                parameters_used=merged_params,
                execution_time_ms=execution_time_ms,
                status="success",
                result_summary=result_text[:500] if result_text else None,
            )

            usage = chat_service.get_usage_metrics(
                final_query,
                result_text,
                response_time_ms=execution_time_ms,
            )
            yield f"event: usage\ndata: {json.dumps({'type': 'usage', 'data': usage})}\n\n"

            done = json.dumps({
                "type": "done",
                "execution_time_ms": execution_time_ms,
                "prompt_id": prompt_id,
                "prompt_title": prompt.title,
                "usage": usage,
            })
            yield f"event: done\ndata: {done}\n\n"

        except Exception as exc:
            execution_time_ms = int((time.perf_counter() - start_time) * 1000)
            logger.exception("[ODAOS prompt exec] Error")
            await service.log_execution(
                user_id=current_user.username,
                prompt_id=prompt_id,
                parameters_used=merged_params,
                execution_time_ms=execution_time_ms,
                status="error",
                result_summary=str(exc)[:500],
            )
            yield f"event: error\ndata: {json.dumps({'type': 'error', 'message': str(exc)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------

@router.get("/sessions")
async def list_sessions(
    current_user: User = Depends(get_current_user),
):
    from app.services.odaos_bridge import get_session_service
    return await get_session_service().list_sessions()


@router.get("/sessions/{session_id}")
async def get_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
):
    from app.services.odaos_bridge import get_session_service
    return await get_session_service().get_session(session_id)
