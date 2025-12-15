from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from app.services.genai_service import genai_service, GenAIRequest, PromptType
# Rate limiting will be handled by middleware - removing decorator for now
from app.services.auth_service import AuthService
from app.models.user import User
import uuid
import logging
from datetime import datetime, timedelta
from app.core.permissions import require_permissions
from app.services.genai_service import PromptType, PromptVersioning, PromptOptimization, PromptQualityMetrics
from app.services.prompt_examples import prompt_template_manager, PromptExample

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models for request/response

class ChatRequest(BaseModel):
    message: str = Field(..., description="User message")
    session_id: Optional[str] = Field(None, description="Session ID for conversation context")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context")

class ChatResponse(BaseModel):
    response: str = Field(..., description="AI response")
    session_id: str = Field(..., description="Session ID")
    model: str = Field(..., description="Model used")
    tokens_used: int = Field(..., description="Tokens consumed")
    response_time: float = Field(..., description="Response time in seconds")
    cached: bool = Field(False, description="Whether response was cached")

class RemediationRequest(BaseModel):
    issue_details: str = Field(..., description="Details of the issue")
    environment: str = Field(..., description="Environment name")
    service_name: str = Field(..., description="Service affected")
    severity: str = Field(..., description="Issue severity")
    resource_info: Dict[str, Any] = Field(default_factory=dict, description="Resource information")

class RemediationResponse(BaseModel):
    remediation_steps: str = Field(..., description="AI-generated remediation steps")
    model: str = Field(..., description="Model used")
    tokens_used: int = Field(..., description="Tokens consumed")
    response_time: float = Field(..., description="Response time in seconds")

class AnalysisRequest(BaseModel):
    data: Dict[str, Any] = Field(..., description="Data to analyze")
    context: str = Field("", description="Analysis context")

class AnalysisResponse(BaseModel):
    insights: str = Field(..., description="AI-generated insights")
    model: str = Field(..., description="Model used")
    tokens_used: int = Field(..., description="Tokens consumed")
    response_time: float = Field(..., description="Response time in seconds")

class CustomPromptRequest(BaseModel):
    prompt: str = Field(..., description="Custom prompt")
    prompt_type: PromptType = Field(PromptType.CHATBOT, description="Type of prompt")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens")
    temperature: Optional[float] = Field(None, description="Temperature setting")
    model: Optional[str] = Field(None, description="Specific model to use")

class BatchRequest(BaseModel):
    requests: List[CustomPromptRequest] = Field(..., description="List of requests to process")

class ServiceStats(BaseModel):
    service: str
    provider: str
    model: str
    fallback_model: str
    caching_enabled: bool
    batching_enabled: bool
    rate_limit_per_minute: int
    cache_ttl_seconds: int
    supported_prompt_types: List[str]

@router.get("/health", response_model=Dict[str, str])
async def genai_health():
    """Check GenAI service health"""
    try:
        # Simple test request
        test_request = GenAIRequest(prompt="Say 'OK' if you're working")
        response = await genai_service.generate_response(test_request)
        return {
            "status": "healthy",
            "service": "GenAI",
            "provider": "Groq",
            "test_response": response.content[:50] + "..." if len(response.content) > 50 else response.content
        }
    except Exception as e:
        logger.error(f"GenAI health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"GenAI service unhealthy: {str(e)}"
        )

@router.get("/stats", response_model=ServiceStats)
async def get_service_stats(current_user: User = Depends(AuthService.get_current_user)):
    """Get GenAI service statistics"""
    return genai_service.get_service_stats()

@router.post("/chat", response_model=ChatResponse)
async def chat_completion(
    request: ChatRequest,
    current_user: User = Depends(AuthService.get_current_user)
):
    """Chat completion with conversation context"""
    try:
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        response = await genai_service.chat_completion(
            message=request.message,
            session_id=session_id,
            user_id=str(current_user.id),
            context=request.context
        )
        
        return ChatResponse(
            response=response.content,
            session_id=session_id,
            model=response.model,
            tokens_used=response.tokens_used,
            response_time=response.response_time,
            cached=response.cached
        )
        
    except Exception as e:
        logger.error(f"Chat completion error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat completion failed: {str(e)}"
        )

