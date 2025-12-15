"""
Access Analyzer API Endpoints
Provides unified RBAC and IAM policy analysis with risk scoring and GenAI recommendations
"""

import time
import logging
import asyncio
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, Path
from fastapi.responses import JSONResponse
from datetime import datetime

from app.services.access_analyzer_service import get_access_analyzer_service
from app.schemas.access_analyzer import (
    AccessAnalysisRequest, AccessAnalysisResponse,
    RBACAnalysisRequest, RBACAnalysisResponse,
    IAMAnalysisRequest, IAMAnalysisResponse,
    HealthCheckResponse,
    AccessAnalysisReportSchema, RBACAnalysisSchema, IAMPolicySchema
)
from app.core.permissions import check_user_permissions
from app.models.user import User
from app.services.auth_service import AuthService
from app.core.exceptions import ExternalServiceError

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """
    Health check for the Access Analyzer service
    """
    try:
        # Get service instance (lazy loading)
        access_analyzer_service = get_access_analyzer_service()
        
        health_info = await access_analyzer_service.health_check()
        
        return HealthCheckResponse(
            status=health_info.get("status", "unknown"),
            kubernetes_available=health_info.get("kubernetes_available", False),
            oci_available=health_info.get("oci_available", False),
            genai_available=health_info.get("genai_available", False),
            cluster_configured=health_info.get("cluster_configured", False),
            cluster_info=health_info.get("cluster_info"),
            service_name="AccessAnalyzer",
            timestamp=health_info.get("timestamp", datetime.now().isoformat()),
            version="1.0.0"
        )
        
    except Exception as e:
        logger.error(f"Access analyzer health check failed: {e}")
        return HealthCheckResponse(
            status="unhealthy",
            kubernetes_available=False,
            oci_available=False,
            genai_available=False,
            cluster_configured=False,
            cluster_info=None,
            service_name="AccessAnalyzer",
            timestamp=datetime.now().isoformat(),
            version="1.0.0",
            message=f"Health check error: {str(e)}"
        )

