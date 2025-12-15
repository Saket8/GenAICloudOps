"""
Pydantic schemas for Access Analyzer API
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

class RiskLevel(str, Enum):
    """Risk level enumeration"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class RBACRoleSchema(BaseModel):
    """RBAC Role schema"""
    name: str
    namespace: Optional[str]
    kind: str
    rules: List[Dict[str, Any]]
    created_time: str
    labels: Dict[str, str]

class RBACBindingSchema(BaseModel):
    """RBAC Binding schema"""
    name: str
    namespace: Optional[str]
    kind: str
    role_ref: Dict[str, str]
    subjects: List[Dict[str, Any]]
    created_time: str

class IAMPolicySchema(BaseModel):
    """IAM Policy schema"""
    id: str
    name: str
    compartment_id: str
    compartment_name: str
    description: str
    statements: List[str]
    version_date: str
    time_created: str
    lifecycle_state: str
    risk_score: int = Field(..., ge=0, le=100)
    risk_level: RiskLevel
    recommendations: List[str]

class RBACAnalysisSchema(BaseModel):
    """RBAC Analysis result schema"""
    role: RBACRoleSchema
    bindings: List[RBACBindingSchema]
    risk_score: int = Field(..., ge=0, le=100)
    risk_level: RiskLevel
    security_issues: List[str]
    recommendations: List[str]
    subjects_count: int = Field(..., ge=0)
    permissions_summary: Dict[str, Any]

class RiskDistributionSchema(BaseModel):
    """Risk distribution schema"""
    critical: int = Field(default=0, ge=0)
    high: int = Field(default=0, ge=0)
    medium: int = Field(default=0, ge=0)
    low: int = Field(default=0, ge=0)
    info: int = Field(default=0, ge=0)

class TopRiskItemSchema(BaseModel):
    """Top risk item schema"""
    name: str
    risk_score: int = Field(..., ge=0, le=100)
    risk_level: RiskLevel
    issues_count: Optional[int] = Field(default=0, ge=0)
    recommendations_count: Optional[int] = Field(default=0, ge=0)

class RBACAnalysisSummarySchema(BaseModel):
    """RBAC analysis summary schema"""
    total_roles: int = Field(..., ge=0)
    total_bindings: int = Field(..., ge=0)
    risk_distribution: Dict[str, int]
    top_risks: List[TopRiskItemSchema]

class IAMAnalysisSummarySchema(BaseModel):
    """IAM analysis summary schema"""
    total_policies: int = Field(..., ge=0)
    risk_distribution: Dict[str, int]
    top_risks: List[TopRiskItemSchema]

class AccessAnalysisReportSchema(BaseModel):
    """Combined access analysis report schema"""
    cluster_name: str
    compartment_id: str
    rbac_summary: RBACAnalysisSummarySchema
    iam_summary: IAMAnalysisSummarySchema
    overall_risk_score: int = Field(..., ge=0, le=100)
    overall_risk_level: RiskLevel
    critical_findings: List[str]
    recommendations: List[str]
    generated_at: str

class AccessAnalysisRequest(BaseModel):
    """Request schema for access analysis"""
    compartment_id: str = Field(..., description="OCI compartment ID to analyze")
    namespace: Optional[str] = Field(default=None, description="Kubernetes namespace to analyze (optional)")
    include_root_policies: bool = Field(default=True, description="Include root compartment policies")
    generate_recommendations: bool = Field(default=True, description="Generate AI recommendations")

class RBACAnalysisRequest(BaseModel):
    """Request schema for RBAC analysis"""
    namespace: Optional[str] = Field(default=None, description="Kubernetes namespace to analyze (optional)")

class IAMAnalysisRequest(BaseModel):
    """Request schema for IAM analysis"""
    compartment_id: str = Field(..., description="OCI compartment ID to analyze")

class AccessAnalysisResponse(BaseModel):
    """Response schema for access analysis"""
    success: bool = Field(..., description="Whether the analysis was successful")
    data: Optional[AccessAnalysisReportSchema] = Field(default=None, description="Analysis report data")
    message: str = Field(..., description="Response message")
    execution_time: float = Field(..., description="Execution time in seconds")

class RBACAnalysisResponse(BaseModel):
    """Response schema for RBAC analysis"""
    success: bool = Field(..., description="Whether the analysis was successful")
    data: Optional[List[RBACAnalysisSchema]] = Field(default=None, description="RBAC analysis data")
    message: str = Field(..., description="Response message")
    execution_time: float = Field(..., description="Execution time in seconds")

class IAMAnalysisResponse(BaseModel):
    """Response schema for IAM analysis"""
    success: bool = Field(..., description="Whether the analysis was successful")
    data: Optional[List[IAMPolicySchema]] = Field(default=None, description="IAM analysis data")
    message: str = Field(..., description="Response message")
    execution_time: float = Field(..., description="Execution time in seconds")

class HealthCheckResponse(BaseModel):
    """Health check response schema"""
    status: str = Field(..., description="Service health status")
    kubernetes_available: bool = Field(..., description="Kubernetes service availability")
    oci_available: bool = Field(..., description="OCI service availability")
    genai_available: bool = Field(..., description="GenAI service availability")
    cluster_configured: bool = Field(..., description="Whether cluster is configured")
    message: str = Field(..., description="Status message") 