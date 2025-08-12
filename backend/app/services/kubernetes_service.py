import asyncio
import logging
import os
import tempfile
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import yaml
import json

# Kubernetes client imports
from kubernetes import client, config, watch
from kubernetes.client import ApiException
from kubernetes.config import ConfigException

# Core app imports
from app.core.config import settings
from app.core.exceptions import BaseCustomException, ExternalServiceError
import redis

logger = logging.getLogger(__name__)

class ClusterConnectionError(BaseCustomException):
    """Custom exception for cluster connection issues"""
    pass

class PodStatus(Enum):
    """Pod status enumeration"""
    PENDING = "Pending"
    RUNNING = "Running" 
    SUCCEEDED = "Succeeded"
    FAILED = "Failed"
    UNKNOWN = "Unknown"
    CRASHLOOPBACKOFF = "CrashLoopBackOff"
    IMAGEPULLBACKOFF = "ImagePullBackOff"
    EVICTED = "Evicted"

@dataclass
class ClusterInfo:
    """Cluster information data class"""
    name: str
    server: str
    version: str
    namespace_count: int
    pod_count: int
    node_count: int
    healthy: bool

@dataclass 
class PodInfo:
    """Pod information data class"""
    name: str
    namespace: str
    status: str
    restart_count: int
    node_name: str
    created_time: datetime
    containers: List[Dict[str, Any]]
    labels: Dict[str, str]
    owner_references: List[Dict[str, Any]]

@dataclass
class RBACRole:
    """RBAC Role information"""
    name: str
    namespace: Optional[str]
    kind: str  # Role or ClusterRole
    rules: List[Dict[str, Any]]
    created_time: datetime
    labels: Dict[str, str]

@dataclass
class RBACBinding:
    """RBAC RoleBinding information"""
    name: str
    namespace: Optional[str]
    kind: str  # RoleBinding or ClusterRoleBinding
    role_ref: Dict[str, str]
    subjects: List[Dict[str, Any]]
    created_time: datetime