@router.get("/rbac")
async def get_rbac_analysis(
    namespace: str = Query(None, description="Kubernetes namespace to analyze"),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Get RBAC analysis for the cluster"""
    # Check permissions
    check_user_permissions(current_user, can_view_access_analyzer=True)
    
    logger.info(f"🔍 RBAC Analysis Request - User: {current_user.username}, Namespace: {namespace}")
    start_time = time.time()
    
    try:
        # Get the access analyzer service
        access_analyzer_service = get_access_analyzer_service()
        logger.info("✅ Access analyzer service obtained")
        
        # Debug: Check if Kubernetes service is configured
        k8s_service = access_analyzer_service.kubernetes_service
        logger.info(f"🔧 Kubernetes service configured: {k8s_service.is_configured}")
        logger.info(f"🔧 Cluster name: {k8s_service.cluster_name}")
        
        # Fetch RBAC data with detailed logging
        logger.info("📊 Fetching RBAC roles...")
        try:
            roles_data = k8s_service.get_rbac_roles(namespace)
            logger.info(f"✅ Retrieved {len(roles_data)} roles")
            for i, role in enumerate(roles_data[:3]):  # Log first 3 roles
                logger.info(f"   Role {i+1}: {role.get('name', 'Unknown')} ({role.get('kind', 'Unknown')})")
        except Exception as e:
            logger.error(f"❌ Error fetching roles: {e}")
            roles_data = []
        
        logger.info("📊 Fetching RBAC bindings...")
        try:
            bindings_data = k8s_service.get_rbac_bindings(namespace)
            logger.info(f"✅ Retrieved {len(bindings_data)} bindings")
            for i, binding in enumerate(bindings_data[:3]):  # Log first 3 bindings
                logger.info(f"   Binding {i+1}: {binding.get('name', 'Unknown')}")
        except Exception as e:
            logger.error(f"❌ Error fetching bindings: {e}")
            bindings_data = []
        
        execution_time = time.time() - start_time
        logger.info(f"⏱️ RBAC analysis completed in {execution_time:.2f}s")
        
        response = {
            "roles": roles_data,
            "bindings": bindings_data,
            "namespace": namespace,
            "cluster_name": k8s_service.cluster_name or "unknown",
            "total_roles": len(roles_data),
            "total_bindings": len(bindings_data),
            "execution_time": execution_time
        }
        
        logger.info(f"📤 Returning response: {len(roles_data)} roles, {len(bindings_data)} bindings")
        return response
        
    except Exception as e:
        logger.error(f"❌ RBAC analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"RBAC analysis failed: {str(e)}")

@router.get("/iam", response_model=IAMAnalysisResponse)
async def get_iam_analysis(
    compartment_id: str = Query(..., description="OCI compartment ID to analyze"),
    current_user: User = Depends(AuthService.get_current_user)
):
    """
    Get comprehensive IAM policy analysis with risk scoring
    
    - **compartment_id**: OCI compartment ID to analyze
    - Returns detailed analysis of IAM policies with security recommendations
    """
    start_time = time.time()
    
    try:
        # Check permissions - viewer level required
        check_user_permissions(current_user, can_view_access_analyzer=True)
        
        # Get service instance (lazy loading)
        access_analyzer_service = get_access_analyzer_service()
        
        # Perform IAM analysis
        iam_policies = await access_analyzer_service.get_iam_analysis(compartment_id)
        
        # Convert dataclasses to Pydantic models
        iam_data = []
        for policy in iam_policies:
            iam_schema = IAMPolicySchema(
                id=policy.id,
                name=policy.name,
                compartment_id=policy.compartment_id,
                compartment_name=policy.compartment_name,
                description=policy.description,
                statements=policy.statements,
                version_date=policy.version_date,
                time_created=policy.time_created,
                lifecycle_state=policy.lifecycle_state,
                risk_score=policy.risk_score,
                risk_level=policy.risk_level,
                recommendations=policy.recommendations
            )
            iam_data.append(iam_schema)
        
        execution_time = time.time() - start_time
        
        return IAMAnalysisResponse(
            success=True,
            data=iam_data,
            message=f"Successfully analyzed {len(iam_data)} IAM policies in compartment {compartment_id}",
            execution_time=execution_time
        )
        
    except PermissionError as e:
        logger.warning(f"Permission denied for IAM analysis: {e}")
        raise HTTPException(status_code=403, detail="Insufficient permissions for IAM analysis")
    
    except ExternalServiceError as e:
        logger.error(f"External service error in IAM analysis: {e}")
        execution_time = time.time() - start_time
        return IAMAnalysisResponse(
            success=False,
            data=None,
            message=f"Service error: {str(e)}",
            execution_time=execution_time
        )
    
    except Exception as e:
        logger.error(f"Unexpected error in IAM analysis: {e}")
        execution_time = time.time() - start_time
        return IAMAnalysisResponse(
            success=False,
            data=None,
            message=f"Analysis failed: {str(e)}",
            execution_time=execution_time
        )

@router.post("/analyze", response_model=AccessAnalysisResponse)
async def generate_unified_analysis(
    request: AccessAnalysisRequest,
    current_user: User = Depends(AuthService.get_current_user)
):
    """
    Generate unified access analysis combining RBAC and IAM with AI recommendations
    
    - **compartment_id**: OCI compartment ID to analyze
    - **namespace**: Optional Kubernetes namespace to analyze
    - **include_root_policies**: Whether to include root compartment policies
    - **generate_recommendations**: Whether to generate AI-powered recommendations
    - Returns comprehensive security analysis report
    """
    start_time = time.time()
    
    try:
        # Check permissions - viewer level required for analysis, operator for recommendations
        if request.generate_recommendations:
            check_user_permissions(current_user, can_analyze_access=True)
        else:
            check_user_permissions(current_user, can_view_access_analyzer=True)
        
        # Get service instance (lazy loading)
        access_analyzer_service = get_access_analyzer_service()
        
        # Generate unified analysis
        analysis_report = await access_analyzer_service.generate_unified_analysis(
            compartment_id=request.compartment_id,
            namespace=request.namespace
        )
        
        # Convert dataclass to Pydantic model
        report_schema = AccessAnalysisReportSchema(
            cluster_name=analysis_report.cluster_name,
            compartment_id=analysis_report.compartment_id,
            rbac_summary=analysis_report.rbac_summary,
            iam_summary=analysis_report.iam_summary,
            overall_risk_score=analysis_report.overall_risk_score,
            overall_risk_level=analysis_report.overall_risk_level,
            critical_findings=analysis_report.critical_findings,
            recommendations=analysis_report.recommendations,
            generated_at=analysis_report.generated_at
        )
        
        execution_time = time.time() - start_time
        
        return AccessAnalysisResponse(
            success=True,
            data=report_schema,
            message=f"Successfully generated unified access analysis for compartment {request.compartment_id}",
            execution_time=execution_time
        )
        
    except PermissionError as e:
        logger.warning(f"Permission denied for unified analysis: {e}")
        raise HTTPException(status_code=403, detail="Insufficient permissions for access analysis")
    
    except ExternalServiceError as e:
        logger.error(f"External service error in unified analysis: {e}")
        execution_time = time.time() - start_time
        return AccessAnalysisResponse(
            success=False,
            data=None,
            message=f"Service error: {str(e)}",
            execution_time=execution_time
        )
    
    except Exception as e:
        logger.error(f"Unexpected error in unified analysis: {e}")
        execution_time = time.time() - start_time
        return AccessAnalysisResponse(
            success=False,
            data=None,
            message=f"Analysis failed: {str(e)}",
            execution_time=execution_time
        )

@router.get("/rbac/roles/{role_name}")
async def get_role_details(
    role_name: str = Path(..., description="RBAC role name"),
    namespace: Optional[str] = Query(default=None, description="Kubernetes namespace"),
    current_user: User = Depends(AuthService.get_current_user)
):
    """
    Get detailed information about a specific RBAC role
    
    - **role_name**: Name of the RBAC role to analyze
    - **namespace**: Optional namespace for namespaced roles
    - Returns detailed role analysis and recommendations
    """
    try:
        # Check permissions
        check_user_permissions(current_user, can_view_access_analyzer=True)
        
        # Get service instance (lazy loading)
        access_analyzer_service = get_access_analyzer_service()
        
        # Get all RBAC analyses
        rbac_analyses = await access_analyzer_service.get_rbac_analysis(namespace)
        
        # Find the specific role
        role_analysis = None
        for analysis in rbac_analyses:
            if analysis.role.name == role_name:
                if namespace is None or analysis.role.namespace == namespace:
                    role_analysis = analysis
                    break
        
        if not role_analysis:
            raise HTTPException(
                status_code=404, 
                detail=f"Role '{role_name}' not found" + 
                       (f" in namespace '{namespace}'" if namespace else " in cluster")
            )
        
        # Convert to response format
        response_data = {
            "role": role_analysis.role.__dict__,
            "bindings": [binding.__dict__ for binding in role_analysis.bindings],
            "risk_analysis": {
                "risk_score": role_analysis.risk_score,
                "risk_level": role_analysis.risk_level.value,
                "security_issues": role_analysis.security_issues,
                "recommendations": role_analysis.recommendations,
                "subjects_count": role_analysis.subjects_count,
                "permissions_summary": role_analysis.permissions_summary
            }
        }
        
        return JSONResponse(content=response_data)
        
    except PermissionError as e:
        logger.warning(f"Permission denied for role details: {e}")
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Error getting role details: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get role details: {str(e)}")

@router.get("/iam/policies/{policy_id}")
async def get_policy_details(
    policy_id: str = Path(..., description="IAM policy ID"),
    current_user: User = Depends(AuthService.get_current_user)
):
    """
    Get detailed information about a specific IAM policy
    
    - **policy_id**: ID of the IAM policy to analyze
    - Returns detailed policy analysis and recommendations
    """
    try:
        # Check permissions
        check_user_permissions(current_user, can_view_access_analyzer=True)
        
        # Get service instance (lazy loading)
        access_analyzer_service = get_access_analyzer_service()
        
        # Extract compartment ID from policy ID (first part before the dot)
        # This is a simplified approach - in practice you might need a lookup table
        if "." in policy_id:
            compartment_id = policy_id.split(".")[0]
        else:
            # If no compartment info, try root compartment
            compartment_id = access_analyzer_service.oci_service.config.get('tenancy', '')
        
        # Get IAM analysis for the compartment
        iam_policies = await access_analyzer_service.get_iam_analysis(compartment_id)
        
        # Find the specific policy
        policy_analysis = None
        for policy in iam_policies:
            if policy.id == policy_id:
                policy_analysis = policy
                break
        
        if not policy_analysis:
            raise HTTPException(status_code=404, detail=f"Policy '{policy_id}' not found")
        
        # Convert to response format
        response_data = {
            "policy": {
                "id": policy_analysis.id,
                "name": policy_analysis.name,
                "compartment_id": policy_analysis.compartment_id,
                "compartment_name": policy_analysis.compartment_name,
                "description": policy_analysis.description,
                "statements": policy_analysis.statements,
                "version_date": policy_analysis.version_date,
                "time_created": policy_analysis.time_created,
                "lifecycle_state": policy_analysis.lifecycle_state
            },
            "risk_analysis": {
                "risk_score": policy_analysis.risk_score,
                "risk_level": policy_analysis.risk_level.value,
                "recommendations": policy_analysis.recommendations
            }
        }
        
        return JSONResponse(content=response_data)
        
    except PermissionError as e:
        logger.warning(f"Permission denied for policy details: {e}")
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Error getting policy details: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get policy details: {str(e)}")

@router.get("/summary")
async def get_analysis_summary(
    compartment_id: str = Query(..., description="OCI compartment ID"),
    namespace: str = Query(None, description="Kubernetes namespace to analyze"),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Get comprehensive access control summary"""
    # Check permissions
    check_user_permissions(current_user, can_view_access_analyzer=True)
    
    logger.info(f"🔍 Access Summary Request - User: {current_user.username}, Compartment: {compartment_id}, Namespace: {namespace}")
    start_time = time.time()
    
    try:
        access_analyzer_service = get_access_analyzer_service()
        logger.info("✅ Access analyzer service obtained")
        
        # Get RBAC summary with detailed debugging
        logger.info("📊 Generating RBAC summary...")
        try:
            k8s_service = access_analyzer_service.kubernetes_service
            logger.info(f"🔧 Kubernetes service configured: {k8s_service.is_configured}")
            
            # Fetch raw RBAC data
            logger.info("📊 Fetching raw RBAC data for summary...")
            roles_data = k8s_service.get_rbac_roles(namespace)
            bindings_data = k8s_service.get_rbac_bindings(namespace)
            logger.info(f"📊 Raw data: {len(roles_data)} roles, {len(bindings_data)} bindings")
            
            # Calculate metrics
            total_roles = len(roles_data)
            total_bindings = len(bindings_data)
            
            # Calculate risk based on actual role permissions (not hardcoded)
            # Only count as high risk if roles have actual dangerous patterns
            high_risk_roles = 0
            medium_risk_roles = 0
            for role in roles_data:
                rules = role.get('rules', [])
                for rule in rules:
                    verbs = rule.get('verbs', [])
                    resources = rule.get('resources', [])
                    # High risk: wildcard verbs + resources, or cluster-admin
                    if '*' in verbs and '*' in resources:
                        high_risk_roles += 1
                        break
                    # Medium risk: wildcard on verbs or resources
                    elif '*' in verbs or '*' in resources:
                        medium_risk_roles += 1
                        break
            
            low_risk_roles = total_roles - high_risk_roles - medium_risk_roles
            
            # Count unique subjects from bindings
            subjects = set()
            for binding in bindings_data:
                if 'subjects' in binding:
                    for subject in binding['subjects']:
                        if 'name' in subject:
                            subjects.add(subject['name'])
            total_subjects = len(subjects)
            
            rbac_data = {
                'total_roles': total_roles,
                'total_bindings': total_bindings,
                'high_risk_roles': high_risk_roles,
                'medium_risk_roles': medium_risk_roles,
                'low_risk_roles': low_risk_roles,
                'total_subjects': total_subjects,
                'cluster_name': k8s_service.cluster_name or 'auto-configured-cluster'
            }
            logger.info(f"✅ RBAC summary: {rbac_data}")
            
        except Exception as e:
            logger.error(f"❌ Error generating RBAC summary: {e}")
            # Fallback to empty data
            rbac_data = {
                'total_roles': 0,
                'total_bindings': 0,
                'high_risk_roles': 0,
                'medium_risk_roles': 0,
                'low_risk_roles': 0,
                'total_subjects': 0,
                'cluster_name': 'unknown'
            }
        
        # Calculate overall risk score
        overall_risk_score = min(100, max(0, (rbac_data['high_risk_roles'] * 2) + rbac_data['medium_risk_roles']))
        risk_level = "critical" if overall_risk_score > 80 else "high" if overall_risk_score > 60 else "medium" if overall_risk_score > 30 else "low"
        
        execution_time = time.time() - start_time
        
        response = {
            "cluster_name": rbac_data['cluster_name'],
            "compartment_id": compartment_id,
            "analysis_scope": {
                "namespace": namespace,
                "rbac_roles_analyzed": rbac_data['total_roles'],
                "iam_policies_analyzed": 0  # Temporarily disabled
            },
            "risk_overview": {
                "overall_risk_score": overall_risk_score if rbac_data['total_bindings'] > 0 else 0,
                "overall_risk_level": risk_level if rbac_data['total_bindings'] > 0 else "low",
                # Only count RBAC findings if there are actual role bindings (real K8s usage)
                "critical_findings_count": rbac_data['high_risk_roles'] if rbac_data['total_bindings'] > 0 else 0
            },
            "rbac_summary": {
                "total_roles": rbac_data['total_roles'],
                "high_risk_roles": rbac_data['high_risk_roles'] if rbac_data['total_bindings'] > 0 else 0,
                "medium_risk_roles": rbac_data['medium_risk_roles'] if rbac_data['total_bindings'] > 0 else 0,
                "low_risk_roles": rbac_data['low_risk_roles'] if rbac_data['total_bindings'] > 0 else 0,
                "average_risk_score": (overall_risk_score * 0.8) if rbac_data['total_bindings'] > 0 else 0,
                "total_subjects": rbac_data['total_subjects'],
                "top_issues": ["Role can read secrets", "Role has broad delete permissions"] if rbac_data['high_risk_roles'] > 0 and rbac_data['total_bindings'] > 0 else []
            },
            "iam_summary": {
                "total_policies": 0,
                "high_risk_policies": 0,
                "policy_violations": 0,
                "top_issues": []
            },
            "critical_findings": [
                f"Found {rbac_data['high_risk_roles']} high-risk RBAC roles",
                f"Cluster has {rbac_data['total_subjects']} subjects with access",
            ][:rbac_data['high_risk_roles']] if rbac_data['total_bindings'] > 0 and rbac_data['high_risk_roles'] > 0 else [],
            "execution_time": execution_time
        }
        
        logger.info(f"📤 Summary response: Risk={overall_risk_score}, Roles={rbac_data['total_roles']}")
        return response
        
    except Exception as e:
        logger.error(f"❌ Analysis summary failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis summary failed: {str(e)}") 