"""
Cost Analyzer API Endpoints
Provides OCI cost analysis, optimization recommendations, and cost forecasting
"""

import time
import logging
import asyncio
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, Path
from fastapi.responses import JSONResponse
from datetime import datetime

from app.services.cost_analyzer_service import get_cost_analyzer_service
from app.schemas.cost_analyzer import (
    CostAnalysisRequest, CostAnalysisResponse,
    TopCostlyResourcesRequest, TopCostlyResourcesResponse,
    CostHealthCheckResponse
)
from app.core.permissions import check_user_permissions
from app.models.user import User
from app.services.auth_service import AuthService
from app.core.exceptions import ExternalServiceError

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/health", response_model=CostHealthCheckResponse)
async def health_check():
    """
    Health check for the Cost Analyzer service
    """
    try:
        # Get service instance (lazy loading)
        cost_analyzer_service = get_cost_analyzer_service()
        
        health_info = await cost_analyzer_service.health_check()
        
        return CostHealthCheckResponse(
            status=health_info.get("status", "unknown"),
            oci_billing_available=health_info.get("oci_billing_available", False),
            cost_data_fresh=health_info.get("cost_data_fresh", False),
            ai_service_available=health_info.get("ai_service_available", False),
            last_data_update=health_info.get("last_data_update"),
            service_name=health_info.get("service_name", "CostAnalyzer"),
            timestamp=datetime.now(),
            version=health_info.get("version", "1.0.0"),
            metrics=health_info.get("metrics", {})
        )
        
    except Exception as e:
        logger.error(f"Cost analyzer health check failed: {str(e)}")
        return CostHealthCheckResponse(
            status="unhealthy",
            oci_billing_available=False,
            cost_data_fresh=False,
            ai_service_available=False,
            last_data_update=None,
            service_name="CostAnalyzer",
            timestamp=datetime.now(),
            version="1.0.0",
            metrics={"error": str(e)}
        )

@router.get("/top", response_model=TopCostlyResourcesResponse)
async def get_top_costly_resources(
    compartment_id: Optional[str] = Query(None, description="Compartment ID to filter by"),
    limit: int = Query(10, ge=1, le=100, description="Number of top resources to return"),
    period: str = Query("monthly", description="Time period for cost analysis"),
    resource_types: Optional[str] = Query(None, description="Comma-separated list of resource types to filter"),
    current_user: User = Depends(AuthService.get_current_user)
):
    """
    Get top costly resources by compartment or across tenancy
    
    **Required Permission:** can_view_cost_analyzer
    
    **Query Parameters:**
    - **compartment_id**: Optional compartment ID to filter resources
    - **limit**: Number of top resources to return (1-100)
    - **period**: Time period for analysis (daily, weekly, monthly, yearly)
    - **resource_types**: Comma-separated resource types to filter
    
    **Returns:**
    - List of top costly resources with cost details
    - Summary statistics and cost breakdown
    - Optimization potential for each resource
    """
    try:
        start_time = time.time()
        
        # Check permissions
        check_user_permissions(current_user, can_view_cost_analyzer=True)
        
        # Parse resource types if provided
        resource_types_list = None
        if resource_types:
            resource_types_list = [rt.strip() for rt in resource_types.split(",")]
        
        # Create request object
        request = TopCostlyResourcesRequest(
            compartment_id=compartment_id,
            limit=limit,
            period=period,
            resource_types=resource_types_list
        )
        
        # Get service instance
        cost_analyzer_service = get_cost_analyzer_service()
        
        # Perform analysis
        logger.info(f"User {current_user.username} requesting top {limit} costly resources")
        result = await cost_analyzer_service.get_top_costly_resources(request)
        
        # Prepare response
        response = TopCostlyResourcesResponse(
            status=result["status"],
            total_resources=result["total_resources"],
            period=result["period"],
            currency=result["currency"],
            resources=result["resources"],
            summary=result["summary"],
            timestamp=result["timestamp"],
            compartment_filter=result["compartment_filter"]
        )
        
        processing_time = time.time() - start_time
        logger.info(f"Top costly resources analysis completed in {processing_time:.2f}s")
        
        return response
        
    except ExternalServiceError as e:
        logger.error(f"External service error in top costly resources: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")
    except ValueError as e:
        logger.error(f"Invalid request parameters: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid parameters: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error in top costly resources: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error occurred")

