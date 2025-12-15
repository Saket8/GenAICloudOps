import asyncio
import oci
import json
import logging
import os
import random
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
from app.core.exceptions import ExternalServiceError, NotFoundError
from app.services.cache_service import cache_service

logger = logging.getLogger(__name__)

try:
    from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
    TENACITY_AVAILABLE = True
except ImportError:
    TENACITY_AVAILABLE = False
    # Create dummy decorators when tenacity is not available
    def retry(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    stop_after_attempt = wait_exponential = retry_if_exception_type = lambda *args, **kwargs: None

# Configuration and data classes
@dataclass
class OCIMetrics:
    """Data class for OCI resource metrics"""
    cpu_utilization: float
    memory_utilization: float
    network_bytes_in: int
    network_bytes_out: int
    timestamp: datetime

@dataclass 
class OCIResource:
    """Data class for OCI resource information"""
    id: str
    name: str
    state: str
    resource_type: str
    compartment_id: str
    availability_domain: Optional[str] = None
    shape: Optional[str] = None
    metrics: Optional[OCIMetrics] = None

class ResourceType(Enum):
    """Enumeration of supported OCI resource types"""
    COMPUTE_INSTANCE = "compute_instance"
    DATABASE = "database"
    OKE_CLUSTER = "oke_cluster"
    API_GATEWAY = "api_gateway"
    LOAD_BALANCER = "load_balancer"
    AUTONOMOUS_DATABASE = "autonomous_database"

class OCIAuthConfig:
    """OCI authentication configuration management"""
    
    def __init__(self):
        from app.core.config import settings
        
        self.config_file = os.getenv("OCI_CONFIG_FILE", settings.OCI_CONFIG_FILE)
        self.profile = os.getenv("OCI_PROFILE", settings.OCI_PROFILE)
        self.region = os.getenv("OCI_REGION", settings.OCI_REGION)
        
        # Environment variable based auth (for containerized environments)
        self.tenancy_id = os.getenv("OCI_TENANCY_ID", settings.OCI_TENANCY_ID)
        self.user_id = os.getenv("OCI_USER_ID", settings.OCI_USER_ID)
        self.fingerprint = os.getenv("OCI_FINGERPRINT", settings.OCI_FINGERPRINT)
        self.key_file = os.getenv("OCI_KEY_FILE", settings.OCI_KEY_FILE)
        
    def get_config(self) -> Dict[str, str]:
        """Get OCI configuration for SDK initialization"""
        if self.tenancy_id and self.user_id and self.fingerprint and self.key_file:
            # Use environment variables
            logger.info("Using OCI configuration from environment variables")
            return {
                "user": self.user_id,
                "key_file": self.key_file,
                "fingerprint": self.fingerprint,
                "tenancy": self.tenancy_id,
                "region": self.region
            }
        else:
            # Use config file
            try:
                # Expand Windows paths properly
                expanded_config_file = os.path.expanduser(self.config_file)
                if not os.path.exists(expanded_config_file):
                    # Try the literal path on Windows
                    if os.path.exists(self.config_file):
                        expanded_config_file = self.config_file
                    else:
                        raise FileNotFoundError(f"OCI config file not found at {self.config_file} or {expanded_config_file}")
                
                logger.info(f"Loading OCI config from: {expanded_config_file}")
                config = oci.config.from_file(expanded_config_file, self.profile)
                
                # Validate config has required fields
                required_fields = ["user", "tenancy", "region", "fingerprint"]
                missing_fields = [field for field in required_fields if not config.get(field)]
                if missing_fields:
                    raise ValueError(f"OCI config missing required fields: {missing_fields}")
                
                logger.info(f"✅ OCI config loaded successfully for region: {config.get('region')}")
                return config
                
            except Exception as e:
                logger.error(f"❌ Failed to load OCI config file: {e}")
                logger.error(f"Config file path: {self.config_file}")
                logger.error(f"Profile: {self.profile}")
                # Don't fall back to mock - raise the error so we know what's wrong
                raise RuntimeError(f"OCI configuration failed: {e}")

class OCIService:
    """Comprehensive OCI SDK integration service"""
    
    def __init__(self):
        from app.core.config import settings
        self.auth_config = OCIAuthConfig()
        # self.cache = OCICacheManager() # Logic replaced with global cache_service
        self.clients = {}
        self.oci_available = False
        self.config = None
        # If dummy mode is enabled, keep OCI unavailable and skip client init
        if getattr(settings, 'USE_DUMMY_OCI', False):
            logger.info("USE_DUMMY_OCI is True - skipping OCI client initialization and using mock data")
            self.oci_available = False
            self.clients = {}
            self.config = {"region": settings.OCI_REGION}
        else:
            self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize OCI configuration only - clients are created lazily on first use"""
        try:
            # Get OCI configuration
            self.config = self.auth_config.get_config()
            
            # Validate configuration first
            oci.config.validate_config(self.config)
            logger.info(f"✅ OCI config validation passed for tenancy: {self.config.get('tenancy', 'unknown')}")
            
            # Mark as available - clients will be created on-demand
            self.oci_available = True
            logger.info("🚀 OCI configuration loaded. Clients will be initialized lazily on first use.")
            
        except Exception as e:
            logger.error(f"❌ Failed to load OCI configuration: {e}")
            logger.warning("🔄 Falling back to mock data for development")
            self.oci_available = False
            self.clients = {}
            self.config = {"region": "us-ashburn-1"}
    
    def _get_client(self, client_name: str):
        """Get or create an OCI client lazily. Thread-safe via GIL."""
        if client_name in self.clients:
            return self.clients[client_name]
        
        if not self.oci_available or not self.config:
            raise ExternalServiceError(f"OCI not available, cannot create {client_name} client")
        
        logger.info(f"🔧 Lazy-initializing OCI client: {client_name}")
        
        # Client factory mapping
        client_factories = {
            'compute': lambda: oci.core.ComputeClient(self.config),
            'identity': lambda: oci.identity.IdentityClient(self.config),
            'monitoring': lambda: oci.monitoring.MonitoringClient(self.config),
            'logging': lambda: oci.logging.LoggingManagementClient(self.config),
            'log_search': lambda: oci.loggingsearch.LogSearchClient(self.config),
            'database': lambda: oci.database.DatabaseClient(self.config),
            'container_engine': lambda: oci.container_engine.ContainerEngineClient(self.config),
            'load_balancer': lambda: oci.load_balancer.LoadBalancerClient(self.config),
            'network_load_balancer': lambda: oci.network_load_balancer.NetworkLoadBalancerClient(self.config),
            'virtual_network': lambda: oci.core.VirtualNetworkClient(self.config),
            'block_storage': lambda: oci.core.BlockstorageClient(self.config),
            'file_storage': lambda: oci.file_storage.FileStorageClient(self.config),
            'object_storage': lambda: oci.object_storage.ObjectStorageClient(self.config),
            'api_gateway': lambda: oci.apigateway.GatewayClient(self.config),
            'usage_api': lambda: oci.usage_api.UsageapiClient(self.config),
            'vault': lambda: oci.vault.VaultsClient(self.config),
            'kms_vault': lambda: oci.key_management.KmsVaultClient(self.config),
            # Phase 3: Audit and Monitoring for lifecycle/activity tracking
            'audit': lambda: oci.audit.AuditClient(self.config),
            'monitoring': lambda: oci.monitoring.MonitoringClient(self.config),
        }
        
        factory = client_factories.get(client_name)
        if not factory:
            raise ExternalServiceError(f"Unknown OCI client: {client_name}")
        
        try:
            client = factory()
            self.clients[client_name] = client
            logger.info(f"✅ OCI client '{client_name}' initialized successfully")
            return client
        except Exception as e:
            logger.error(f"❌ Failed to initialize OCI client '{client_name}': {e}")
            raise ExternalServiceError(f"Failed to initialize {client_name}: {e}")

    async def test_connection(self) -> bool:
        """Test OCI connection asynchronously on-demand"""
        if not self.oci_available or not self.clients.get('identity'):
            return False
            
        try:
            # Test the connection with a simple call using asyncio
            identity_client = self._get_client('identity')
            loop = asyncio.get_event_loop()
            
            tenancy = await loop.run_in_executor(
                None,
                lambda: identity_client.get_tenancy(self.config['tenancy'])
            )
            
            logger.info(f"✅ OCI connection test successful. Tenancy: {tenancy.data.name}")
            return True
            
        except Exception as test_error:
            logger.warning(f"⚠️ OCI connection test failed: {test_error}")
            logger.warning("🔄 Will use mock data for development")
            return False

    async def _make_oci_call(self, client_method, *args, **kwargs):
        """Make OCI API call with retry logic"""
        retries = 5
        base_delay = 1.0
        
        for i in range(retries):
            try:
                # Create a wrapper function to handle kwargs properly
                def call_with_kwargs():
                    return client_method(*args, **kwargs)
                
                return await asyncio.get_event_loop().run_in_executor(
                    None, call_with_kwargs
                )
            except oci.exceptions.ServiceError as e:
                # Handle 429 Too Many Requests
                if e.status == 429:
                    if i < retries - 1:
                        delay = base_delay * (2 ** i) + random.uniform(0, 1.0)
                        logger.warning(f"⚠️ OCI Throttling (429) on {client_method.__name__ if hasattr(client_method, '__name__') else 'API call'}. Retrying in {delay:.2f}s...")
                        await asyncio.sleep(delay)
                        continue
                
                logger.error(f"OCI API error: {e}")
                raise ExternalServiceError(f"OCI API call failed: {e.message}")
            except Exception as e:
                logger.error(f"Unexpected error in OCI call: {e}")
                raise

    # ===== Phase 3: Stopped Duration via Monitoring API =====
    
    async def get_instance_last_activity(
        self, 
        compartment_id: str, 
        instance_id: str,
        days_back: int = 90
    ) -> Optional[datetime]:
        """
        Use Monitoring API to find the last time an instance had CPU activity.
        Returns the datetime of last activity, or None if no metrics found.
        
        This is more reliable than Audit API for detecting "stopped for X days".
        """
        if not self.oci_available:
            logger.warning("OCI not available, cannot get instance metrics")
            return None
        
        try:
            monitoring_client = self._get_client('monitoring')
            
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=days_back)
            
            # Build the MQL query for CPU utilization
            query = f'CpuUtilization[1d]{{resourceId = "{instance_id}"}}.mean()'
            
            from oci.monitoring.models import SummarizeMetricsDataDetails
            
            summarize_details = SummarizeMetricsDataDetails(
                namespace="oci_computeagent",
                query=query,
                start_time=start_time,
                end_time=end_time,
            )
            
            response = await self._make_oci_call(
                monitoring_client.summarize_metrics_data,
                compartment_id=compartment_id,
                summarize_metrics_data_details=summarize_details
            )
            
            # Find the most recent datapoint timestamp
            last_activity = None
            for metric_data in response.data:
                for datapoint in metric_data.aggregated_datapoints:
                    if datapoint.timestamp:
                        if last_activity is None or datapoint.timestamp > last_activity:
                            last_activity = datapoint.timestamp
            
            if last_activity:
                logger.info(f"✅ Found last activity for {instance_id[:30]}... at {last_activity}")
            else:
                logger.info(f"ℹ️ No metrics found for {instance_id[:30]}...")
            
            return last_activity
            
        except Exception as e:
            logger.error(f"❌ Failed to get instance metrics: {e}")
            return None
    
    async def get_instance_stopped_duration(
        self, 
        compartment_id: str, 
        instance_id: str
    ) -> Optional[int]:
        """
        Calculate days since instance was stopped using Monitoring API.
        Returns None if instance is running or has recent activity.
        """
        last_activity = await self.get_instance_last_activity(compartment_id, instance_id)
        
        if not last_activity:
            # No metrics = could be stopped for a long time or new instance
            return None
        
        # Calculate days since last activity
        now = datetime.utcnow()
        if last_activity.tzinfo:
            now = now.replace(tzinfo=last_activity.tzinfo)
        
        days_inactive = (now - last_activity).days
        
        # Only return if inactive for more than 1 day (to avoid false positives)
        if days_inactive > 1:
            return days_inactive
        
        return None
    
    async def get_instance_lifecycle_events(
        self, 
        compartment_id: str, 
        instance_id: str,
        days_back: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Get lifecycle events - now returns empty list and uses Monitoring API instead.
        This method is kept for API compatibility.
        """
        # Audit API has known issues - using Monitoring API via get_instance_stopped_duration instead
        return []


    async def get_compartments(self) -> List[Dict[str, Any]]:
        """Get all compartments in tenancy with caching"""
        cache_key = "oci:compartments"
        
        # Try global cache service first
        cached = await cache_service.get("oci", "compartments:v2")
        if cached:
            return cached

        try:
            if not self.oci_available:
                logger.warning("OCI identity unavailable - returning mock compartments")
                return [{"id": "ocid1.compartment.oc1..mock", "name": "Mock Compartment", "lifecycle_state": "ACTIVE"}]

            # Fetch root compartment (Tenancy)
            tenancy_id = self.config['tenancy']
            
            # Helper to recursively fetch sub-compartments
            all_compartments = []
            
            async def fetch_sub_compartments(parent_id):
                try:
                    response = await self._make_oci_call(
                        self._get_client('identity').list_compartments,
                        parent_id,
                        compartment_id_in_subtree=True,
                        access_level="ACCESSIBLE"
                    )
                    return response.data
                except Exception as e:
                    logger.error(f"Failed to fetch sub-compartments for {parent_id}: {e}")
                    return []

            # Get tenancy details first (it's also a compartment)
            try:
                tenancy = await self._make_oci_call(
                    self._get_client('identity').get_tenancy,
                    tenancy_id
                )
                all_compartments.append({
                    "id": tenancy.data.id,
                    "name": tenancy.data.name,
                    "description": tenancy.data.description,
                    "lifecycle_state": "ACTIVE", # Tenancy is always active if we can reach it
                    "time_created": None
                })
            except Exception as e:
                logger.warning(f"Could not fetch tenancy details: {e}")

            # Get all other compartments
            sub_compartments = await fetch_sub_compartments(tenancy_id)
            for c in sub_compartments:
                if c.lifecycle_state == "ACTIVE":
                    all_compartments.append({
                        "id": c.id,
                        "name": c.name,
                        "description": c.description,
                        "lifecycle_state": c.lifecycle_state,
                        "compartment_id": c.compartment_id,
                        "time_created": c.time_created.isoformat() if c.time_created else None
                    })
            
            logger.info(f"Found {len(all_compartments)} active compartments")
            
            # Cache the result
            await cache_service.set("oci", "compartments:v2", all_compartments, ttl=86400)
            
            return all_compartments
            
        except Exception as e:
            logger.error(f"Failed to get compartments: {e}")
            return []

    async def get_compute_instances(self, compartment_id: str) -> List[Dict[str, Any]]:
        """Get compute instances in a compartment"""
        cache_key = f"compute_instances:{compartment_id}"
        
        # Use global cache service
        cached = await cache_service.get("oci", cache_key)
        if cached:
            return cached
        
        try:
            if not self.oci_available:
                logger.error("OCI compute unavailable")
                return []

            
            response = await self._make_oci_call(
                self._get_client('compute').list_instances,
                compartment_id
            )
            
            instances = []
            for instance in response.data:
                instances.append({
                    "id": instance.id,
                    "display_name": instance.display_name,
                    "lifecycle_state": instance.lifecycle_state,
                    "shape": instance.shape,
                    "availability_domain": instance.availability_domain,
                    "time_created": instance.time_created.isoformat() if instance.time_created else None,
                    "region": instance.region if hasattr(instance, 'region') else self.config.get('region')
                })
            
            await cache_service.set("oci", cache_key, instances, ttl=600)  # 5 minutes cache
            return instances
            
        except Exception as e:
            logger.error(f"Failed to get compute instances: {e}")
            # Return empty list instead of raising exception to prevent frontend crashes
            return []

    async def get_databases(self, compartment_id: str) -> List[Dict[str, Any]]:
        """Get database services in a compartment (both DB Systems and Autonomous Databases)"""
        cache_key = f"databases:{compartment_id}"
        cached = await cache_service.get("oci", cache_key)
        if cached:
            return cached
        
        try:
            if not self.oci_available:
                logger.error("OCI database unavailable")
                return []

            
            databases = []
            
            # Get Database Systems (VM and Bare Metal DB systems)
            try:
                db_systems_response = await self._make_oci_call(
                    self._get_client('database').list_db_systems,
                    compartment_id=compartment_id
                )
                
                for db_system in db_systems_response.data:
                    databases.append({
                        "id": db_system.id,
                        "display_name": db_system.display_name,
                        "lifecycle_state": db_system.lifecycle_state,
                        "database_edition": getattr(db_system, 'database_edition', 'Unknown'),
                        "shape": getattr(db_system, 'shape', 'Unknown'),
                        "cpu_core_count": getattr(db_system, 'cpu_core_count', 0),
                        "data_storage_size_in_gbs": getattr(db_system, 'data_storage_size_in_gbs', 0),
                        "node_count": getattr(db_system, 'node_count', 1),
                        "availability_domain": getattr(db_system, 'availability_domain', 'Unknown'),
                        "resource_type": "DB_SYSTEM",
                        "time_created": db_system.time_created.isoformat() if db_system.time_created else None
                    })
                    
                    # Get DB Homes within each DB system, then databases within each DB Home
                    try:
                        # First get DB Homes for this DB System
                        db_homes_response = await self._make_oci_call(
                            self._get_client('database').list_db_homes,
                            compartment_id=compartment_id,
                            db_system_id=db_system.id
                        )
                        
                        for db_home in db_homes_response.data:
                            # Then get databases within each DB Home
                            try:
                                databases_response = await self._make_oci_call(
                                    self._get_client('database').list_databases,
                                    compartment_id=compartment_id,
                                    db_home_id=db_home.id
                                )
                                
                                for db in databases_response.data:
                                    databases.append({
                                        "id": db.id,
                                        "display_name": f"  └─ {db.db_name} (Database)",
                                        "db_name": db.db_name,
                                        "lifecycle_state": db.lifecycle_state,
                                        "db_workload": getattr(db, 'db_workload', 'Unknown'),
                                        "character_set": getattr(db, 'character_set', 'Unknown'),
                                        "pdb_name": getattr(db, 'pdb_name', None),
                                        "is_cdb": getattr(db, 'is_cdb', False),
                                        "resource_type": "DATABASE",
                                        "db_system_id": db_system.id,
                                        "db_home_id": db_home.id,
                                        "time_created": db.time_created.isoformat() if db.time_created else None
                                    })
                            except Exception as db_error:
                                logger.warning(f"Failed to get databases for DB home {db_home.id}: {db_error}")
                                
                    except Exception as db_home_error:
                        logger.warning(f"Failed to get DB homes for DB system {db_system.id}: {db_home_error}")
                        
            except Exception as e:
                logger.warning(f"Failed to get DB systems: {e}")
            
            # Also get Autonomous Databases
            try:
                autonomous_response = await self._make_oci_call(
                    self._get_client('database').list_autonomous_databases,
                    compartment_id=compartment_id
                )
                
                for db in autonomous_response.data:
                    databases.append({
                        "id": db.id,
                        "db_name": getattr(db, 'db_name', 'Unknown'),
                        "display_name": db.display_name,
                        "lifecycle_state": db.lifecycle_state,
                        "db_workload": getattr(db, 'db_workload', 'Unknown'),
                        "cpu_core_count": getattr(db, 'cpu_core_count', 0),
                        "data_storage_size_in_tbs": getattr(db, 'data_storage_size_in_tbs', 0),
                        "resource_type": "AUTONOMOUS_DATABASE",
                        "time_created": db.time_created.isoformat() if db.time_created else None
                    })
            except Exception as e:
                logger.warning(f"Failed to get Autonomous databases: {e}")
            
            logger.info(f"Found {len(databases)} total database resources in compartment")
            await cache_service.set("oci", cache_key, databases, ttl=300)
            return databases
            
        except Exception as e:
            logger.error(f"Failed to get databases: {e}")
            return []

    async def get_oke_clusters(self, compartment_id: str) -> List[Dict[str, Any]]:
        """Get OKE clusters in a compartment"""
        cache_key = f"oke:{compartment_id}"
        cached = await cache_service.get("oci", cache_key)
        if cached:
            return cached
        
        try:
            if not self.oci_available:
                logger.error("OCI container engine unavailable")
                return []

            
            response = await self._make_oci_call(
                self._get_client('container_engine').list_clusters,
                compartment_id
            )
            
            clusters = []
            for cluster in response.data:
                clusters.append({
                    "id": cluster.id,
                    "name": cluster.name,
                    "lifecycle_state": cluster.lifecycle_state,
                    "kubernetes_version": cluster.kubernetes_version,
                    "vcn_id": cluster.vcn_id
                })
            
            await cache_service.set("oci", cache_key, clusters, ttl=300)
            return clusters
            
        except Exception as e:
            logger.error(f"Failed to get OKE clusters: {e}")
            return []

    async def get_api_gateways(self, compartment_id: str) -> List[Dict[str, Any]]:
        """Get API Gateways in a compartment"""
        cache_key = f"api_gateways:{compartment_id}"
        cached = await cache_service.get("oci", cache_key)
        if cached:
            return cached
        
        try:
            if not self.oci_available:
                logger.debug("OCI API gateway unavailable")
                return []

            response = await self._make_oci_call(
                self._get_client('api_gateway').list_gateways,
                compartment_id
            )
            
            gateways = []
            gateway_list = response.data.items if hasattr(response.data, 'items') else response.data
            for gateway in gateway_list:
                gateways.append({
                    "id": gateway.id,
                    "display_name": gateway.display_name,
                    "lifecycle_state": gateway.lifecycle_state,
                    "hostname": getattr(gateway, 'hostname', 'N/A')
                })
            
            await cache_service.set("oci", cache_key, gateways, ttl=300)
            return gateways
            
        except Exception as e:
            logger.error(f"Failed to get API gateways: {e}")
            return []

    async def get_load_balancers(self, compartment_id: str) -> List[Dict[str, Any]]:
        """Get load balancers in a compartment"""
        cache_key = f"load_balancers:{compartment_id}"
        cached = await cache_service.get("oci", cache_key)
        if cached:
            return cached
        
        try:
            if not self.oci_available:
                logger.debug("OCI load balancer unavailable")
                return []
            
            response = await self._make_oci_call(
                self._get_client('load_balancer').list_load_balancers,
                compartment_id
            )
            
            load_balancers = []
            for lb in response.data:
                load_balancers.append({
                    "id": lb.id,
                    "display_name": lb.display_name,
                    "lifecycle_state": lb.lifecycle_state,
                    "shape_name": lb.shape_name,
                    "is_private": lb.is_private
                })
            
            await cache_service.set("oci", cache_key, load_balancers, ttl=300)
            return load_balancers
            
        except Exception as e:
            logger.error(f"Failed to get load balancers: {e}")
            return []

    async def get_network_resources(self, compartment_id: str) -> List[Dict[str, Any]]:
        """Get network resources (VCNs, subnets, etc.) in a compartment"""
        cache_key = f"network:{compartment_id}"
        cached = await cache_service.get("oci", cache_key)
        if cached:
            return cached
        
        try:
            if not self.oci_available:
                logger.debug("OCI virtual network unavailable")
                return []
            
            # Get VCNs
            vcn_response = await self._make_oci_call(
                self._get_client('virtual_network').list_vcns,
                compartment_id
            )
            
            networks = []
            for vcn in vcn_response.data:
                networks.append({
                    "id": vcn.id,
                    "display_name": vcn.display_name,
                    "lifecycle_state": vcn.lifecycle_state,
                    "cidr_block": vcn.cidr_block,
                    "resource_type": "VCN",
                    "time_created": vcn.time_created.isoformat() if vcn.time_created else None
                })
                
                # Get subnets for each VCN
                try:
                    subnet_response = await self._make_oci_call(
                        self._get_client('virtual_network').list_subnets,
                        compartment_id,
                        vcn_id=vcn.id
                    )
                    
                    for subnet in subnet_response.data:
                        networks.append({
                            "id": subnet.id,
                            "display_name": f"  └─ {subnet.display_name}",
                            "lifecycle_state": subnet.lifecycle_state,
                            "cidr_block": subnet.cidr_block,
                            "resource_type": "Subnet",
                            "vcn_id": vcn.id,
                            "time_created": subnet.time_created.isoformat() if subnet.time_created else None
                        })
                except Exception as e:
                    logger.warning(f"Failed to get subnets for VCN {vcn.id}: {e}")
            
            await cache_service.set("oci", cache_key, networks, ttl=300)
            return networks
            
        except Exception as e:
            logger.error(f"Failed to get network resources: {e}")
            return []

    async def get_block_volumes(self, compartment_id: str) -> List[Dict[str, Any]]:
        """Get block volumes in a compartment"""
        cache_key = f"block_volumes:{compartment_id}"
        cached = await cache_service.get("oci", cache_key)
        if cached:
            return cached
        
        try:
            if not self.oci_available:
                logger.debug("OCI block storage unavailable")
                return []
            
            response = await self._make_oci_call(
                self._get_client('block_storage').list_volumes,
                compartment_id=compartment_id
            )
            
            volumes = []
            for volume in response.data:
                volumes.append({
                    "id": volume.id,
                    "display_name": volume.display_name,
                    "lifecycle_state": volume.lifecycle_state,
                    "size_in_gbs": volume.size_in_gbs,
                    "availability_domain": volume.availability_domain,
                    "volume_group_id": getattr(volume, 'volume_group_id', None),
                    "is_hydrated": getattr(volume, 'is_hydrated', True),
                    "time_created": volume.time_created.isoformat() if volume.time_created else None
                })
            
            await cache_service.set("oci", cache_key, volumes, ttl=300)
            return volumes
            
        except Exception as e:
            logger.error(f"Failed to get block volumes: {e}")
            return []

    async def get_file_systems(self, compartment_id: str) -> List[Dict[str, Any]]:
        """Get file systems in a compartment"""
        cache_key = f"file_systems:{compartment_id}"
        cached = await cache_service.get("oci", cache_key)
        if cached:
            return cached
        
        try:
            if not self.oci_available:
                logger.debug("OCI file storage unavailable")
                return []
            
            # Get availability domains first
            identity_client = self._get_client('identity')
            ads_response = await self._make_oci_call(
                identity_client.list_availability_domains,
                compartment_id=self.config['tenancy']
            )
            
            file_systems = []
            # Query file systems in each availability domain
            for ad in ads_response.data:
                try:
                    response = await self._make_oci_call(
                        self._get_client('file_storage').list_file_systems,
                        compartment_id=compartment_id,
                        availability_domain=ad.name
                    )
                    
                    for fs in response.data:
                        file_systems.append({
                            "id": fs.id,
                            "display_name": fs.display_name,
                            "lifecycle_state": fs.lifecycle_state,
                            "availability_domain": fs.availability_domain,
                            "metered_bytes": getattr(fs, 'metered_bytes', 0),
                            "source_details": getattr(fs, 'source_details', None),
                            "time_created": fs.time_created.isoformat() if fs.time_created else None
                        })
                except Exception as ad_error:
                    logger.warning(f"Failed to get file systems in AD {ad.name}: {ad_error}")
                    continue
            
            await cache_service.set("oci", cache_key, file_systems, ttl=300)
            return file_systems
            
        except Exception as e:
            logger.error(f"Failed to get file systems: {e}")
            return []

    async def get_object_storage_buckets(self, compartment_id: str) -> List[Dict[str, Any]]:
        """Get Object Storage buckets in a compartment"""
        cache_key = f"buckets:{compartment_id}"
        cached = await cache_service.get("oci", cache_key)
        if cached:
            return cached
        
        try:
            if not self.oci_available:
                logger.debug("OCI object storage unavailable")
                return []
            
            # Get the namespace first
            object_storage_client = self._get_client('object_storage')
            namespace_response = await self._make_oci_call(
                object_storage_client.get_namespace,
                compartment_id=compartment_id
            )
            namespace = namespace_response.data
            
            # List buckets in the compartment
            response = await self._make_oci_call(
                object_storage_client.list_buckets,
                namespace_name=namespace,
                compartment_id=compartment_id
            )
            
            buckets = []
            for bucket in response.data:
                # Get bucket details for more info
                try:
                    bucket_details = await self._make_oci_call(
                        object_storage_client.get_bucket,
                        namespace_name=namespace,
                        bucket_name=bucket.name
                    )
                    bd = bucket_details.data
                    buckets.append({
                        "id": bd.id if hasattr(bd, 'id') else f"bucket:{namespace}:{bucket.name}",
                        "display_name": bucket.name,
                        "namespace": namespace,
                        "storage_tier": getattr(bd, 'storage_tier', 'Standard'),
                        "approximate_size": getattr(bd, 'approximate_size', 0),
                        "approximate_count": getattr(bd, 'approximate_count', 0),
                        "public_access_type": getattr(bd, 'public_access_type', 'NoPublicAccess'),
                        "versioning": getattr(bd, 'versioning', 'Disabled'),
                        "lifecycle_state": "ACTIVE",
                        "resource_type": "OBJECT_STORAGE_BUCKET",
                        "time_created": bucket.time_created.isoformat() if bucket.time_created else None
                    })
                except Exception as bucket_error:
                    logger.warning(f"Failed to get bucket details for {bucket.name}: {bucket_error}")
                    buckets.append({
                        "id": f"bucket:{namespace}:{bucket.name}",
                        "display_name": bucket.name,
                        "namespace": namespace,
                        "lifecycle_state": "ACTIVE",
                        "resource_type": "OBJECT_STORAGE_BUCKET",
                        "time_created": bucket.time_created.isoformat() if bucket.time_created else None
                    })
            
            logger.info(f"Found {len(buckets)} Object Storage buckets in compartment")
            await cache_service.set("oci", cache_key, buckets, ttl=300)
            return buckets
            
        except Exception as e:
            logger.error(f"Failed to get Object Storage buckets: {e}")
            return []

    async def get_vaults(self, compartment_id: str) -> List[Dict[str, Any]]:
        """Get Vaults and their secrets in a compartment"""
        cache_key = f"vaults:{compartment_id}"
        cached = await cache_service.get("oci", cache_key)
        if cached:
            return cached
        
        try:
            if not self.oci_available:
                logger.debug("OCI vault unavailable")
                return []
            
            kms_vault_client = self._get_client('kms_vault')
            
            # List vaults in the compartment
            response = await self._make_oci_call(
                kms_vault_client.list_vaults,
                compartment_id=compartment_id
            )
            
            vaults = []
            for vault in response.data:
                vault_info = {
                    "id": vault.id,
                    "display_name": vault.display_name,
                    "lifecycle_state": vault.lifecycle_state,
                    "vault_type": getattr(vault, 'vault_type', 'DEFAULT'),
                    "crypto_endpoint": getattr(vault, 'crypto_endpoint', None),
                    "management_endpoint": getattr(vault, 'management_endpoint', None),
                    "resource_type": "VAULT",
                    "time_created": vault.time_created.isoformat() if vault.time_created else None
                }
                vaults.append(vault_info)
                
                # Try to list secrets if vault is active
                if vault.lifecycle_state == "ACTIVE":
                    try:
                        secrets_client = self._get_client('vault')
                        secrets_response = await self._make_oci_call(
                            secrets_client.list_secrets,
                            compartment_id=compartment_id,
                            vault_id=vault.id
                        )
                        
                        for secret in secrets_response.data:
                            vaults.append({
                                "id": secret.id,
                                "display_name": f"  └─ {secret.secret_name} (Secret)",
                                "secret_name": secret.secret_name,
                                "lifecycle_state": secret.lifecycle_state,
                                "vault_id": vault.id,
                                "resource_type": "SECRET",
                                "time_created": secret.time_created.isoformat() if secret.time_created else None
                            })
                    except Exception as secret_error:
                        logger.warning(f"Failed to list secrets for vault {vault.display_name}: {secret_error}")
            
            logger.info(f"Found {len(vaults)} vault resources (vaults + secrets) in compartment")
            await cache_service.set("oci", cache_key, vaults, ttl=300)
            return vaults
            
        except Exception as e:
            logger.error(f"Failed to get vaults: {e}")
            return []

    async def get_resource_metrics(self, resource_id: str, resource_type: str) -> Dict[str, Any]:
        """Get real-time metrics for a resource"""
        cache_key = f"metrics:{resource_id}:{resource_type}"
        cached = await cache_service.get("oci", cache_key)
        if cached:
            return cached
        
        try:
            if not self.oci_available or 'monitoring' not in self.clients:
                logger.debug("OCI monitoring unavailable")
                return {
                    "resource_id": resource_id,
                    "metrics": {
                        "cpu_utilization": 0,
                        "memory_utilization": 0,
                        "network_bytes_in": 0,
                        "network_bytes_out": 0
                    },
                    "timestamp": datetime.utcnow().isoformat(),
                    "health_status": "UNKNOWN"
                }
            
            # This is a placeholder for real metrics implementation
            end_time = datetime.utcnow()
            
            metrics_data = {
                "resource_id": resource_id,
                "metrics": {
                    "cpu_utilization": 0.0,
                    "memory_utilization": 0.0, 
                    "network_bytes_in": 0,
                    "network_bytes_out": 0
                },
                "timestamp": end_time.isoformat(),
                "health_status": "UNKNOWN"
            }
            
            await cache_service.set("oci", cache_key, metrics_data, ttl=60)
            return metrics_data
            
        except Exception as e:
            logger.error(f"Failed to get metrics for {resource_id}: {e}")
            raise ExternalServiceError("Unable to retrieve resource metrics")

    async def get_all_resources(self, compartment_id: str, resource_filter: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get all resources in a compartment with optional filtering"""
        try:
            # If compartment_id is a tenancy root, query all compartments
            is_tenancy_root = compartment_id == self.config.get('tenancy') if self.config else False
            
            if is_tenancy_root:
                logger.info("🔍 Querying all compartments for resources...")
                return await self._get_all_resources_from_all_compartments(resource_filter)
            else:
                logger.info(f"🔍 Querying single compartment for resources: {compartment_id}")
                return await self._get_all_resources_from_single_compartment(compartment_id, resource_filter)
            
        except Exception as e:
            logger.error(f"Failed to get all resources: {e}")
            raise ExternalServiceError("Unable to retrieve compartment resources")

    async def _get_all_resources_from_all_compartments(self, resource_filter: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get resources from all compartments in the tenancy - TENANCY AGNOSTIC"""
        try:
            # Get all compartments
            compartments = await self.get_compartments()
            logger.info(f"Found {len(compartments)} compartments to query")
            
            # Create tasks for all available compartments
            compartment_tasks = []
            compartment_map = {} # Map ID to Name for quick lookup
            
            # Limit concurrency to avoid timeouts
            semaphore = asyncio.Semaphore(5)
            
            async def protected_task(comp_id, resource_filter):
                async with semaphore:
                    return await self._get_all_resources_from_single_compartment(comp_id, resource_filter)

            for comp in compartments:
                comp_id = comp['id']
                comp_name = comp['name']
                compartment_map[comp_id] = comp_name
                
                # Create protected task
                task = protected_task(comp_id, resource_filter)
                compartment_tasks.append(task)
            
            # Execute all compartment queries in parallel (throttled)
            logger.info(f"🚀 Launching parallel queries for {len(compartment_tasks)} compartments (throttled)...")
            results_list = await asyncio.gather(*compartment_tasks, return_exceptions=True)
            
            # Initialize aggregated results
            # Get keys from method_map or default to known types
            resource_types = [
                'compute_instances', 'databases', 'oke_clusters', 'api_gateways', 
                'load_balancers', 'network_resources', 'block_volumes', 'file_systems',
                'object_storage_buckets', 'vaults'
            ]
            aggregated_results = {rt: [] for rt in resource_types}
            
            # Process results
            success_count = 0
            fail_count = 0
            
            for i, result in enumerate(results_list):
                # Retrieve compartment info (order is preserved in gather)
                comp = compartments[i]
                comp_name = comp['name']
                
                if isinstance(result, Exception):
                    logger.debug(f"Failed to query compartment {comp_name}: {result}")
                    fail_count += 1
                    continue
                
                success_count += 1
                
                # Aggregate resources from this compartment
                comp_resources = result.get('resources', {})
                for resource_type, items in comp_resources.items():
                    if resource_type in aggregated_results and items:
                        # Add source compartment info
                        for item in items:
                            item['source_compartment'] = comp_name
                        
                        aggregated_results[resource_type].extend(items)
            
            logger.info(f"✅ Parallel query complete: {success_count} succeeded, {fail_count} failed")
            
            # Summary logging
            total_resources = sum(len(resources) for resources in aggregated_results.values())
            logger.info(f"Total resources found across all compartments: {total_resources}")
            
            return {
                "compartment_id": "all_compartments",
                "resources": aggregated_results,
                "total_resources": total_resources,
                "last_updated": datetime.utcnow().isoformat(),
                "compartments_queried": len(compartments)
            }
            
        except Exception as e:
            logger.error(f"Failed to get resources from all compartments: {e}")
            raise

    async def _get_all_resources_from_single_compartment(self, compartment_id: str, resource_filter: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get all resources from a single compartment"""
        # Get all resource types in parallel
        tasks = []
        
        if not resource_filter or 'compute_instances' in resource_filter:
            tasks.append(('compute_instances', self.get_compute_instances(compartment_id)))
        
        if not resource_filter or 'databases' in resource_filter:
            tasks.append(('databases', self.get_databases(compartment_id)))
        
        if not resource_filter or 'oke_clusters' in resource_filter:
            tasks.append(('oke_clusters', self.get_oke_clusters(compartment_id)))
        
        if not resource_filter or 'api_gateways' in resource_filter:
            tasks.append(('api_gateways', self.get_api_gateways(compartment_id)))
        
        if not resource_filter or 'load_balancers' in resource_filter:
            tasks.append(('load_balancers', self.get_load_balancers(compartment_id)))
        
        if not resource_filter or 'network_resources' in resource_filter:
            tasks.append(('network_resources', self.get_network_resources(compartment_id)))
        
        if not resource_filter or 'block_volumes' in resource_filter:
            tasks.append(('block_volumes', self.get_block_volumes(compartment_id)))
        
        if not resource_filter or 'file_systems' in resource_filter:
            tasks.append(('file_systems', self.get_file_systems(compartment_id)))
        
        if not resource_filter or 'object_storage_buckets' in resource_filter:
            tasks.append(('object_storage_buckets', self.get_object_storage_buckets(compartment_id)))
        
        if not resource_filter or 'vaults' in resource_filter:
            tasks.append(('vaults', self.get_vaults(compartment_id)))
        
        # Execute all tasks in parallel using asyncio.gather
        results = {}
        
        if not tasks:
            return {
                "compartment_id": compartment_id,
                "resources": {},
                "total_resources": 0,
                "last_updated": datetime.utcnow().isoformat()
            }

        # Separate names and coroutines
        task_names = [t[0] for t in tasks]
        coroutines = [t[1] for t in tasks]
        
        # Run in parallel
        # return_exceptions=True allows all tasks to complete even if one fails
        task_results = await asyncio.gather(*coroutines, return_exceptions=True)
        
        # Process results
        for name, result in zip(task_names, task_results):
            if isinstance(result, Exception):
                logger.error(f"❌ Failed to get {name}: {result}")
                results[name] = []
            else:
                results[name] = result
                logger.info(f"✅ {name}: {len(result)} resources found")
        
        return {
            "compartment_id": compartment_id,
            "resources": results,
            "total_resources": sum(len(resources) for resources in results.values()),
            "last_updated": datetime.utcnow().isoformat()
        }

    async def get_instance_start_stop_events(
        self, 
        compartment_id: str, 
        instance_id: str = None,
        days_back: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get instance start/stop events from OCI Audit API.
        
        Uses the Audit ListEvents API to find actual StartInstance, StopInstance, 
        and InstanceAction events.
        
        Args:
            compartment_id: OCI compartment OCID to search
            instance_id: Optional specific instance OCID to filter for
            days_back: Number of days to search back (default 30)
            
        Returns:
            List of start/stop events with timestamps and resource details
        """
        cache_key = f"audit_events:{compartment_id}:{instance_id or 'all'}:{days_back}"
        cached = await cache_service.get("oci", cache_key)
        if cached:
            return cached
        
        try:
            if not self.oci_available:
                logger.debug("OCI audit service unavailable")
                return []
            
            from datetime import timezone
            
            # Define time window
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(days=days_back)
            
            audit_client = self._get_client('audit')
            
            # Call Audit API with pagination
            all_events = []
            page = None
            
            while True:
                if page:
                    response = await self._make_oci_call(
                        audit_client.list_events,
                        compartment_id=compartment_id,
                        start_time=start_time,
                        end_time=end_time,
                        page=page
                    )
                else:
                    response = await self._make_oci_call(
                        audit_client.list_events,
                        compartment_id=compartment_id,
                        start_time=start_time,
                        end_time=end_time
                    )
                
                # Process events
                for event in response.data:
                    event_data = event.data if hasattr(event, 'data') else None
                    if not event_data:
                        continue
                    
                    event_name = getattr(event_data, 'event_name', None) or ''
                    resource_id = getattr(event_data, 'resource_id', None) or ''
                    
                    # Filter for instance start/stop events
                    is_start_stop = event_name in (
                        'StartInstance', 'StopInstance', 'InstanceAction',
                        'LaunchInstance', 'TerminateInstance'
                    )
                    
                    # If specific instance requested, filter for it
                    if instance_id and resource_id != instance_id:
                        continue
                    
                    if is_start_stop:
                        # Determine action type
                        action_type = 'unknown'
                        if event_name == 'StartInstance' or event_name == 'LaunchInstance':
                            action_type = 'start'
                        elif event_name == 'StopInstance':
                            action_type = 'stop'
                        elif event_name == 'TerminateInstance':
                            action_type = 'terminate'
                        elif event_name == 'InstanceAction':
                            # Check request parameters for action type
                            request = getattr(event_data, 'request', None)
                            if request:
                                params = getattr(request, 'parameters', {}) or {}
                                action = params.get('action', '').upper()
                                if action in ('START', 'RESET'):
                                    action_type = 'start'
                                elif action in ('STOP', 'SOFTSTOP'):
                                    action_type = 'stop'
                        
                        all_events.append({
                            'event_time': event.event_time.isoformat() if hasattr(event, 'event_time') else None,
                            'event_name': event_name,
                            'action_type': action_type,
                            'resource_id': resource_id,
                            'compartment_id': compartment_id
                        })
                
                # Handle pagination - limit to 2 pages max for speed
                page_count = getattr(self, '_audit_page_count', 0) + 1
                self._audit_page_count = page_count
                
                if page_count >= 2:
                    logger.debug("Audit API: reached 2 page limit, stopping pagination")
                    break
                    
                if hasattr(response, 'has_next_page') and response.has_next_page:
                    page = response.next_page
                else:
                    break
                
                # Safety limit events
                if len(all_events) > 100:
                    logger.warning("Audit events limit reached (100), truncating results")
                    break
            
            # Reset page counter
            self._audit_page_count = 0
            
            # Sort by event time (most recent first)
            all_events.sort(key=lambda x: x.get('event_time', ''), reverse=True)
            
            logger.info(f"Retrieved {len(all_events)} start/stop events from Audit API")
            
            # Cache for 5 minutes
            await cache_service.set("oci", cache_key, all_events, ttl=300)
            return all_events
            
        except Exception as e:
            logger.error(f"Failed to get audit events: {e}")
            return []
    
    async def calculate_instance_stopped_duration(
        self,
        compartment_id: str,
        instance_id: str,
        current_state: str
    ) -> int:
        """
        Calculate how many days an instance has been stopped based on Audit events.
        
        Args:
            compartment_id: OCI compartment OCID
            instance_id: Instance OCID to check
            current_state: Current lifecycle state of the instance
            
        Returns:
            Number of days instance has been stopped, or 0 if unknown/running
        """
        # Only calculate for stopped instances
        if current_state.upper() not in ('STOPPED', 'INACTIVE'):
            return 0
        
        try:
            # Get start/stop events for this instance (last 14 days for speed)
            events = await self.get_instance_start_stop_events(
                compartment_id=compartment_id,
                instance_id=instance_id,
                days_back=14
            )
            
            if not events:
                # No events found - cannot determine duration
                logger.debug(f"No audit events found for instance {instance_id}")
                return 0
            
            # Find the most recent stop event
            last_stop_event = None
            for event in events:
                if event.get('action_type') == 'stop':
                    last_stop_event = event
                    break  # Events are sorted most recent first
            
            if not last_stop_event:
                # Instance is stopped but we have no stop event
                # It may have been stopped before our time window
                return 0
            
            # Calculate days since last stop
            from datetime import timezone
            stop_time_str = last_stop_event.get('event_time')
            if stop_time_str:
                stop_time = datetime.fromisoformat(stop_time_str.replace('Z', '+00:00'))
                days_stopped = (datetime.now(timezone.utc) - stop_time).days
                return max(0, days_stopped)
            
            return 0
            
        except Exception as e:
            logger.error(f"Failed to calculate stopped duration: {e}")
            return 0

# Legacy CloudOperationsService for backward compatibility
# Global singleton instance (lazy initialized)
_oci_service_instance = None

def get_oci_service() -> OCIService:
    """Get the OCIService singleton, initializing it if necessary"""
    global _oci_service_instance
    if _oci_service_instance is None:
        logger.info("Initializing OCIService singleton...")
        _oci_service_instance = OCIService()
        # Ensure we test connection asynchronously later if needed, 
        # but pure init should be fast now (just client construction)
    return _oci_service_instance

# Legacy CloudOperationsService with lazy loading
class CloudOperationsService:
    """Legacy service wrapper for backward compatibility"""
    
    def __init__(self):
        # Don't init OCIService here, use the singleton getter when needed
        pass
    
    @property
    def oci_service(self):
        return get_oci_service()
    
    async def get_cloud_resources(self, provider: str = "oci", compartment_id: Optional[str] = None) -> Dict[str, Any]:
        """Get cloud resources (wrapper for legacy compatibility)"""
        if provider != "oci":
            raise ExternalServiceError(f"Provider {provider} not supported")
        
        try:
            if not compartment_id:
                # Get first available compartment
                compartments = await self.oci_service.get_compartments()
                if not compartments:
                    raise ExternalServiceError("No accessible compartments found")
                compartment_id = compartments[0]['id']
            
            return await self.oci_service.get_all_resources(compartment_id)
            
        except Exception as e:
            logger.error(f"Failed to get cloud resources: {e}")
            raise ExternalServiceError("Cloud resources unavailable")

# Service instances - LAZY LOADED
# We remove the global instantiation. 
# Consumers must use get_oci_service() or imports will fail if they rely on 'oci_service'
# But we will provide a module-level property or update consumers.
# To be safe, we will leave 'oci_service' as None and update consumers to call get_oci_service()
oci_service = None 
cloud_ops_service = CloudOperationsService()

# For backward compatibility
k8s_service = None  # Will be implemented separately if needed 