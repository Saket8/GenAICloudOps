# Prompt Library API Routes

import time
import json
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.odaos_core.api.middleware.auth import verify_admin
from app.odaos_core.api.services.prompt_service import PromptService
from app.odaos_core.api.models.prompt import (
    Prompt,
    PromptSummary,
    PromptCategory,
    PromptExecuteRequest,
    PromptExecuteResponse,
    PromptCreate,
    PromptUpdate,
    PromptListResponse,
    FavoriteToggleResponse,
    PromptHistoryResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Singleton service instance (initialized on first request)
_prompt_service: Optional[PromptService] = None
_chat_service = None  # ChatService singleton for prompt execution


def get_prompt_service() -> PromptService:
    """Get or create the PromptService singleton."""
    global _prompt_service
    if _prompt_service is None:
        _prompt_service = PromptService()
    return _prompt_service


# ============================================================================
# Read Endpoints (authenticated)
# ============================================================================

@router.get("", response_model=PromptListResponse)
async def list_prompts(
    category: Optional[str] = Query(None, description="Filter by category name"),
    search: Optional[str] = Query(None, description="Search in title, description, tags"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty level"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    username: str = Depends(verify_admin),
    service: PromptService = Depends(get_prompt_service),
):
    """List all active prompts with optional filtering and pagination."""
    return await service.list_prompts(
        category=category,
        search=search,
        tag=tag,
        difficulty=difficulty,
        page=page,
        per_page=per_page,
        user_id=username,
    )


@router.get("/categories", response_model=list[PromptCategory])
async def list_categories(
    username: str = Depends(verify_admin),
    service: PromptService = Depends(get_prompt_service),
):
    """List all prompt categories with prompt counts."""
    return await service.list_categories()


@router.get("/favorites", response_model=list[PromptSummary])
async def get_favorites(
    username: str = Depends(verify_admin),
    service: PromptService = Depends(get_prompt_service),
):
    """Get the current user's favorited prompts."""
    return await service.get_favorites(user_id=username)


@router.get("/history", response_model=PromptHistoryResponse)
async def get_history(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    username: str = Depends(verify_admin),
    service: PromptService = Depends(get_prompt_service),
):
    """Get prompt execution history for the current user."""
    return await service.get_history(
        user_id=username,
        limit=limit,
        offset=offset,
    )


@router.get("/{prompt_id}", response_model=Prompt)
async def get_prompt(
    prompt_id: str,
    username: str = Depends(verify_admin),
    service: PromptService = Depends(get_prompt_service),
):
    """Get a single prompt with full details."""
    prompt = await service.get_prompt(prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return prompt


# ============================================================================
# Favorites Toggle
# ============================================================================

@router.post("/{prompt_id}/favorite", response_model=FavoriteToggleResponse)
async def toggle_favorite(
    prompt_id: str,
    username: str = Depends(verify_admin),
    service: PromptService = Depends(get_prompt_service),
):
    """Toggle favorite status for a prompt."""
    # Verify prompt exists
    prompt = await service.get_prompt(prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return await service.toggle_favorite(user_id=username, prompt_id=prompt_id)


# ============================================================================
# Prompt Execution
# ============================================================================

@router.post("/{prompt_id}/execute")
async def execute_prompt(
    prompt_id: str,
    request: PromptExecuteRequest,
    username: str = Depends(verify_admin),
    service: PromptService = Depends(get_prompt_service),
):
    """Execute a prompt with parameters.
    
    Returns SSE stream matching the chat stream format:
    - event: token (streamed response text)
    - event: done (completion with metadata)
    - event: error (if execution fails)
    """
    # Fetch prompt
    prompt = await service.get_prompt(prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")

    # Merge parameters: defaults first, then user-provided overrides
    merged_params = {**prompt.default_values, **request.parameters}

    # Validate required parameters
    for param in prompt.parameters:
        if param.required and param.name not in merged_params:
            raise HTTPException(
                status_code=422,
                detail=f"Required parameter '{param.name}' is missing",
            )

    # Build final query: use custom_query if provided, otherwise build from template
    if request.custom_query:
        final_query = request.custom_query
    else:
        try:
            final_query = prompt.prompt_template
            for key, value in merged_params.items():
                final_query = final_query.replace(f"{{{key}}}", str(value))
        except Exception as e:
            raise HTTPException(
                status_code=422,
                detail=f"Failed to build query from template: {str(e)}",
            )

    start_time = time.perf_counter()
    execution_id = str(__import__('uuid').uuid4())

    async def event_generator():
        """SSE event generator that streams the prompt execution."""
        result_text = ""
        status = "success"

        try:
            # Use singleton ChatService — avoid re-initializing on every call
            global _chat_service
            if _chat_service is None:
                from app.odaos_core.api.services.chat_service import ChatService
                _chat_service = ChatService()
            chat_service = _chat_service

            # CRITICAL: unique session_id per execution so MemorySaver
            # doesn't bleed context between different prompt runs
            session_id = f"prompt-exec-{execution_id}"
            
            logger.info(
                "[Prompt %s] Executing '%s' | exec_id=%s | session=%s | query_len=%d",
                prompt_id, prompt.title, execution_id[:8], session_id, len(final_query),
            )

            # Use stream_prompt_response — always routes through orchestrator
            # (not viz_service which would discard the structured template)
            async for event in chat_service.stream_prompt_response(
                message=final_query,
                session_id=session_id,
                execution_id=execution_id,
                prompt_category=prompt.category,
            ):
                if isinstance(event, dict):
                    event_type = event.get("type", "token")
                    event_data = json.dumps(event)
                    yield f"event: {event_type}\ndata: {event_data}\n\n"

                    if event_type == "token":
                        result_text += event.get("content", "")
                else:
                    yield f"event: token\ndata: {json.dumps({'content': str(event)})}\n\n"
                    result_text += str(event)

            # Calculate execution time
            execution_time_ms = int((time.perf_counter() - start_time) * 1000)

            # Log execution
            await service.log_execution(
                user_id=username,
                prompt_id=prompt_id,
                parameters_used=merged_params,
                execution_time_ms=execution_time_ms,
                status="success",
                result_summary=result_text[:500] if result_text else None,
            )

            # Send usage event
            usage = chat_service.get_usage_metrics(
                final_query,
                result_text,
                response_time_ms=execution_time_ms
            )
            usage_data = json.dumps({"type": "usage", "data": usage})
            yield f"event: usage\ndata: {usage_data}\n\n"

            # Send done event
            done_data = json.dumps({
                "type": "done",
                "execution_time_ms": execution_time_ms,
                "prompt_id": prompt_id,
                "prompt_title": prompt.title,
                "usage": usage,
            })
            yield f"event: done\ndata: {done_data}\n\n"

        except ImportError:
            # ChatService not available — return a helpful message
            execution_time_ms = int((time.perf_counter() - start_time) * 1000)
            logger.warning("ChatService not available, returning template-only response")

            # Still log the execution
            await service.log_execution(
                user_id=username,
                prompt_id=prompt_id,
                parameters_used=merged_params,
                execution_time_ms=execution_time_ms,
                status="success",
                result_summary=f"[Template mode] {final_query}",
            )

            # Stream the final query as the result
            response_text = (
                f"**Executing Prompt:** {prompt.title}\n\n"
                f"**Query:**\n```\n{final_query}\n```\n\n"
                f"*Note: Full AI pipeline not connected. "
                f"This shows the resolved prompt template.*"
            )
            yield f"event: token\ndata: {json.dumps({'content': response_text})}\n\n"

            usage = {
                "input_tokens": None,
                "output_tokens": None,
                "total_tokens": None,
                "energy_wh": None,
                "co2_g": None,
                "response_time_ms": execution_time_ms,
            }
            usage_data = json.dumps({"type": "usage", "data": usage})
            yield f"event: usage\ndata: {usage_data}\n\n"

            done_data = json.dumps({
                "type": "done",
                "execution_time_ms": execution_time_ms,
                "prompt_id": prompt_id,
                "prompt_title": prompt.title,
                "mode": "template_only",
                "usage": usage,
            })
            yield f"event: done\ndata: {done_data}\n\n"

        except Exception as e:
            execution_time_ms = int((time.perf_counter() - start_time) * 1000)
            logger.error("Prompt execution failed: %s", str(e))

            await service.log_execution(
                user_id=username,
                prompt_id=prompt_id,
                parameters_used=merged_params,
                execution_time_ms=execution_time_ms,
                status="error",
                result_summary=str(e)[:500],
            )

            error_data = json.dumps({
                "type": "error",
                "message": str(e),
                "execution_time_ms": execution_time_ms,
            })
            yield f"event: error\ndata: {error_data}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ============================================================================
# Admin CRUD Endpoints
# ============================================================================

@router.post("/admin", response_model=Prompt)
async def create_prompt(
    data: PromptCreate,
    username: str = Depends(verify_admin),
    service: PromptService = Depends(get_prompt_service),
):
    """Create a new prompt (admin only)."""
    return await service.create_prompt(data)


@router.put("/admin/{prompt_id}", response_model=Prompt)
async def update_prompt(
    prompt_id: str,
    data: PromptUpdate,
    username: str = Depends(verify_admin),
    service: PromptService = Depends(get_prompt_service),
):
    """Update an existing prompt (admin only)."""
    prompt = await service.update_prompt(prompt_id, data)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return prompt


@router.delete("/admin/{prompt_id}")
async def delete_prompt(
    prompt_id: str,
    username: str = Depends(verify_admin),
    service: PromptService = Depends(get_prompt_service),
):
    """Soft-delete a prompt (admin only)."""
    deleted = await service.delete_prompt(prompt_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Prompt not found or already deleted")
    return {"deleted": True, "prompt_id": prompt_id}