@router.post("/analyze", response_model=CostAnalysisResponse)
async def analyze_costs(
    request: CostAnalysisRequest,
    current_user: User = Depends(AuthService.get_current_user)
):
    """
    Perform comprehensive cost analysis across compartments
    
    **Required Permission:** can_view_cost_analyzer
    
    **Request Body:**
    - **compartment_ids**: Optional list of compartment IDs to analyze
    - **resource_types**: Optional list of resource types to include
    - **period**: Time period for analysis (daily, weekly, monthly, yearly)
    - **start_date**: Optional start date for custom period
    - **end_date**: Optional end date for custom period
    - **include_forecasting**: Whether to include cost forecasting
    - **include_optimization**: Whether to include optimization recommendations
    - **include_anomaly_detection**: Whether to detect cost anomalies
    
    **Returns:**
    - Comprehensive cost analysis report
    - Compartment-wise cost breakdown
    - Cost trends and forecasting
    - Anomaly detection results
    - AI-powered optimization recommendations
    """
    try:
        start_time = time.time()
        
        # Check permissions
        check_user_permissions(current_user, can_view_cost_analyzer=True)
        
        # Validate request
        if request.start_date and request.end_date:
            if request.start_date >= request.end_date:
                raise ValueError("start_date must be before end_date")
        
        # Get service instance
        cost_analyzer_service = get_cost_analyzer_service()
        
        # Perform comprehensive analysis
        logger.info(f"User {current_user.username} requesting comprehensive cost analysis")
        result = await cost_analyzer_service.analyze_costs(request)
        
        # Prepare response
        response = CostAnalysisResponse(
            status=result["status"],
            analysis_id=result["analysis_id"],
            timestamp=result["timestamp"],
            period=result["period"],
            summary=result["summary"],
            compartment_breakdown=result["compartment_breakdown"],
            cost_trends=result["cost_trends"],
            anomalies=result["anomalies"],
            recommendations=result["recommendations"],
            forecasts=result.get("forecasts"),
            ai_insights=result["ai_insights"]
        )
        
        processing_time = time.time() - start_time
        logger.info(f"Comprehensive cost analysis completed in {processing_time:.2f}s")
        
        return response
        
    except ExternalServiceError as e:
        logger.error(f"External service error in cost analysis: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")
    except ValueError as e:
        logger.error(f"Invalid request parameters: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid parameters: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error in cost analysis: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error occurred")

@router.get("/insights/summary")
async def get_cost_insights_summary(
    period: str = Query("monthly", description="Time period for insights"),
    current_user: User = Depends(AuthService.get_current_user)
):
    """
    Get high-level cost insights and summary metrics
    
    **Required Permission:** can_view_cost_analyzer
    
    **Returns:**
    - High-level cost metrics
    - Key insights and recommendations
    - Cost health indicators
    """
    try:
        # Check permissions
        check_user_permissions(current_user, can_view_cost_analyzer=True)
        
        # Get service instance
        cost_analyzer_service = get_cost_analyzer_service()
        
        # Generate quick insights
        request = CostAnalysisRequest(
            period=period,
            include_forecasting=False,
            include_optimization=True,
            include_anomaly_detection=True
        )
        
        result = await cost_analyzer_service.analyze_costs(request)
        
        # Extract summary insights
        insights = {
            "total_cost": result["summary"]["total_cost"],
            "currency": result["summary"]["currency"],
            "period": period,
            "optimization_potential": result["summary"]["optimization_potential"],
            "anomaly_count": len(result["anomalies"]),
            "high_priority_recommendations": len([
                r for r in result["recommendations"] 
                if r.get("priority", 0) >= 4
            ]),
            "cost_health_score": result["ai_insights"]["cost_health_score"],
            "key_insights": result["ai_insights"]["key_findings"][:3],
            "timestamp": datetime.now().isoformat()
        }
        
        return JSONResponse(content=insights)
        
    except Exception as e:
        logger.error(f"Error generating cost insights summary: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate insights summary")