class KubernetesService:
    """
    Comprehensive Kubernetes service for real cluster integration
    Supports RBAC analysis, pod monitoring, and log extraction
    """
    
    def __init__(self):
        from app.core.config import settings
        self.clients = {}  # Multiple cluster support
        self.redis_client = None
        self.current_cluster = None
        self.kubeconfig_path = None
        self._use_dummy = getattr(settings, 'USE_DUMMY_KUBERNETES', True)  # Default to True for demo
        self._setup_redis()
        
    def _setup_redis(self):
        """Setup Redis caching if available"""
        if settings.REDIS_ENABLED:
            try:
                self.redis_client = redis.Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    db=settings.REDIS_DB,
                    decode_responses=True,
                    socket_connect_timeout=2,
                    socket_timeout=2
                )
                self.redis_client.ping()
                logger.info("Kubernetes service initialized with Redis caching")
            except Exception as e:
                logger.info(f"Redis not available for Kubernetes service: {e}")
                self.redis_client = None

    async def configure_cluster(self, kubeconfig_content: str, cluster_name: str = "default") -> bool:
        """
        Configure cluster connection with real kubeconfig content
        
        Args:
            kubeconfig_content: The actual kubeconfig file content
            cluster_name: Name to identify this cluster
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # If dummy mode, short-circuit and do not touch kubeconfig
            if getattr(self, '_use_dummy', False):
                self.clients[cluster_name] = {
                    'core_v1': None,
                    'apps_v1': None,
                    'rbac_v1': None,
                    'version': None,
                    'metrics': None,
                    'custom_objects': None
                }
                self.current_cluster = cluster_name
                logger.info("USE_DUMMY_KUBERNETES is True - configured dummy cluster without kubeconfig")
                return True

            # Create temporary kubeconfig file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
                f.write(kubeconfig_content)
                self.kubeconfig_path = f.name
            
            # Load kubeconfig
            config.load_kube_config(config_file=self.kubeconfig_path)
            
            # Create clients
            self.clients[cluster_name] = {
                'core_v1': client.CoreV1Api(),
                'apps_v1': client.AppsV1Api(),
                'rbac_v1': client.RbacAuthorizationV1Api(),
                'version': client.VersionApi(),
                'metrics': None,  # Will be set up later if metrics server available
                'custom_objects': client.CustomObjectsApi()
            }
            
            self.current_cluster = cluster_name
            
            # Test connection
            cluster_info = await self.get_cluster_info(cluster_name)
            logger.info(f"Successfully connected to cluster: {cluster_info.name}")
            
            return True
            
        except ConfigException as e:
            logger.error(f"Invalid kubeconfig: {e}")
            raise ClusterConnectionError(f"Invalid kubeconfig: {str(e)}")
        except ApiException as e:
            logger.error(f"Kubernetes API error: {e}")
            raise ClusterConnectionError(f"API error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error connecting to cluster: {e}")
            raise ClusterConnectionError(f"Connection error: {str(e)}")
        finally:
            # Clean up temporary file
            if self.kubeconfig_path and os.path.exists(self.kubeconfig_path):
                try:
                    os.unlink(self.kubeconfig_path)
                except Exception as e:
                    logger.warning(f"Could not clean up temp kubeconfig: {e}")

    async def get_cluster_info(self, cluster_name: str = None) -> ClusterInfo:
        """Get basic cluster information"""
        cluster_name = cluster_name or self.current_cluster
        if not cluster_name or cluster_name not in self.clients:
            raise ClusterConnectionError("No cluster configured")
        
        try:
            # If dummy mode, return mocked cluster info
            if getattr(self, '_use_dummy', False):
                return ClusterInfo(
                    name=cluster_name,
                    server="Dummy",
                    version="1.27",
                    namespace_count=4,
                    pod_count=42,
                    node_count=3,
                    healthy=True
                )

            core_v1 = self.clients[cluster_name]['core_v1']
            version_api = self.clients[cluster_name]['version']
            
            # Get cluster version
            try:
                version_info = version_api.get_code()
                version_str = f"{version_info.major}.{version_info.minor}"
            except Exception as e:
                logger.warning(f"Could not get cluster version: {e}")
                version_str = "Unknown"
            
            # Get namespaces
            namespaces = core_v1.list_namespace()
            namespace_count = len(namespaces.items)
            
            # Get pods
            pods = core_v1.list_pod_for_all_namespaces()
            pod_count = len(pods.items)
            
            # Get nodes
            nodes = core_v1.list_node()
            node_count = len(nodes.items)
            
            return ClusterInfo(
                name=cluster_name,
                server="Connected",
                version=version_str,
                namespace_count=namespace_count,
                pod_count=pod_count,
                node_count=node_count,
                healthy=True
            )
            
        except ApiException as e:
            logger.error(f"Error getting cluster info: {e}")
            raise ClusterConnectionError(f"Failed to get cluster info: {str(e)}")

    async def get_namespaces(self, cluster_name: str = None) -> List[Dict[str, Any]]:
        """Get all namespaces in the cluster"""
        cluster_name = cluster_name or self.current_cluster
        if not cluster_name or cluster_name not in self.clients:
            raise ClusterConnectionError("No cluster configured")
        
        cache_key = f"k8s:namespaces:{cluster_name}"
        
        # Check cache
        if self.redis_client:
            try:
                cached = self.redis_client.get(cache_key)
                if cached:
                    return json.loads(cached)
            except Exception as e:
                logger.debug(f"Cache error: {e}")
        
        try:
            # Dummy mode returns mock namespaces
            if getattr(self, '_use_dummy', False):
                result = [
                    {'name': 'default', 'status': 'Active', 'created_time': datetime.utcnow().isoformat(), 'labels': {}, 'annotations': {}},
                    {'name': 'kube-system', 'status': 'Active', 'created_time': datetime.utcnow().isoformat(), 'labels': {}, 'annotations': {}},
                    {'name': 'production', 'status': 'Active', 'created_time': datetime.utcnow().isoformat(), 'labels': {'environment': 'production'}, 'annotations': {}},
                    {'name': 'staging', 'status': 'Active', 'created_time': datetime.utcnow().isoformat(), 'labels': {'environment': 'staging'}, 'annotations': {}}
                ]
            else:
                core_v1 = self.clients[cluster_name]['core_v1']
                namespaces = core_v1.list_namespace()
                
                result = []
                for ns in namespaces.items:
                    result.append({
                        'name': ns.metadata.name,
                        'status': ns.status.phase,
                        'created_time': ns.metadata.creation_timestamp.isoformat(),
                        'labels': ns.metadata.labels or {},
                        'annotations': ns.metadata.annotations or {}
                    })
            
            # Cache for 5 minutes
            if self.redis_client:
                try:
                    self.redis_client.setex(cache_key, 300, json.dumps(result, default=str))
                except Exception as e:
                    logger.debug(f"Cache write error: {e}")
            
            return result
            
        except ApiException as e:
            logger.error(f"Error getting namespaces: {e}")
            raise ClusterConnectionError(f"Failed to get namespaces: {str(e)}")

    async def get_pods(self, namespace: str = None, cluster_name: str = None) -> List[PodInfo]:
        """Get pods in specified namespace or all namespaces"""
        
        # Return dummy data immediately if using dummy mode or no cluster configured
        if getattr(self, '_use_dummy', True) or not self.current_cluster:
            now = datetime.utcnow()
            return [
                PodInfo(
                    name='web-server-xyz', namespace=namespace or 'production', status='Running',
                    restart_count=0, node_name='worker-node-1', created_time=now,
                    containers=[{'name': 'web', 'ready': True, 'restart_count': 0, 'image': 'nginx:1.21', 'state': 'Running'}],
                    labels={'app': 'web'}, owner_references=[]
                ),
                PodInfo(
                    name='db-pod-abc', namespace=namespace or 'production', status='CrashLoopBackOff',
                    restart_count=12, node_name='worker-node-2', created_time=now,
                    containers=[{'name': 'db', 'ready': False, 'restart_count': 12, 'image': 'postgres:13', 'state': 'Waiting: CrashLoopBackOff'}],
                    labels={'app': 'db'}, owner_references=[]
                ),
                PodInfo(
                    name='api-service-def', namespace=namespace or 'production', status='Running',
                    restart_count=1, node_name='worker-node-1', created_time=now,
                    containers=[{'name': 'api', 'ready': True, 'restart_count': 1, 'image': 'app:latest', 'state': 'Running'}],
                    labels={'app': 'api'}, owner_references=[]
                )
            ]
        
        cluster_name = cluster_name or self.current_cluster
        if not cluster_name or cluster_name not in self.clients:
            raise ClusterConnectionError("No cluster configured")
        
        cache_key = f"k8s:pods:{cluster_name}:{namespace or 'all'}"
        
        try:
            core_v1 = self.clients[cluster_name]['core_v1']
            
            if namespace:
                pods = core_v1.list_namespaced_pod(namespace=namespace)
            else:
                pods = core_v1.list_pod_for_all_namespaces()
            
            result = []
            for pod in pods.items:
                # Calculate restart count
                restart_count = sum(
                    container.restart_count or 0 
                    for container in (pod.status.container_statuses or [])
                )
                
                # Get container info
                containers = []
                for container in (pod.status.container_statuses or []):
                    containers.append({
                        'name': container.name,
                        'ready': container.ready,
                        'restart_count': container.restart_count or 0,
                        'image': container.image,
                        'state': self._get_container_state(container.state)
                    })
                
                pod_info = PodInfo(
                    name=pod.metadata.name,
                    namespace=pod.metadata.namespace,
                    status=pod.status.phase,
                    restart_count=restart_count,
                    node_name=pod.spec.node_name or "Unknown",
                    created_time=pod.metadata.creation_timestamp,
                    containers=containers,
                    labels=pod.metadata.labels or {},
                    owner_references=pod.metadata.owner_references or []
                )
                result.append(pod_info)
            
            return result
            
        except ApiException as e:
            logger.error(f"Error getting pods: {e}")
            raise ClusterConnectionError(f"Failed to get pods: {str(e)}")

    def _get_container_state(self, state) -> str:
        """Extract container state from Kubernetes container state object"""
        if state.running:
            return "Running"
        elif state.waiting:
            return f"Waiting: {state.waiting.reason}"
        elif state.terminated:
            return f"Terminated: {state.terminated.reason}"
        else:
            return "Unknown"

    async def get_pod_logs(self, pod_name: str, namespace: str, 
                          container: str = None, lines: int = 100,
                          cluster_name: str = None) -> str:
        """Get logs for a specific pod"""
        cluster_name = cluster_name or self.current_cluster
        if not cluster_name or cluster_name not in self.clients:
            raise ClusterConnectionError("No cluster configured")
        
        try:
            if getattr(self, '_use_dummy', False):
                return f"{datetime.utcnow().isoformat()} [INFO] Dummy logs for pod {pod_name} in {namespace}...\n{datetime.utcnow().isoformat()} [ERROR] Simulated error line"

            core_v1 = self.clients[cluster_name]['core_v1']
            
            logs = core_v1.read_namespaced_pod_log(
                name=pod_name,
                namespace=namespace,
                container=container,
                tail_lines=lines,
                timestamps=True
            )
            
            return logs
            
        except ApiException as e:
            logger.error(f"Error getting pod logs: {e}")
            if e.status == 404:
                return f"Pod {pod_name} not found in namespace {namespace}"
            else:
                raise ClusterConnectionError(f"Failed to get pod logs: {str(e)}")

    async def get_rbac_roles(self, namespace: str = None, cluster_name: str = None) -> List[RBACRole]:
        """Get RBAC roles (both Role and ClusterRole)"""
        cluster_name = cluster_name or self.current_cluster
        if not cluster_name or cluster_name not in self.clients:
            raise ClusterConnectionError("No cluster configured")
        
        try:
            if getattr(self, '_use_dummy', False):
                result = [
                    RBACRole(name='cluster-admin', namespace=None, kind='ClusterRole', rules=[{"verbs": ["*"], "resources": ["*"]}], created_time=datetime.utcnow(), labels={}),
                    RBACRole(name='edit', namespace=None, kind='ClusterRole', rules=[{"verbs": ["get","list","create","update","patch","delete"], "resources": ["pods","services"]}], created_time=datetime.utcnow(), labels={}),
                    RBACRole(name='view', namespace=None, kind='ClusterRole', rules=[{"verbs": ["get","list","watch"], "resources": ["pods","services"]}], created_time=datetime.utcnow(), labels={})
                ]
                return result

            rbac_v1 = self.clients[cluster_name]['rbac_v1']
            result = []
            
            # Get ClusterRoles
            cluster_roles = rbac_v1.list_cluster_role()
            for role in cluster_roles.items:
                rbac_role = RBACRole(
                    name=role.metadata.name,
                    namespace=None,  # ClusterRoles don't have namespace
                    kind="ClusterRole",
                    rules=[rule.to_dict() for rule in (role.rules or [])],
                    created_time=role.metadata.creation_timestamp,
                    labels=role.metadata.labels or {}
                )
                result.append(rbac_role)
            
            # Get namespaced Roles
            if namespace:
                roles = rbac_v1.list_namespaced_role(namespace=namespace)
            else:
                roles = rbac_v1.list_role_for_all_namespaces()
            
            for role in roles.items:
                rbac_role = RBACRole(
                    name=role.metadata.name,
                    namespace=role.metadata.namespace,
                    kind="Role",
                    rules=[rule.to_dict() for rule in (role.rules or [])],
                    created_time=role.metadata.creation_timestamp,
                    labels=role.metadata.labels or {}
                )
                result.append(rbac_role)
            
            return result
            
        except ApiException as e:
            logger.error(f"Error getting RBAC roles: {e}")
            raise ClusterConnectionError(f"Failed to get RBAC roles: {str(e)}")

    async def get_rbac_bindings(self, namespace: str = None, cluster_name: str = None) -> List[RBACBinding]:
        """Get RBAC role bindings (both RoleBinding and ClusterRoleBinding)"""
        cluster_name = cluster_name or self.current_cluster
        if not cluster_name or cluster_name not in self.clients:
            raise ClusterConnectionError("No cluster configured")
        
        try:
            if getattr(self, '_use_dummy', False):
                result = [
                    RBACBinding(name='cluster-admin-binding', namespace=None, kind='ClusterRoleBinding', role_ref={'name': 'cluster-admin', 'kind': 'ClusterRole'}, subjects=[{"kind": "User", "name": "admin"}], created_time=datetime.utcnow()),
                    RBACBinding(name='developer-binding', namespace='default', kind='RoleBinding', role_ref={'name': 'edit', 'kind': 'ClusterRole'}, subjects=[{"kind": "User", "name": "developer"}], created_time=datetime.utcnow())
                ]
                return result

            rbac_v1 = self.clients[cluster_name]['rbac_v1']
            result = []
            
            # Get ClusterRoleBindings
            cluster_bindings = rbac_v1.list_cluster_role_binding()
            for binding in cluster_bindings.items:
                rbac_binding = RBACBinding(
                    name=binding.metadata.name,
                    namespace=None,  # ClusterRoleBindings don't have namespace
                    kind="ClusterRoleBinding",
                    role_ref=binding.role_ref.to_dict(),
                    subjects=[subject.to_dict() for subject in (binding.subjects or [])],
                    created_time=binding.metadata.creation_timestamp
                )
                result.append(rbac_binding)
            
            # Get namespaced RoleBindings
            if namespace:
                bindings = rbac_v1.list_namespaced_role_binding(namespace=namespace)
            else:
                bindings = rbac_v1.list_role_binding_for_all_namespaces()
            
            for binding in bindings.items:
                rbac_binding = RBACBinding(
                    name=binding.metadata.name,
                    namespace=binding.metadata.namespace,
                    kind="RoleBinding",
                    role_ref=binding.role_ref.to_dict(),
                    subjects=[subject.to_dict() for subject in (binding.subjects or [])],
                    created_time=binding.metadata.creation_timestamp
                )
                result.append(rbac_binding)
            
            return result
            
        except ApiException as e:
            logger.error(f"Error getting RBAC bindings: {e}")
            raise ClusterConnectionError(f"Failed to get RBAC bindings: {str(e)}")

    async def health_check(self, cluster_name: str = None) -> Dict[str, Any]:
        """Health check for Kubernetes service"""
        try:
            if not self.current_cluster:
                return {
                    "status": "unhealthy",
                    "message": "No cluster configured",
                    "clusters_configured": 0
                }
            
            cluster_info = await self.get_cluster_info(cluster_name)
            
            return {
                "status": "healthy",
                "service": "Kubernetes",
                "cluster_name": cluster_info.name,
                "cluster_version": cluster_info.version,
                "namespaces": cluster_info.namespace_count,
                "pods": cluster_info.pod_count,
                "nodes": cluster_info.node_count,
                "clusters_configured": len(self.clients)
            }
            
        except Exception as e:
            logger.error(f"Kubernetes health check failed: {e}")
            return {
                "status": "unhealthy", 
                "message": str(e),
                "clusters_configured": len(self.clients)
            }

    def cleanup(self):
        """Cleanup resources"""
        if self.kubeconfig_path and os.path.exists(self.kubeconfig_path):
            try:
                os.unlink(self.kubeconfig_path)
            except Exception as e:
                logger.warning(f"Could not clean up kubeconfig file: {e}")
    
    def reset_all_clusters(self):
        """Reset all cluster configurations and clear cached clients"""
        self.clients.clear()
        self.current_cluster = None
        self.kubeconfig_path = None
        logger.info("All cluster configurations have been reset")

# Global service instance - lazy loading
_kubernetes_service = None

def get_kubernetes_service() -> KubernetesService:
    """Get kubernetes service instance with lazy loading"""
    global _kubernetes_service
    if _kubernetes_service is None:
        _kubernetes_service = KubernetesService()
    return _kubernetes_service

# Access via function call only - don't instantiate at module level 