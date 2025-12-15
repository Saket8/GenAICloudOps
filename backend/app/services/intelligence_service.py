"""
Intelligence Service - Multi-dimensional analytics for cloud resources.

Combines data from multiple OCI APIs to provide composite health scores
and insights not available in OCI Console.
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class HealthLevel(str, Enum):
    """Health level categories"""
    CRITICAL = "critical"
    WARNING = "warning"
    HEALTHY = "healthy"


@dataclass
class HealthIssue:
    """Single health issue affecting a resource"""
    category: str  # state, cost, backup, performance
    severity: str  # critical, warning, info
    message: str
    deduction: int  # points deducted
    recommendation: Optional[str] = None


@dataclass
class ResourceHealth:
    """Health assessment for a single resource"""
    resource_id: str
    resource_name: str
    resource_type: str
    compartment_id: str
    score: int  # 0-10
    level: HealthLevel
    issues: List[HealthIssue]
    lifecycle_state: str
    estimated_cost: float
    last_activity: Optional[datetime] = None
    days_stopped: int = 0  # How many days resource has been stopped
    time_created: Optional[datetime] = None


@dataclass
class HealthMatrix:
    """Complete health matrix for a compartment"""
    compartment_id: str
    timestamp: datetime
    total_resources: int
    healthy_count: int
    warning_count: int
    critical_count: int
    total_waste: float
    resources: List[ResourceHealth]
    by_type: Dict[str, List[ResourceHealth]]


class IntelligenceService:
    """
    Intelligence service for multi-dimensional resource analytics.
    
    Combines data from:
    - Core API (resource states)
    - Monitoring API (CPU, memory, disk)
    - Usage API (cost data)
    - Block Volume API (backup policies)
    - Audit API (activity tracking)
    """
    
    # Health scoring weights
    SCORING_RULES = {
        # Lifecycle state penalties
        'state_stopped': -2,
        'state_terminated': -5,
        'state_error': -4,
        
        # Inactivity penalties
        'inactive_30_days': -1,
        'inactive_90_days': -3,
        
        # Cost waste penalties
        'cost_waste_detected': -2,
        
        # Backup penalties
        'no_backup_policy': -2,
        
        # Performance penalties  
        'low_cpu_utilization': -1,  # <5% for 7 days
    }
    
    BASE_SCORE = 10
    MIN_SCORE = 0
    MAX_SCORE = 10
    
    # Shape to cost mapping (reused from CloudResourcesPage)
    SHAPE_COST_MAP = {
        'VM.Standard.E2.1.Micro': 0,
        'VM.Standard.E2.1': 8,
        'VM.Standard.E3.Flex': 15,
        'VM.Standard.E4.Flex': 20,
        'VM.Standard.E5.Flex': 22,
        'VM.Standard.A1.Flex': 10,
        'VM.Standard3.Flex': 25,
        'VM.Optimized3.Flex': 35,
        'VM.DenseIO.E4.Flex': 50,
        'default': 20,
    }
    
    DB_COST_MAP = {
        'ENTERPRISE_EDITION': 75,
        'STANDARD_EDITION': 45,
        'ENTERPRISE_EDITION_EXTREME_PERFORMANCE': 110,
        'default': 50,
    }
    
    def __init__(self, oci_service):
        """
        Initialize with existing OCI service for API calls.
        
        Args:
            oci_service: Instance of OCIService with authenticated clients
        """
        self.oci_service = oci_service
        self._cache: Dict[str, Any] = {}
        self._cache_ttl = timedelta(hours=1)
    
    def _get_cache_key(self, prefix: str, compartment_id: str) -> str:
        """Generate cache key"""
        return f"intelligence:{prefix}:{compartment_id}"
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid"""
        if cache_key not in self._cache:
            return False
        cached_time = self._cache.get(f"{cache_key}:timestamp")
        if not cached_time:
            return False
        return datetime.utcnow() - cached_time < self._cache_ttl
    
    def _get_estimated_cost(self, resource: Dict[str, Any], resource_type: str) -> float:
        """Calculate estimated monthly cost for a resource"""
        if resource_type == 'compute':
            shape = resource.get('shape', '')
            shape_base = shape.split('.')[0] + '.' + '.'.join(shape.split('.')[1:3]) if '.' in shape else shape
            base_cost = self.SHAPE_COST_MAP.get(shape_base, self.SHAPE_COST_MAP['default'])
            
            # Flex shapes: multiply by OCPU count
            if 'Flex' in shape:
                shape_config = resource.get('shape_config', {})
                ocpus = shape_config.get('ocpus', 1) if isinstance(shape_config, dict) else 1
                base_cost = base_cost * ocpus
            
            return base_cost
        
        elif resource_type == 'database':
            edition = resource.get('db_version', 'default')
            base_cost = self.DB_COST_MAP.get(edition, self.DB_COST_MAP['default'])
            cpu_count = resource.get('cpu_core_count', 1)
            return base_cost * cpu_count
        
        elif resource_type == 'block_volume':
            size_gb = resource.get('size_in_gbs', 50)
            return size_gb * 0.025  # ~$0.025/GB/month
        
        elif resource_type == 'load_balancer':
            return 25  # Base LB cost
        
        return 0
    
    def _calculate_health_score(
        self, 
        resource: Dict[str, Any], 
        resource_type: str
    ) -> ResourceHealth:
        """
        Calculate composite health score for a single resource.
        
        Combines multiple factors:
        - Lifecycle state
        - Activity recency
        - Cost efficiency
        - Backup status
        - Performance metrics
        
        Returns:
            ResourceHealth with score, level, and issues list
        """
        score = self.BASE_SCORE
        issues: List[HealthIssue] = []
        
        resource_id = resource.get('id', '')
        resource_name = resource.get('display_name', resource.get('name', 'Unknown'))
        lifecycle_state = resource.get('lifecycle_state', 'UNKNOWN').upper()
        compartment_id = resource.get('compartment_id', '')
        
        estimated_cost = self._get_estimated_cost(resource, resource_type)
        
        # ===== Parse time_created for resource age context =====
        time_created_raw = resource.get('time_created')
        time_created: Optional[datetime] = None
        days_stopped = 0  # Unknown - requires Audit API for real data
        
        if time_created_raw:
            try:
                if isinstance(time_created_raw, str):
                    # Handle ISO format strings
                    time_created = datetime.fromisoformat(time_created_raw.replace('Z', '+00:00'))
                elif isinstance(time_created_raw, datetime):
                    time_created = time_created_raw
            except Exception as e:
                logger.debug(f"Could not parse time_created: {e}")
        
        # NOTE: days_stopped remains 0 (unknown) because:
        # - Audit API has known issues and returns empty data
        # - Estimating from time_created is misleading (e.g., instances that
        #   stop on weekends and run on weekdays would show false high values)
        # - We only report what we KNOW: current lifecycle_state
        
        # ===== 1. Lifecycle State Check =====
        if lifecycle_state in ['STOPPED', 'INACTIVE']:
            score += self.SCORING_RULES['state_stopped']
            issues.append(HealthIssue(
                category='state',
                severity='warning',
                message=f'Resource is {lifecycle_state}',
                deduction=abs(self.SCORING_RULES['state_stopped']),
                recommendation='Start the resource or delete if no longer needed'
            ))
        
        elif lifecycle_state in ['TERMINATED', 'DELETED', 'FAILED']:
            score += self.SCORING_RULES['state_terminated']
            issues.append(HealthIssue(
                category='state',
                severity='critical',
                message=f'Resource is {lifecycle_state}',
                deduction=abs(self.SCORING_RULES['state_terminated']),
                recommendation='Remove from inventory or investigate failure'
            ))
        
        elif lifecycle_state in ['ERROR', 'FAULTY']:
            score += self.SCORING_RULES['state_error']
            issues.append(HealthIssue(
                category='state',
                severity='critical',
                message=f'Resource is in ERROR state',
                deduction=abs(self.SCORING_RULES['state_error']),
                recommendation='Investigate and remediate the error condition'
            ))
        
        # ===== 2. Inactivity Check (based on creation time as proxy) =====
        time_created = resource.get('time_created')
        if time_created and lifecycle_state in ['STOPPED', 'INACTIVE']:
            try:
                if isinstance(time_created, str):
                    created_dt = datetime.fromisoformat(time_created.replace('Z', '+00:00'))
                else:
                    created_dt = time_created
                
                days_since_created = (datetime.utcnow().replace(tzinfo=created_dt.tzinfo) - created_dt).days
                
                # If stopped and created > 90 days ago, likely inactive
                if days_since_created > 90:
                    score += self.SCORING_RULES['inactive_90_days']
                    issues.append(HealthIssue(
                        category='activity',
                        severity='critical',
                        message=f'Resource stopped/inactive for extended period',
                        deduction=abs(self.SCORING_RULES['inactive_90_days']),
                        recommendation='Consider deleting if no longer needed'
                    ))
                elif days_since_created > 30:
                    score += self.SCORING_RULES['inactive_30_days']
                    issues.append(HealthIssue(
                        category='activity',
                        severity='warning',
                        message=f'Resource stopped for over 30 days',
                        deduction=abs(self.SCORING_RULES['inactive_30_days']),
                        recommendation='Review if resource is still needed'
                    ))
            except Exception as e:
                logger.debug(f"Could not parse time_created: {e}")
        
        # ===== 3. Cost Waste Check =====
        if lifecycle_state in ['STOPPED', 'INACTIVE'] and estimated_cost > 0:
            # Check if there are attached resources still incurring cost
            if resource_type == 'compute':
                # Boot volume likely still attached
                score += self.SCORING_RULES['cost_waste_detected']
                issues.append(HealthIssue(
                    category='cost',
                    severity='warning',
                    message=f'Stopped resource with attached boot volume costing ~${estimated_cost * 0.2:.0f}/mo',
                    deduction=abs(self.SCORING_RULES['cost_waste_detected']),
                    recommendation='Delete boot volume if data is not needed'
                ))
        
        # ===== 4. Backup Policy Check =====
        # For block volumes, check if backup policy exists
        if resource_type == 'block_volume':
            backup_policy_id = resource.get('volume_backup_policy_id')
            if not backup_policy_id:
                score += self.SCORING_RULES['no_backup_policy']
                issues.append(HealthIssue(
                    category='backup',
                    severity='warning',
                    message='No backup policy attached to volume',
                    deduction=abs(self.SCORING_RULES['no_backup_policy']),
                    recommendation='Attach a backup policy for data protection'
                ))
        
        # ===== Clamp score to valid range =====
        score = max(self.MIN_SCORE, min(self.MAX_SCORE, score))
        
        # ===== Determine health level =====
        if score >= 8:
            level = HealthLevel.HEALTHY
        elif score >= 5:
            level = HealthLevel.WARNING
        else:
            level = HealthLevel.CRITICAL
        
        return ResourceHealth(
            resource_id=resource_id,
            resource_name=resource_name,
            resource_type=resource_type,
            compartment_id=compartment_id,
            score=score,
            level=level,
            issues=issues,
            lifecycle_state=lifecycle_state,
            estimated_cost=estimated_cost,
            days_stopped=days_stopped,
            time_created=time_created
        )
    
    async def get_health_matrix(self, compartment_id: str) -> HealthMatrix:
        """
        Get complete health matrix for all resources in a compartment.
        
        Combines resource data with health scoring to produce
        a heatmap-ready data structure.
        
        Args:
            compartment_id: OCI compartment OCID
            
        Returns:
            HealthMatrix with all resources and their health scores
        """
        cache_key = self._get_cache_key('health_matrix', compartment_id)
        
        # Check cache
        if self._is_cache_valid(cache_key):
            logger.info(f"Returning cached health matrix for {compartment_id[:20]}...")
            return self._cache[cache_key]
        
        logger.info(f"Computing health matrix for compartment {compartment_id[:20]}...")
        
        # Fetch all resources using existing OCI service
        result = await self.oci_service.get_all_resources(compartment_id)
        
        # Extract resources from nested structure
        # get_all_resources returns: { "resources": { "compute_instances": [...], ... }, ... }
        all_resources = result.get('resources', {})
        
        logger.info(f"📊 Retrieved {result.get('total_resources', 0)} total resources from API")
        
        resources: List[ResourceHealth] = []
        by_type: Dict[str, List[ResourceHealth]] = {}
        
        # Process each resource type
        type_mapping = {
            'compute_instances': 'compute',
            'databases': 'database',
            'block_volumes': 'block_volume',
            'load_balancers': 'load_balancer',
            'oke_clusters': 'cluster',
            'network_resources': 'network',
            'file_systems': 'storage',
            'object_storage_buckets': 'storage',
        }
        
        for api_type, resource_type in type_mapping.items():
            resource_list = all_resources.get(api_type, [])
            logger.debug(f"Processing {api_type}: {len(resource_list)} resources")
            
            for resource in resource_list:
                health = self._calculate_health_score(resource, resource_type)
                resources.append(health)
                
                # Group by type
                if resource_type not in by_type:
                    by_type[resource_type] = []
                by_type[resource_type].append(health)
        
        # ===== Audit API Enrichment for stopped duration =====
        # TEMPORARILY DISABLED: Audit API causing server instability
        # TODO: Re-enable after investigating OCI Audit API performance issues
        # The code has been kept but guard with False flag
        ENABLE_AUDIT_ENRICHMENT = False
        
        stopped_compute = [r for r in resources 
                          if r.lifecycle_state in ('STOPPED', 'INACTIVE') 
                          and r.resource_type == 'compute']
        
        if stopped_compute and ENABLE_AUDIT_ENRICHMENT:
            logger.info(f"🔍 Fetching Audit data for {len(stopped_compute)} stopped compute instances...")
            import asyncio
            
            async def enrich_stopped_duration(resource: ResourceHealth):
                try:
                    # 10 second timeout per instance
                    days = await asyncio.wait_for(
                        self.oci_service.calculate_instance_stopped_duration(
                            compartment_id=resource.compartment_id,
                            instance_id=resource.resource_id,
                            current_state=resource.lifecycle_state
                        ),
                        timeout=10.0
                    )
                    resource.days_stopped = days
                except asyncio.TimeoutError:
                    logger.warning(f"Audit API timeout for {resource.resource_name}, skipping")
                except Exception as e:
                    logger.debug(f"Could not get stopped duration for {resource.resource_id}: {e}")
            
            # Run enrichment with overall 30s timeout
            try:
                await asyncio.wait_for(
                    asyncio.gather(*[enrich_stopped_duration(r) for r in stopped_compute], return_exceptions=True),
                    timeout=30.0
                )
                
                # Log enrichment results
                enriched = sum(1 for r in stopped_compute if r.days_stopped > 0)
                logger.info(f"✅ Enriched {enriched}/{len(stopped_compute)} instances with real stopped duration")
            except asyncio.TimeoutError:
                logger.warning("⏱️ Audit enrichment timed out (30s), proceeding without full data")
        elif stopped_compute:
            logger.info(f"⏭️ Skipped Audit enrichment for {len(stopped_compute)} stopped instances (disabled)")
        
        # Calculate summary stats
        healthy_count = sum(1 for r in resources if r.level == HealthLevel.HEALTHY)
        warning_count = sum(1 for r in resources if r.level == HealthLevel.WARNING)
        critical_count = sum(1 for r in resources if r.level == HealthLevel.CRITICAL)
        
        # Calculate total waste
        total_waste = sum(
            r.estimated_cost * 0.2  # Assume 20% of cost is waste for stopped resources
            for r in resources 
            if r.lifecycle_state in ['STOPPED', 'INACTIVE']
        )
        
        matrix = HealthMatrix(
            compartment_id=compartment_id,
            timestamp=datetime.utcnow(),
            total_resources=len(resources),
            healthy_count=healthy_count,
            warning_count=warning_count,
            critical_count=critical_count,
            total_waste=total_waste,
            resources=resources,
            by_type=by_type
        )
        
        # Cache result
        self._cache[cache_key] = matrix
        self._cache[f"{cache_key}:timestamp"] = datetime.utcnow()
        
        logger.info(f"✅ Health matrix computed: {len(resources)} resources, "
                   f"{healthy_count} healthy, {warning_count} warning, {critical_count} critical")
        
        return matrix
    
    def get_resource_health_details(
        self, 
        resource_id: str, 
        compartment_id: str
    ) -> Optional[ResourceHealth]:
        """
        Get detailed health information for a specific resource.
        
        Used for drill-down view when user clicks a cell.
        
        Args:
            resource_id: OCI resource OCID
            compartment_id: OCI compartment OCID
            
        Returns:
            ResourceHealth with detailed issues and recommendations
        """
        cache_key = self._get_cache_key('health_matrix', compartment_id)
        
        if cache_key in self._cache:
            matrix: HealthMatrix = self._cache[cache_key]
            for resource in matrix.resources:
                if resource.resource_id == resource_id:
                    return resource
        
        return None
    
    def to_dict(self, health: ResourceHealth) -> Dict[str, Any]:
        """Convert ResourceHealth to dictionary for JSON serialization"""
        return {
            'resource_id': health.resource_id,
            'resource_name': health.resource_name,
            'resource_type': health.resource_type,
            'compartment_id': health.compartment_id,
            'score': health.score,
            'level': health.level.value,
            'lifecycle_state': health.lifecycle_state,
            'estimated_cost': health.estimated_cost,
            'days_stopped': health.days_stopped,
            'time_created': (
                health.time_created.isoformat() 
                if health.time_created and hasattr(health.time_created, 'isoformat') 
                else health.time_created
            ),
            'issues': [
                {
                    'category': issue.category,
                    'severity': issue.severity,
                    'message': issue.message,
                    'deduction': issue.deduction,
                    'recommendation': issue.recommendation
                }
                for issue in health.issues
            ]
        }
    
    def matrix_to_dict(self, matrix: HealthMatrix) -> Dict[str, Any]:
        """Convert HealthMatrix to dictionary for JSON serialization"""
        # Handle timestamp that may already be string from cache
        timestamp = matrix.timestamp
        if hasattr(timestamp, 'isoformat'):
            timestamp = timestamp.isoformat()
        
        return {
            'compartment_id': matrix.compartment_id,
            'timestamp': timestamp,
            'summary': {
                'total_resources': matrix.total_resources,
                'healthy_count': matrix.healthy_count,
                'warning_count': matrix.warning_count,
                'critical_count': matrix.critical_count,
                'total_waste': matrix.total_waste
            },
            'resources': [self.to_dict(r) for r in matrix.resources],
            'by_type': {
                rtype: [self.to_dict(r) for r in resources]
                for rtype, resources in matrix.by_type.items()
            }
        }

    async def generate_top_actions(self, compartment_id: str, limit: int = 5) -> Dict[str, Any]:
        """
        Generate prioritized list of top actions to optimize infrastructure.
        
        Analyzes health matrix and returns actionable recommendations
        sorted by potential $ savings.
        
        Args:
            compartment_id: OCI compartment OCID
            limit: Maximum number of actions to return
            
        Returns:
            Dictionary with prioritized actions and total potential savings
        """
        from datetime import datetime
        
        # Get fresh health matrix (includes Audit API enrichment for stopped duration)
        matrix = await self.get_health_matrix(compartment_id)
        
        actions = []
        
        # ===== 1. Stopped Resources =====
        # Now enriched with real Audit API data when available
        for resource in matrix.resources:
            if resource.lifecycle_state in ['STOPPED', 'INACTIVE']:
                monthly_cost = resource.estimated_cost
                days_stopped = resource.days_stopped  # Real data from Audit API
                
                # Build description based on whether we have real data
                if days_stopped > 0:
                    description = f'{resource.resource_name} stopped for {days_stopped} days'
                else:
                    description = f'{resource.resource_name} is currently {resource.lifecycle_state}'
                
                actions.append({
                    'id': f'stopped_{resource.resource_id}',
                    'category': 'review_stopped',
                    'icon': '⏸️',
                    'title': 'Review Stopped Resource',
                    'description': description,
                    'resource_id': resource.resource_id,
                    'resource_name': resource.resource_name,
                    'resource_type': resource.resource_type,
                    'days_stopped': days_stopped,
                    'potential_savings': monthly_cost * 0.8,  # 80% savings if deleted
                    'priority': 2,
                    'action_type': 'review',
                    'risk_level': 'low'
                })
            
            elif resource.lifecycle_state == 'UNAVAILABLE':
                # Resource in bad state - higher priority
                actions.append({
                    'id': f'unavailable_{resource.resource_id}',
                    'category': 'fix_unavailable',
                    'icon': '⚠️',
                    'title': 'Fix Unavailable Resource',
                    'description': f'{resource.resource_name} is UNAVAILABLE - investigate',
                    'resource_id': resource.resource_id,
                    'resource_name': resource.resource_name,
                    'resource_type': resource.resource_type,
                    'days_stopped': 0,
                    'potential_savings': resource.estimated_cost,
                    'priority': 1,
                    'action_type': 'investigate',
                    'risk_level': 'high'
                })
        
        # ===== 2. Resources Without Backup Policy =====
        for resource in matrix.resources:
            no_backup = any(issue.message and 'backup' in issue.message.lower() for issue in resource.issues)
            if no_backup:
                actions.append({
                    'id': f'backup_{resource.resource_id}',
                    'category': 'fix_security',
                    'icon': '🔒',
                    'title': 'Attach Backup Policy',
                    'description': f'{resource.resource_name} has no backup policy',
                    'resource_id': resource.resource_id,
                    'resource_name': resource.resource_name,
                    'resource_type': resource.resource_type,
                    'potential_savings': 0,  # No direct savings, but risk reduction
                    'priority': 3,
                    'action_type': 'configure',
                    'risk_level': 'high'  # High risk if data lost
                })
        
        # ===== 3. Critical Health Score Resources =====
        for resource in matrix.resources:
            if resource.score <= 3 and resource.lifecycle_state == 'RUNNING':
                # Running but unhealthy - potential optimization target
                actions.append({
                    'id': f'optimize_{resource.resource_id}',
                    'category': 'optimize',
                    'icon': '⚡',
                    'title': 'Optimize Unhealthy Resource',
                    'description': f'{resource.resource_name} has health score {resource.score}/10',
                    'resource_id': resource.resource_id,
                    'resource_name': resource.resource_name,
                    'resource_type': resource.resource_type,
                    'potential_savings': resource.estimated_cost * 0.3,  # Estimate 30% savings
                    'priority': 2,
                    'action_type': 'optimize',
                    'risk_level': 'low'
                })
        
        # ===== Sort by priority and savings =====
        actions.sort(key=lambda x: (-x['priority'], -x['potential_savings']))
        
        # Calculate total potential savings
        total_savings = sum(a['potential_savings'] for a in actions)
        
        # Group by category for summary
        categories = {}
        for action in actions:
            cat = action['category']
            if cat not in categories:
                categories[cat] = {'count': 0, 'savings': 0}
            categories[cat]['count'] += 1
            categories[cat]['savings'] += action['potential_savings']
        
        return {
            'actions': actions[:limit],
            'total_actions': len(actions),
            'total_potential_savings': total_savings,
            'categories': categories,
            'generated_at': datetime.utcnow().isoformat()
        }


# Singleton instance (lazy initialization)
_intelligence_service: Optional[IntelligenceService] = None


def get_intelligence_service() -> IntelligenceService:
    """Get or create intelligence service instance"""
    global _intelligence_service
    
    if _intelligence_service is None:
        from app.services.cloud_service import get_oci_service
        oci_service = get_oci_service()
        _intelligence_service = IntelligenceService(oci_service)
    
    return _intelligence_service