@router.get("/recommendations/priority")
async def get_priority_recommendations(
    limit: int = Query(5, ge=1, le=20, description="Number of recommendations to return"),
    min_savings: Optional[float] = Query(None, ge=0, description="Minimum estimated savings"),
    current_user: User = Depends(AuthService.get_current_user)
):
    """
    Get high-priority cost optimization recommendations
    
    **Required Permission:** can_view_cost_analyzer
    
    **Returns:**
    - Prioritized optimization recommendations
    - Estimated savings and implementation effort
    - Risk assessment for each recommendation
    """
    try:
        # Check permissions
        check_user_permissions(current_user, can_view_cost_analyzer=True)
        
        # Get service instance
        cost_analyzer_service = get_cost_analyzer_service()
        
        # Generate recommendations
        request = CostAnalysisRequest(
            include_forecasting=False,
            include_optimization=True,
            include_anomaly_detection=False
        )
        
        result = await cost_analyzer_service.analyze_costs(request)
        recommendations = result["recommendations"]
        
        # Filter and sort recommendations
        if min_savings:
            recommendations = [
                r for r in recommendations 
                if r.get("estimated_savings", 0) >= min_savings
            ]
        
        # Sort by priority and estimated savings
        recommendations.sort(
            key=lambda x: (x.get("priority", 0), x.get("estimated_savings", 0)), 
            reverse=True
        )
        
        # Limit results
        recommendations = recommendations[:limit]
        
        response = {
            "total_recommendations": len(recommendations),
            "total_potential_savings": sum(r.get("estimated_savings", 0) for r in recommendations),
            "recommendations": recommendations,
            "timestamp": datetime.now().isoformat()
        }
        
        return JSONResponse(content=response)
        
    except Exception as e:
        logger.error(f"Error fetching priority recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch recommendations")

@router.get("/trends/{compartment_id}")
async def get_compartment_cost_trends(
    compartment_id: str = Path(..., description="Compartment ID"),
    periods: int = Query(12, ge=1, le=24, description="Number of periods to include"),
    current_user: User = Depends(AuthService.get_current_user)
):
    """
    Get cost trends for a specific compartment
    
    **Required Permission:** can_view_cost_analyzer
    
    **Returns:**
    - Historical cost trends for the compartment
    - Period-over-period changes
    - Trend analysis and patterns
    """
    try:
        # Check permissions
        check_user_permissions(current_user, can_view_cost_analyzer=True)
        
        # Get service instance
        cost_analyzer_service = get_cost_analyzer_service()
        
        # Generate analysis for specific compartment
        request = CostAnalysisRequest(
            compartment_ids=[compartment_id],
            include_forecasting=False,
            include_optimization=False,
            include_anomaly_detection=False
        )
        
        result = await cost_analyzer_service.analyze_costs(request)
        
        # Find the compartment data
        compartment_data = None
        for comp in result["compartment_breakdown"]:
            if comp["compartment_id"] == compartment_id:
                compartment_data = comp
                break
        
        if not compartment_data:
            raise HTTPException(status_code=404, detail="Compartment not found")
        
        # Get trends (limit to requested periods)
        trends = compartment_data["cost_trends"][:periods]
        
        response = {
            "compartment_id": compartment_id,
            "compartment_name": compartment_data["compartment_name"],
            "current_cost": compartment_data["total_cost"],
            "trends": trends,
            "periods_analyzed": len(trends),
            "timestamp": datetime.now().isoformat()
        }
        
        return JSONResponse(content=response)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching compartment trends: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch compartment trends") 