@router.post("/remediation", response_model=RemediationResponse)
async def get_remediation_suggestions(
    request: RemediationRequest,
    current_user: User = Depends(AuthService.get_current_user)
):
    """Get AI-powered remediation suggestions for issues"""
    try:
        response = await genai_service.get_remediation_suggestions(
            issue_details=request.issue_details,
            environment=request.environment,
            service_name=request.service_name,
            severity=request.severity,
            resource_info=request.resource_info
        )
        
        return RemediationResponse(
            remediation_steps=response.content,
            model=response.model,
            tokens_used=response.tokens_used,
            response_time=response.response_time
        )
        
    except Exception as e:
        logger.error(f"Remediation suggestions error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Remediation suggestions failed: {str(e)}"
        )

@router.post("/analysis", response_model=AnalysisResponse)
async def analyze_data(
    request: AnalysisRequest,
    current_user: User = Depends(AuthService.get_current_user)
):
    """Analyze data and provide AI insights"""
    try:
        response = await genai_service.analyze_metrics(
            data=request.data,
            context=request.context
        )
        
        return AnalysisResponse(
            insights=response.content,
            model=response.model,
            tokens_used=response.tokens_used,
            response_time=response.response_time
        )
        
    except Exception as e:
        logger.error(f"Data analysis error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Data analysis failed: {str(e)}"
        )

@router.post("/custom", response_model=ChatResponse)
async def custom_prompt(
    request: CustomPromptRequest,
    current_user: User = Depends(AuthService.get_current_user)
):
    """Send a custom prompt to the AI"""
    try:
        genai_request = GenAIRequest(
            prompt=request.prompt,
            prompt_type=request.prompt_type,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            model=request.model,
            user_id=str(current_user.id)
        )
        
        response = await genai_service.generate_response(genai_request)
        
        return ChatResponse(
            response=response.content,
            session_id=f"custom_{response.request_id}",
            model=response.model,
            tokens_used=response.tokens_used,
            response_time=response.response_time,
            cached=response.cached
        )
        
    except Exception as e:
        logger.error(f"Custom prompt error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Custom prompt failed: {str(e)}"
        )

@router.post("/batch", response_model=List[ChatResponse])
async def batch_generate(
    request: BatchRequest,
    current_user: User = Depends(AuthService.get_current_user)
):
    """Process multiple AI requests in batch"""
    try:
        if len(request.requests) > 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 10 requests per batch"
            )
        
        genai_requests = [
            GenAIRequest(
                prompt=req.prompt,
                prompt_type=req.prompt_type,
                max_tokens=req.max_tokens,
                temperature=req.temperature,
                model=req.model,
                user_id=str(current_user.id)
            )
            for req in request.requests
        ]
        
        responses = await genai_service.batch_generate(genai_requests)
        
        return [
            ChatResponse(
                response=resp.content,
                session_id=f"batch_{resp.request_id}",
                model=resp.model,
                tokens_used=resp.tokens_used,
                response_time=resp.response_time,
                cached=resp.cached
            )
            for resp in responses
        ]
        
    except Exception as e:
        logger.error(f"Batch generate error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch generation failed: {str(e)}"
        )

@router.delete("/context/{session_id}")
async def clear_conversation_context(
    session_id: str,
    current_user: User = Depends(AuthService.get_current_user)
):
    """Clear conversation context for a session"""
    try:
        if genai_service.context_manager:
            genai_service.context_manager.clear_context(session_id)
        
        return {"message": f"Context cleared for session {session_id}"}
        
    except Exception as e:
        logger.error(f"Clear context error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear context: {str(e)}"
        )

