"""
Working Kubernetes service implementation
Uses the proven manual approach that we know works
"""

import os
import tempfile
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
# Kubernetes imports moved to lazy loading to avoid 66-second delay on Windows

logger = logging.getLogger(__name__)

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
    node_name: Optional[str]
    restart_count: int
    age: str
    ready: str

@dataclass
class RBACRole:
    """RBAC Role data class"""
    name: str
    namespace: Optional[str]
    kind: str
    rules: List[Dict[str, Any]]
    created_time: str
    labels: Dict[str, str]

@dataclass
class RBACBinding:
    """RBAC Binding data class"""
    name: str
    namespace: Optional[str]
    kind: str
    role_ref: Dict[str, str]
    subjects: List[Dict[str, Any]]
    created_time: str

class WorkingKubernetesService:
    """Working Kubernetes service using the proven approach"""
    
    def __init__(self):
        self.is_configured = False
        self.cluster_name = None
        self.temp_kubeconfig_path = None
        self._auto_configured = False  # Track if we tried auto-config
        # SAFE MODE: Skip all real Kubernetes calls for debugging
        self.safe_mode = False  # Set to True to bypass all blocking calls
        # Don't auto-configure during init to avoid blocking
    
    def _ensure_configured(self):
        """Ensure service is configured, auto-configure if needed"""
        if self.safe_mode:
            # In safe mode, mark as configured without real setup
            self.is_configured = True
            self.cluster_name = "safe-mode-cluster"
            return
            
        if not self.is_configured and not self._auto_configured:
            self._auto_configured = True
            self._auto_configure()
    
    def _auto_configure(self):
        """Automatically configure using default kubeconfig if available"""
        try:
            # Lazy import to avoid blocking at module level
            from kubernetes import config
            
            # Try loading from default location first
            config.load_kube_config()
            
            # Mark as configured without testing connection (to avoid blocking)
            # Connection will be tested when actually making API calls
            self.is_configured = True
            self.cluster_name = "auto-configured-cluster"
            
            logger.info("Auto-configured Kubernetes cluster (connection will be tested on first API call)")
            
        except Exception as e:
            logger.warning(f"Auto-configuration failed, manual configuration required: {e}")
            # Don't log as error since this is expected in some environments
    
    def configure_cluster(self, kubeconfig_content: str, cluster_name: str = "default") -> bool:
        """Configure cluster using the working approach"""
        try:
            # Create temporary kubeconfig file (the approach we proved works)
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
                f.write(kubeconfig_content)
                self.temp_kubeconfig_path = f.name
            
            # Load kubeconfig (this worked in our test)
            config.load_kube_config(config_file=self.temp_kubeconfig_path)
            
            # Test connection with a simple API call
            core_v1 = client.CoreV1Api()
            nodes = core_v1.list_node(timeout_seconds=10)
            
            self.is_configured = True
            self.cluster_name = cluster_name
            
            logger.info(f"Successfully configured cluster '{cluster_name}' with {len(nodes.items)} nodes")
            return True
            
        except Exception as e:
            logger.error(f"Failed to configure cluster: {e}")
            self._cleanup_temp_file()
            return False
    
    def get_cluster_info(self) -> ClusterInfo:
        """Get cluster information using the working approach"""
        if not self.is_configured:
            raise Exception("Cluster not configured")
        
        try:
            # Create API clients (the way that works)
            core_v1 = client.CoreV1Api()
            version_api = client.VersionApi()
            
            # Get version using the correct API (this is the fix!)
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
                name=self.cluster_name,
                server="Connected",
                version=version_str,
                namespace_count=namespace_count,
                pod_count=pod_count,
                node_count=node_count,
                healthy=True
            )
            
        except Exception as e:
            logger.error(f"Failed to get cluster info: {e}")
            raise Exception(f"Failed to get cluster info: {str(e)}")
    
    def get_namespaces(self) -> List[Dict[str, Any]]:
        """Get all namespaces"""
        if not self.is_configured:
            raise Exception("Cluster not configured")
        
        try:
            core_v1 = client.CoreV1Api()
            namespaces = core_v1.list_namespace()
            
            result = []
            for ns in namespaces.items:
                result.append({
                    "name": ns.metadata.name,
                    "status": ns.status.phase,
                    "age": ns.metadata.creation_timestamp.isoformat() if ns.metadata.creation_timestamp else "Unknown",
                    "labels": ns.metadata.labels or {}
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get namespaces: {e}")
            raise Exception(f"Failed to get namespaces: {str(e)}")
    
    def get_pods(self, namespace: str = None) -> List[PodInfo]:
        """Get pods from cluster"""
        if not self.is_configured:
            raise Exception("Cluster not configured")
        
        try:
            core_v1 = client.CoreV1Api()
            
            if namespace:
                pods = core_v1.list_namespaced_pod(namespace)
            else:
                pods = core_v1.list_pod_for_all_namespaces()
            
            result = []
            for pod in pods.items:
                # Calculate age
                if pod.metadata.creation_timestamp:
                    from datetime import datetime, timezone
                    now = datetime.now(timezone.utc)
                    age_delta = now - pod.metadata.creation_timestamp
                    age = f"{age_delta.days}d" if age_delta.days > 0 else f"{age_delta.seconds//3600}h"
                else:
                    age = "Unknown"
                
                # Get ready status
                ready_containers = 0
                total_containers = len(pod.spec.containers) if pod.spec.containers else 0
                if pod.status.container_statuses:
                    for container in pod.status.container_statuses:
                        if container.ready:
                            ready_containers += 1
                
                ready = f"{ready_containers}/{total_containers}"
                
                # Get restart count
                restart_count = 0
                if pod.status.container_statuses:
                    restart_count = sum(c.restart_count for c in pod.status.container_statuses)
                
                pod_info = PodInfo(
                    name=pod.metadata.name,
                    namespace=pod.metadata.namespace,
                    status=pod.status.phase,
                    node_name=pod.spec.node_name,
                    restart_count=restart_count,
                    age=age,
                    ready=ready
                )
                result.append(pod_info)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get pods: {e}")
            raise Exception(f"Failed to get pods: {str(e)}")
    
    def get_pod_logs(self, pod_name: str, namespace: str, container: str = None, lines: int = 100) -> str:
        """Get logs from a specific pod"""
        if not self.is_configured:
            raise Exception("Cluster not configured")
        
        try:
            core_v1 = client.CoreV1Api()
            
            logs = core_v1.read_namespaced_pod_log(
                name=pod_name,
                namespace=namespace,
                container=container,
                tail_lines=lines
            )
            
            return logs
            
        except Exception as e:
            logger.error(f"Failed to get pod logs: {e}")
            raise Exception(f"Failed to get pod logs: {str(e)}")
    
    def get_rbac_roles(self, namespace: str = None) -> List[RBACRole]:
        """Get RBAC roles"""
        # SAFE MODE: Return mock data to test non-blocking
        if self.safe_mode:
            logger.info("🔧 SAFE MODE: Returning mock RBAC roles data")
            return [
                {
                    "name": "cluster-admin",
                    "namespace": None,
                    "kind": "ClusterRole",
                    "rules": [{"verbs": ["*"], "resources": ["*"]}],
                    "created_time": "2024-01-01T00:00:00Z",
                    "labels": {}
                },
                {
                    "name": "edit",
                    "namespace": None,
                    "kind": "ClusterRole", 
                    "rules": [{"verbs": ["get", "list", "create", "update", "patch", "delete"], "resources": ["*"]}],
                    "created_time": "2024-01-01T00:00:00Z",
                    "labels": {}
                },
                {
                    "name": "view",
                    "namespace": None,
                    "kind": "ClusterRole",
                    "rules": [{"verbs": ["get", "list", "watch"], "resources": ["*"]}],
                    "created_time": "2024-01-01T00:00:00Z",
                    "labels": {}
                }
            ]
        
        self._ensure_configured()  # Lazy auto-configure
        if not self.is_configured:
            raise Exception("Cluster not configured")
        
        try:
            rbac_v1 = client.RbacAuthorizationV1Api()
            result = []
            
            if namespace:
                # Get namespaced roles with timeout
                roles = rbac_v1.list_namespaced_role(namespace, timeout_seconds=5)
                for role in roles.items:
                    rbac_role = RBACRole(
                        name=role.metadata.name,
                        namespace=role.metadata.namespace,
                        kind="Role",
                        rules=[rule.to_dict() for rule in (role.rules or [])] if hasattr(role, 'rules') and role.rules is not None else [],
                        created_time=role.metadata.creation_timestamp.isoformat() if role.metadata.creation_timestamp else "Unknown",
                        labels=role.metadata.labels or {}
                    )
                    result.append(rbac_role)
            else:
                # Get cluster roles with timeout
                cluster_roles = rbac_v1.list_cluster_role(timeout_seconds=5)
                for role in cluster_roles.items:
                    rbac_role = RBACRole(
                        name=role.metadata.name,
                        namespace=None,
                        kind="ClusterRole",
                        rules=[rule.to_dict() for rule in (role.rules or [])] if hasattr(role, 'rules') and role.rules is not None else [],
                        created_time=role.metadata.creation_timestamp.isoformat() if role.metadata.creation_timestamp else "Unknown",
                        labels=role.metadata.labels or {}
                    )
                    result.append(rbac_role)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get RBAC roles: {e}")
            raise Exception(f"Failed to get RBAC roles: {str(e)}")
    
    def get_rbac_bindings(self, namespace: str = None) -> List[RBACBinding]:
        """Get RBAC bindings"""
        # SAFE MODE: Return mock data to test non-blocking
        if self.safe_mode:
            logger.info("🔧 SAFE MODE: Returning mock RBAC bindings data")
            return [
                {
                    "name": "cluster-admin-binding",
                    "namespace": None,
                    "role_ref": {"name": "cluster-admin", "kind": "ClusterRole"},
                    "subjects": [{"kind": "User", "name": "admin"}]
                },
                {
                    "name": "system-default",
                    "namespace": None,
                    "role_ref": {"name": "edit", "kind": "ClusterRole"},
                    "subjects": [{"kind": "ServiceAccount", "name": "default", "namespace": "kube-system"}]
                }
            ]
        
        self._ensure_configured()  # Lazy auto-configure
        if not self.is_configured:
            raise Exception("Cluster not configured")
        
        try:
            rbac_v1 = client.RbacAuthorizationV1Api()
            result = []
            
            if namespace:
                # Get namespaced role bindings
                bindings = rbac_v1.list_namespaced_role_binding(namespace, timeout_seconds=5)
                for binding in bindings.items:
                    rbac_binding = RBACBinding(
                        name=binding.metadata.name,
                        namespace=binding.metadata.namespace,
                        kind="RoleBinding",
                        role_ref=binding.role_ref.to_dict() if binding.role_ref else {},
                        subjects=[subject.to_dict() for subject in (binding.subjects or [])] if hasattr(binding, 'subjects') and binding.subjects is not None else [],
                        created_time=binding.metadata.creation_timestamp.isoformat() if binding.metadata.creation_timestamp else "Unknown"
                    )
                    result.append(rbac_binding)
            else:
                # Get cluster role bindings
                cluster_bindings = rbac_v1.list_cluster_role_binding(timeout_seconds=5)
                for binding in cluster_bindings.items:
                    rbac_binding = RBACBinding(
                        name=binding.metadata.name,
                        namespace=None,
                        kind="ClusterRoleBinding",
                        role_ref=binding.role_ref.to_dict() if binding.role_ref else {},
                        subjects=[subject.to_dict() for subject in (binding.subjects or [])] if hasattr(binding, 'subjects') and binding.subjects is not None else [],
                        created_time=binding.metadata.creation_timestamp.isoformat() if binding.metadata.creation_timestamp else "Unknown"
                    )
                    result.append(rbac_binding)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get RBAC bindings: {e}")
            raise Exception(f"Failed to get RBAC bindings: {str(e)}")
    
    def health_check(self) -> Dict[str, Any]:
        """Health check for the service"""
        self._ensure_configured()  # Lazy auto-configure
        if not self.is_configured:
            return {
                "status": "unhealthy",
                "message": "No cluster configured",
                "clusters_configured": 0
            }
        
        try:
            cluster_info = self.get_cluster_info()
            return {
                "status": "healthy",
                "service": "WorkingKubernetes",
                "cluster_name": cluster_info.name,
                "cluster_version": cluster_info.version,
                "namespaces": cluster_info.namespace_count,
                "pods": cluster_info.pod_count,
                "nodes": cluster_info.node_count,
                "clusters_configured": 1
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": str(e),
                "clusters_configured": 1 if self.is_configured else 0
            }
    
    def _cleanup_temp_file(self):
        """Clean up temporary kubeconfig file"""
        if self.temp_kubeconfig_path and os.path.exists(self.temp_kubeconfig_path):
            try:
                os.unlink(self.temp_kubeconfig_path)
                self.temp_kubeconfig_path = None
            except Exception as e:
                logger.warning(f"Could not clean up temp kubeconfig: {e}")
    
    def cleanup(self):
        """Cleanup resources"""
        self._cleanup_temp_file()
        self.is_configured = False
        self.cluster_name = None

# Global working service instance - use lazy loading to avoid blocking
_working_kubernetes_service = None

def get_working_kubernetes_service() -> WorkingKubernetesService:
    """Get working kubernetes service instance with lazy loading"""
    global _working_kubernetes_service
    if _working_kubernetes_service is None:
        _working_kubernetes_service = WorkingKubernetesService()
    return _working_kubernetes_service

# Don't instantiate at module level - use function call only 