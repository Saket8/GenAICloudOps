"""
Pydantic schemas for Cost Analyzer API
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

class CostLevel(str, Enum):
    """Cost level enumeration"""
    CRITICAL = "critical"  # Very high cost
    HIGH = "high"         # High cost
    MEDIUM = "medium"     # Medium cost
    LOW = "low"          # Low cost
    MINIMAL = "minimal"   # Very low cost

class OptimizationType(str, Enum):
    """Optimization type enumeration"""
    RIGHTSIZING = "rightsizing"
    SCALING = "scaling"
    STORAGE_OPTIMIZATION = "storage_optimization"
    RESERVED_INSTANCES = "reserved_instances"
    SPOT_INSTANCES = "spot_instances"
    RESOURCE_CLEANUP = "resource_cleanup"
    SCHEDULING = "scheduling"

class ResourceCostSchema(BaseModel):
    """Schema for individual resource cost"""
    resource_id: str
    resource_name: str
    resource_type: str
    compartment_id: str
    compartment_name: str
    cost_amount: float = Field(..., ge=0)
    currency: str = Field(default="USD")
    period: str  # daily, weekly, monthly
    usage_metrics: Dict[str, Any]
    cost_level: CostLevel
    last_updated: datetime

class TopCostlyResourceSchema(BaseModel):
    """Schema for top costly resources"""
    resource: ResourceCostSchema
    rank: int = Field(..., ge=1)
    cost_percentage: float = Field(..., ge=0, le=100)
    optimization_potential: Optional[float] = Field(default=0, ge=0)

class CostTrendSchema(BaseModel):
    """Schema for cost trends"""
    period: str
    cost_amount: float = Field(..., ge=0)
    change_percentage: Optional[float] = Field(default=0)
    date: datetime

class CostAnomalySchema(BaseModel):
    """Schema for cost anomalies"""
    resource_id: str
    resource_name: str
    anomaly_type: str
    severity: CostLevel
    detected_at: datetime
    current_cost: float = Field(..., ge=0)
    expected_cost: float = Field(..., ge=0)
    deviation_percentage: float
    description: str

class OptimizationRecommendationSchema(BaseModel):
    """Schema for optimization recommendations"""
    recommendation_id: str
    resource_id: str
    resource_name: str
    optimization_type: OptimizationType
    description: str
    estimated_savings: float = Field(..., ge=0)
    effort_level: str  # low, medium, high
    implementation_steps: List[str]
    risk_level: str  # low, medium, high
    priority: int = Field(..., ge=1, le=5)
    ai_confidence: float = Field(default=0.8, ge=0, le=1)

class CostForecastSchema(BaseModel):
    """Schema for cost forecasting"""
    forecast_period: str  # next_month, next_quarter, next_year
    predicted_cost: float = Field(..., ge=0)
    confidence_interval: Dict[str, float]
    factors_considered: List[str]
    forecast_date: datetime

class CompartmentCostBreakdownSchema(BaseModel):
    """Schema for compartment cost breakdown"""
    compartment_id: str
    compartment_name: str
    total_cost: float = Field(..., ge=0)
    cost_percentage: float = Field(..., ge=0, le=100)
    resource_count: int = Field(..., ge=0)
    top_resources: List[TopCostlyResourceSchema]
    cost_trends: List[CostTrendSchema]

class CostSummarySchema(BaseModel):
    """Schema for overall cost summary"""
    total_cost: float = Field(..., ge=0)
    currency: str = Field(default="USD")
    period: str
    resource_count: int = Field(..., ge=0)
    compartment_count: int = Field(..., ge=0)
    cost_distribution: Dict[str, float]
    optimization_potential: float = Field(default=0, ge=0)

# Request Schemas
class CostAnalysisRequest(BaseModel):
    """Request schema for cost analysis"""
    compartment_ids: Optional[List[str]] = Field(default=None)
    resource_types: Optional[List[str]] = Field(default=None)
    period: str = Field(default="monthly")  # daily, weekly, monthly, yearly
    start_date: Optional[datetime] = Field(default=None)
    end_date: Optional[datetime] = Field(default=None)
    include_forecasting: bool = Field(default=False)
    include_optimization: bool = Field(default=True)
    include_anomaly_detection: bool = Field(default=True)

class TopCostlyResourcesRequest(BaseModel):
    """Request schema for top costly resources"""
    compartment_id: Optional[str] = Field(default=None)
    limit: int = Field(default=10, ge=1, le=100)
    period: str = Field(default="monthly")
    resource_types: Optional[List[str]] = Field(default=None)

# Response Schemas
class TopCostlyResourcesResponse(BaseModel):
    """Response schema for top costly resources"""
    status: str
    total_resources: int = Field(..., ge=0)
    period: str
    currency: str = Field(default="USD")
    resources: List[TopCostlyResourceSchema]
    summary: CostSummarySchema
    timestamp: datetime
    compartment_filter: Optional[str] = Field(default=None)

class CostAnalysisResponse(BaseModel):
    """Response schema for comprehensive cost analysis"""
    status: str
    analysis_id: str
    timestamp: datetime
    period: str
    summary: CostSummarySchema
    compartment_breakdown: List[CompartmentCostBreakdownSchema]
    cost_trends: List[CostTrendSchema]
    anomalies: List[CostAnomalySchema]
    recommendations: List[OptimizationRecommendationSchema]
    forecasts: Optional[List[CostForecastSchema]] = Field(default=None)
    ai_insights: Dict[str, Any]  # Dummy AI insights for now

class CostHealthCheckResponse(BaseModel):
    """Response schema for cost analyzer health check"""
    status: str
    oci_billing_available: bool
    cost_data_fresh: bool
    ai_service_available: bool
    last_data_update: Optional[datetime]
    service_name: str = Field(default="CostAnalyzer")
    timestamp: datetime
    version: str = Field(default="1.0.0")
    metrics: Dict[str, Any] 