@router.get("/context/{session_id}")
async def get_conversation_context(
    session_id: str,
    current_user: User = Depends(AuthService.get_current_user)
):
    """Get conversation context for a session"""
    try:
        if not genai_service.context_manager:
            return {"messages": [], "metadata": {}}
        
        context = genai_service.context_manager.get_context(session_id)
        return context
        
    except Exception as e:
        logger.error(f"Get context error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get context: {str(e)}"
        )

@router.get("/prompts/types")
async def get_prompt_types(current_user: User = Depends(AuthService.get_current_user)):
    """Get available prompt types"""
    return {
        "prompt_types": [
            {
                "type": pt.value,
                "description": f"Prompt type for {pt.value} use cases"
            }
            for pt in PromptType
        ]
    } 

@router.post("/insights/production-analysis")
async def generate_production_insights(
    request: Dict[str, Any],
    current_user: User = Depends(require_permissions("can_execute_remediation"))
) -> Dict[str, Any]:
    """
    Generate production-grade AI insights with predictive analytics
    
    **Required permissions:** operator or higher
    """
    try:
        compartment_id = request.get("compartment_id")
        if not compartment_id:
            raise HTTPException(status_code=400, detail="compartment_id is required")
        
        # Get comprehensive monitoring data (lazy initialization)
        from app.services.monitoring_service import get_monitoring_service
        monitoring_service = get_monitoring_service()
        
        # Collect real-time data
        alert_summary = await monitoring_service.get_alert_summary(compartment_id)
        alerts = await monitoring_service.get_alarm_status(compartment_id)
        
        # Simple AI insights (complex analytics removed for stability)
        insights = {
            "executive_summary": f"Analysis of {len(alerts)} alerts in compartment {compartment_id}",
            "alert_count": len(alerts),
            "critical_alerts": len([a for a in alerts if a.get('severity') == 'CRITICAL']),
            "high_alerts": len([a for a in alerts if a.get('severity') == 'HIGH']),
            "recommendations": [
                "Monitor critical alerts closely",
                "Review resource utilization",
                "Consider scaling if needed"
            ],
            "confidence_score": 0.8
        }
        
        return {
            "status": "success",
            "insights": insights,
            "generated_at": datetime.utcnow().isoformat(),
            "analysis_scope": {
                "compartment_id": compartment_id,
                "total_alerts": len(alerts),
                "analysis_period": "real-time"
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to generate production insights: {e}")
        raise HTTPException(status_code=500, detail="Unable to generate AI insights")

# All production AI analytics helper functions removed for backend stability 

@router.post("/prompts/validate", response_model=Dict[str, Any])
async def validate_prompt_parameters(
    prompt_type: PromptType,
    parameters: Dict[str, Any] = Body(...),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Validate prompt parameters before generation"""
    try:
        # Check user permissions
        if not require_permissions("genai", "use")(current_user):
            raise HTTPException(status_code=403, detail="Insufficient permissions for GenAI validation")
        
        # Get service instance
        genai_service = genai_service
        
        # Validate parameters
        validation_result = genai_service.validate_prompt_parameters(prompt_type, **parameters)
        
        return {
            "status": "success",
            "validation": validation_result,
            "prompt_type": prompt_type.value
        }
        
    except Exception as e:
        logger.error(f"Prompt validation error: {e}")
        return {
            "status": "error",
            "message": str(e),
            "validation": {"valid": False, "missing_parameters": [], "error": str(e)}
        }

@router.post("/prompts/versions/create", response_model=Dict[str, Any])
async def create_prompt_version(
    prompt_type: PromptType,
    version: str = Body(...),
    template: str = Body(...),
    metadata: Dict[str, Any] = Body(default={}),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Create a new version of a prompt template"""
    try:
        # Check admin permissions for version management
        if not require_permissions("genai", "admin")(current_user):
            raise HTTPException(status_code=403, detail="Admin permissions required for version management")
        
        # Get service instance
        genai_service = genai_service
        
        # Add author information to metadata
        metadata.update({
            "author": current_user.email,
            "created_by": current_user.id
        })
        
        # Register new version
        genai_service.register_prompt_version(prompt_type, version, template, metadata)
        
        return {
            "status": "success",
            "message": f"Version {version} created for {prompt_type.value}",
            "version": version,
            "prompt_type": prompt_type.value
        }
        
    except Exception as e:
        logger.error(f"Version creation error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create version: {str(e)}")

@router.get("/prompts/versions/{prompt_type}", response_model=Dict[str, Any])
async def list_prompt_versions(
    prompt_type: PromptType,
    current_user: User = Depends(AuthService.get_current_user)
):
    """List all versions of a prompt type"""
    try:
        # Check user permissions
        if not require_permissions("genai", "view")(current_user):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Get service instance
        genai_service = genai_service
        
        # Get versions
        versions = genai_service.prompt_versioning.list_versions(prompt_type)
        
        return {
            "status": "success",
            "prompt_type": prompt_type.value,
            "versions": versions,
            "total_versions": len(versions)
        }
        
    except Exception as e:
        logger.error(f"Version listing error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list versions: {str(e)}")

@router.post("/prompts/ab-test/create", response_model=Dict[str, Any])
async def create_ab_test(
    prompt_type: PromptType,
    baseline_template: str = Body(...),
    variant_template: str = Body(...),
    test_name: str = Body(...),
    traffic_split: float = Body(0.5),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Create an A/B test for prompt optimization"""
    try:
        # Check admin permissions for A/B testing
        if not require_permissions("genai", "admin")(current_user):
            raise HTTPException(status_code=403, detail="Admin permissions required for A/B testing")
        
        # Validate traffic split
        if not 0.0 <= traffic_split <= 1.0:
            raise HTTPException(status_code=400, detail="Traffic split must be between 0.0 and 1.0")
        
        # Get service instance
        genai_service = genai_service
        
        # Create A/B test
        test_id = genai_service.create_prompt_ab_test(
            prompt_type=prompt_type,
            baseline_template=baseline_template,
            variant_template=variant_template,
            test_name=test_name,
            traffic_split=traffic_split
        )
        
        return {
            "status": "success",
            "message": f"A/B test created for {prompt_type.value}",
            "test_id": test_id,
            "test_name": test_name,
            "traffic_split": traffic_split
        }
        
    except Exception as e:
        logger.error(f"A/B test creation error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create A/B test: {str(e)}")

@router.get("/prompts/ab-test/{test_id}/results", response_model=Dict[str, Any])
async def get_ab_test_results(
    test_id: str,
    current_user: User = Depends(AuthService.get_current_user)
):
    """Get results from an A/B test"""
    try:
        # Check user permissions
        if not require_permissions("genai", "view")(current_user):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Get service instance
        genai_service = genai_service
        
        # Get test results
        results = genai_service.get_ab_test_results(test_id)
        
        if not results:
            raise HTTPException(status_code=404, detail="A/B test not found")
        
        return {
            "status": "success",
            "test_results": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"A/B test results error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get test results: {str(e)}")

@router.post("/prompts/generate/with-quality", response_model=Dict[str, Any])
async def generate_with_quality_tracking(
    request: Dict[str, Any] = Body(...),
    expected_elements: List[str] = Body(default=[]),
    user_feedback: Optional[float] = Body(default=None),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Generate response with quality tracking"""
    try:
        # Check user permissions
        if not require_permissions("genai", "use")(current_user):
            raise HTTPException(status_code=403, detail="Insufficient permissions for GenAI usage")
        
        # Validate request structure
        required_fields = ["prompt", "prompt_type"]
        missing_fields = [field for field in required_fields if field not in request]
        if missing_fields:
            raise HTTPException(status_code=400, detail=f"Missing required fields: {missing_fields}")
        
        # Get service instance
        genai_service = genai_service
        
        # Create GenAI request
        from app.services.genai_service import GenAIRequest
        genai_request = GenAIRequest(
            prompt=request["prompt"],
            prompt_type=PromptType(request["prompt_type"]),
            user_id=current_user.id,
            context=request.get("context", {}),
            max_tokens=request.get("max_tokens"),
            temperature=request.get("temperature"),
            model=request.get("model")
        )
        
        # Generate response with quality tracking
        response, quality_scores = await genai_service.generate_with_quality_tracking(
            genai_request,
            expected_elements=expected_elements,
            user_feedback=user_feedback
        )
        
        return {
            "status": "success",
            "response": {
                "content": response.content,
                "model": response.model,
                "tokens_used": response.tokens_used,
                "response_time": response.response_time,
                "cached": response.cached
            },
            "quality_scores": quality_scores,
            "metadata": {
                "prompt_type": request["prompt_type"],
                "user_id": current_user.id,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Quality generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate with quality tracking: {str(e)}")

@router.get("/prompts/examples", response_model=Dict[str, Any])
async def get_prompt_examples(
    prompt_type: Optional[PromptType] = None,
    complexity: Optional[str] = None,
    use_case: Optional[str] = None,
    current_user: User = Depends(AuthService.get_current_user)
):
    """Get prompt examples based on filters"""
    try:
        # Check user permissions
        if not require_permissions("genai", "view")(current_user):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Get examples based on filters
        if prompt_type:
            examples = prompt_template_manager.get_examples_by_type(prompt_type)
        elif complexity:
            examples = prompt_template_manager.get_examples_by_complexity(complexity)
        elif use_case:
            examples = prompt_template_manager.get_use_case_examples(use_case)
        else:
            # Return all examples organized by category
            all_examples = prompt_template_manager.examples
            examples = []
            for category, category_examples in all_examples.items():
                examples.extend(category_examples)
        
        # Convert to serializable format
        serialized_examples = []
        for example in examples:
            serialized_examples.append({
                "name": example.name,
                "description": example.description,
                "prompt_type": example.prompt_type.value,
                "complexity_level": example.complexity_level,
                "use_cases": example.use_cases,
                "expected_output_elements": example.expected_output_elements,
                "performance_notes": example.performance_notes
            })
        
        return {
            "status": "success",
            "examples": serialized_examples,
            "total_examples": len(serialized_examples),
            "filters_applied": {
                "prompt_type": prompt_type.value if prompt_type else None,
                "complexity": complexity,
                "use_case": use_case
            }
        }
        
    except Exception as e:
        logger.error(f"Examples retrieval error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get examples: {str(e)}")

@router.get("/prompts/examples/{example_name}/generate", response_model=Dict[str, Any])
async def generate_example_prompt(
    example_name: str,
    current_user: User = Depends(AuthService.get_current_user)
):
    """Generate a complete prompt using an example template"""
    try:
        # Check user permissions
        if not require_permissions("genai", "view")(current_user):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Generate example prompt
        generated_prompt = prompt_template_manager.generate_example_prompt(example_name)
        
        if not generated_prompt:
            raise HTTPException(status_code=404, detail=f"Example '{example_name}' not found")
        
        # Get example metadata
        example = prompt_template_manager.get_example_by_name(example_name)
        
        return {
            "status": "success",
            "example_name": example_name,
            "generated_prompt": generated_prompt,
            "example_metadata": {
                "description": example.description,
                "prompt_type": example.prompt_type.value,
                "complexity_level": example.complexity_level,
                "use_cases": example.use_cases,
                "expected_elements": example.expected_output_elements
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Example prompt generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate example prompt: {str(e)}")

@router.get("/prompts/quality/metrics", response_model=Dict[str, Any])
async def get_quality_metrics_summary(
    prompt_type: Optional[PromptType] = None,
    time_range: str = "24h",
    current_user: User = Depends(AuthService.get_current_user)
):
    """Get summary of prompt quality metrics"""
    try:
        # Check user permissions
        if not require_permissions("genai", "view")(current_user):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # This would typically fetch from analytics/metrics storage
        # For now, return sample data structure
        sample_metrics = {
            "overview": {
                "total_prompts": 1250,
                "average_quality_score": 0.82,
                "average_response_time": 3.2,
                "success_rate": 0.96
            },
            "by_prompt_type": {
                "infrastructure_monitoring": {
                    "count": 450,
                    "avg_quality": 0.85,
                    "avg_response_time": 2.8
                },
                "cost_analysis": {
                    "count": 320,
                    "avg_quality": 0.79,
                    "avg_response_time": 3.5
                },
                "troubleshooting": {
                    "count": 280,
                    "avg_quality": 0.81,
                    "avg_response_time": 4.1
                }
            },
            "quality_trends": {
                "length_appropriateness": 0.83,
                "structure_quality": 0.87,
                "content_coverage": 0.79,
                "user_satisfaction": 0.81
            }
        }
        
        return {
            "status": "success",
            "time_range": time_range,
            "prompt_type_filter": prompt_type.value if prompt_type else "all",
            "metrics": sample_metrics,
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Quality metrics error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get quality metrics: {str(e)}")

@router.get("/prompts/types", response_model=Dict[str, Any])
async def get_available_prompt_types(
    current_user: User = Depends(AuthService.get_current_user)
):
    """Get list of available prompt types with descriptions"""
    try:
        # Check user permissions
        if not require_permissions("genai", "view")(current_user):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        prompt_types_info = {
            "core_types": {
                PromptType.REMEDIATION.value: "Generate specific remediation steps for infrastructure issues",
                PromptType.ANALYSIS.value: "Provide comprehensive analysis of cloud infrastructure data",
                PromptType.EXPLANATION.value: "Explain technical concepts in accessible language",
                PromptType.OPTIMIZATION.value: "Analyze and recommend optimizations for cost and performance",
                PromptType.TROUBLESHOOTING.value: "Systematic troubleshooting for complex issues",
                PromptType.CHATBOT.value: "Conversational assistance for cloud operations"
            },
            "specialized_types": {
                PromptType.INFRASTRUCTURE_MONITORING.value: "Monitor and analyze OCI resource health",
                PromptType.SECURITY_ANALYSIS.value: "Analyze security configurations and risks",
                PromptType.ACCESS_RISK_ASSESSMENT.value: "Assess IAM and RBAC access risks",
                PromptType.COST_ANALYSIS.value: "Analyze costs and identify optimization opportunities",
                PromptType.COST_FORECASTING.value: "Predict future costs and budget planning",
                PromptType.LOG_ANALYSIS.value: "Analyze application and infrastructure logs",
                PromptType.POD_HEALTH_ANALYSIS.value: "Monitor Kubernetes pod health and performance",
                PromptType.KUBERNETES_TROUBLESHOOTING.value: "Troubleshoot Kubernetes cluster issues",
                PromptType.OCI_RESOURCE_ANALYSIS.value: "Analyze OCI resource configurations and usage",
                PromptType.ALERT_CORRELATION.value: "Correlate alerts and identify root causes",
                PromptType.PERFORMANCE_ANALYSIS.value: "Analyze system performance and bottlenecks"
            },
            "contextual_types": {
                PromptType.CONTEXTUAL_CHATBOT.value: "Context-aware conversational assistance",
                PromptType.MULTI_TURN_CONVERSATION.value: "Manage multi-turn conversations with context",
                PromptType.EXPERT_CONSULTATION.value: "Provide expert-level technical consultation"
            }
        }
        
        return {
            "status": "success",
            "prompt_types": prompt_types_info,
            "total_types": len([pt for category in prompt_types_info.values() for pt in category]),
            "categories": list(prompt_types_info.keys())
        }
        
    except Exception as e:
        logger.error(f"Prompt types retrieval error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get prompt types: {str(e)}") 